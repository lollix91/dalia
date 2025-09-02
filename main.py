import os 
import re
import uuid
import time
import json
import shlex
import logging
import asyncio
import argparse
import threading
import subprocess
from nicegui import ui
logging.basicConfig(level=logging.INFO)

def has_port(text: str, port: int) -> bool:
    pattern = rf"(?<!\d):?{port}\b"
    return re.search(pattern, text) is not None

def port_busy(port):
    result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
    logging.info(result.stdout)
    return has_port(result.stdout, port)

def load_src(root):
    result      = {
        "agents": dict(),
        "comm": ""
    }
    mappingpath = os.path.join(root, 'src', 'mapping.json')
    try:
        with open(mappingpath, 'r') as f:
            mapping = json.loads(f.read())
    except Exception as e:
        logging.exception(f"{mappingpath} does not exist")
        return {} 
    try:
        for name, type in mapping.items():
            path = os.path.join(root, 'src', 'types', f'{type}.txt') 
            assert os.path.isfile(path)
            with open(path, 'r') as f:
                code = f.read().strip()
            result["agents"][name] = {
                "type": type,
                "code": code
            }
    except Exception as e:
        logging.exception(f"problem with mappings in {mappingpath}")
        return {} 
    commpath = os.path.join(root, 'src', 'conf', f'communication.con')
    try:
        assert os.path.isfile(commpath)
        with open(commpath, 'r') as f:
            code = f.read().strip()
            result["comm"] = code
    except Exception as e:
        logging.exception(f"problem with file {commpath}")
        return {} 
    return result

def rmdir(path):
    if os.path.exists(path) and os.path.isdir(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(path)

def build(*, root, sicstuspath, dalipath):
    src = load_src(root)
    if not src:
        return
    p = subprocess.Popen("pkill -9 sicstus 2>/dev/null || true", shell=True)
    p.wait()
    dalipath = os.path.join(dalipath, 'src')
    sicstus  = os.path.join(sicstuspath, 'bin', 'sicstus')
    wrk = os.path.join(root, 'wrk')
    rmdir(wrk)
    agentsdir = os.path.join(wrk, 'agents')
    setupsdir = os.path.join(wrk, 'setups')
    confdir  = os.path.join(wrk, 'conf')
    logdir = os.path.join(root, 'log')
    rmdir(logdir)
    os.makedirs(logdir, exist_ok=True)
    os.makedirs(setupsdir, exist_ok=True)
    os.makedirs(agentsdir, exist_ok=True)
    os.makedirs(confdir, exist_ok=True)
    with open(os.path.join(confdir, f'communication.con'), 'w') as f:
        f.write(src["comm"])
    port = 3010
    logging.info(f"waiting for port {port} to be free")
    while port_busy(port):
        time.sleep(1)
    time.sleep(5)
    cmds  = [
        f"{sicstus} --noinfo -l {os.path.join(dalipath, 'active_server_wi.pl')} --goal go."
    ]
    for name in src["agents"]:
        with open(os.path.join(agentsdir, f'{name}.txt'), 'w') as f:
            f.write(src['agents'][name]["code"])
        os.chmod(os.path.join(agentsdir, f'{name}.txt'), 0o755)
        setup = f"agent('{agentsdir}/{name}', '{name}','no',italian,['{confdir}/communication'],['{dalipath}/communication_fipa','{dalipath}/learning','{dalipath}/planasp'],'no','{dalipath}/onto/dali_onto.txt',[])."
        with open(os.path.join(setupsdir, f'{name}.txt'), 'w') as f:
            f.write(setup)
        os.chmod(os.path.join(setupsdir, f'{name}.txt'), 0o755)
        cmds += [
            " ".join([sicstus, '--noinfo', '-l', os.path.join(dalipath, 'active_dali_wi.pl'), '--goal', f'"start0(\'{os.path.join(setupsdir, f'{name}.txt')}\')."'])
        ]
    cmds += [
        f"{sicstus} --noinfo -l {os.path.join(dalipath, 'active_user_wi.pl')} --goal user_interface."
    ]
    return cmds


class InteractiveShell(ui.element):
    def __init__(self, *, cmd: str, title: str, _client = None):
        super().__init__('div', _client=_client)
        self.classes("p-10 font-mono bg-black").props("dark")
        with self:
            self.process = subprocess.Popen(
                shlex.split(cmd),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            ui.label(title).classes("text-negative")
            self.output = ui.log(max_lines=1000).classes(
                "text-green-500 overflow-auto"
            )
            ui.input("?-", placeholder='start typing').on('keydown.enter', self.on_enter).classes(
                "rounded outlined dense"
            ).props('input-style="color: #87CEEB" input-class="font-mono"')
            asyncio.create_task(self.read_stdout())
    async def on_enter(self, e):
        cmd = e.sender.value
        e.sender.value = ""
        self.output.push(f"?- {cmd}")
        if self.process.stdin:
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()
    async def read_stdout(self):
        loop = asyncio.get_running_loop()
        while True:
            line = await loop.run_in_executor(None, self.process.stdout.readline)
            if not line:
                await asyncio.sleep(.1)
                continue
            self.output.push(line.rstrip())
            await asyncio.sleep(.1)


@ui.page("/")
async def index():
    root = os.path.dirname(os.path.abspath(__file__))
    ui.colors(primary='#000')
    ui.add_css(r'''
                a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}
                ::-webkit-scrollbar {
                width: 20px;
                }
                ::-webkit-scrollbar-track {
                box-shadow: inset 0 0 5px rgb(255 255 255 / 10%);
                border-radius: 10px;
                }
                ::-webkit-scrollbar-thumb {
                background: linear-gradient(45deg, #94a3b8, #a8a29e); 
                border-radius: 10px;
                }
                body {
                background: #1D1D1D
                }
    ''')
    ui.query('.q-page').classes('flex')
    ui.query('.nicegui-content').classes('w-full')
    with ui.header(elevated=True).classes("justify-between items-center"):
        with ui.avatar():
            ui.image(os.path.join(root, 'files', 'assets', 'DALI_logo.png'))
        ui.label("DALIA").style('color: #FFFFFF; font-size: 200%; font-weight: 900')
        with ui.button(icon='menu'):
            with ui.menu() as menu:
                ui.menu_item(f"Authors")
    cmds = build(root=root, sicstuspath=os.path.abspath(args.sicstuspath), dalipath=os.path.abspath(args.dalipath))
    
    with ui.card().classes("w-full flex justify-center items-center").props('dark'):
        with ui.grid(columns=2).classes('w-full').props('dark'):
            for idx, cmd in enumerate(cmds):
                logging.info(cmd)
                InteractiveShell(cmd=cmd, title=f"agent_{idx}")
                await asyncio.sleep(5)

    
if __name__ in {"__main__", "__mp_main__"}:
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--dalipath', type=str, required=True)
    argparser.add_argument('--sicstuspath', type=str, required=True)
    args      = argparser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.StreamHandler()
        ]
    )
    ui.run(
        title='DALIA', 
        favicon=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files', 'assets', 'DALI_logo.png'),
        storage_secret=uuid.uuid4().hex,
        host="0.0.0.0", 
        port=8080,
        reconnect_timeout=300
    )