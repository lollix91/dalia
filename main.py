import os 
import re
import uuid
import time
import json
import shlex
import logging
import asyncio
import tempfile
import argparse
import threading
import subprocess
import socket

try:
    import pty
except ImportError:  # pty is not available on Windows
    pty = None
from robohash import Robohash
from nicegui import ui, background_tasks, run, app


class AnsiStrip:
    def __init__(self):
        self.ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    def __call__(self, text: str) -> str:
        return self.ansi_escape.sub('', text)

def has_port(text: str, port: int) -> bool:
    pattern = rf"(?<!\d):?{port}\b"
    return re.search(pattern, text) is not None

def port_busy(port):
    """Return True if the TCP port is already in use on localhost.

    Instead of parsing platform-dependent netstat output, we simply try to
    bind a socket on the given port. If bind fails, we assume the port is
    busy. This works both on Windows and Unix-like systems.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            logging.info(f"port {port} appears to be busy")
            return True
    logging.info(f"port {port} appears to be free")
    return False

def load_src(dirpath):
    result      = {
        "agents": dict(),
        "comm": ""
    }
    instancespath = os.path.join(dirpath, 'instances.json')
    try:
        with open(instancespath, 'r') as f:
            instances = json.loads(f.read())
    except Exception as e:
        logging.exception(f"{instancespath} does not exist")
        return {} 
    try:
        for name, type in instances.items():
            path = os.path.join(dirpath, 'types', f'{type}.txt') 
            assert os.path.isfile(path)
            assert name not in ['user', 'server']
            with open(path, 'r') as f:
                code = f.read().strip()
            result["agents"][name] = {
                "type": type,
                "code": code
            }
    except Exception as e:
        logging.exception(f"problem with instancess in {instancespath}")
        return {} 
    commpath = os.path.join(dirpath, 'conf', f'communication.con')
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

def build(*, src, dali, prolog):
    src = load_src(src)
    if not src:
        return
    workdir = tempfile.mkdtemp()
    in_docker = bool(os.environ.get('docker', False))
    if in_docker and os.name != 'nt':
        try:
            p = subprocess.Popen("pkill -9 sicstus 2>/dev/null || true", shell=True)
            p.wait()
        except Exception as e:
            logging.exception(e)
    dali     = os.path.join(dali, 'src')

    rmdir(workdir)
    agentsdir_fs = os.path.join(workdir, 'agents')
    setupsdir_fs = os.path.join(workdir, 'setups')
    confdir_fs   = os.path.join(workdir, 'conf')
    logdir    = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
    rmdir(logdir)
    os.makedirs(logdir, exist_ok=True)
    os.makedirs(setupsdir_fs, exist_ok=True)
    os.makedirs(agentsdir_fs, exist_ok=True)
    os.makedirs(confdir_fs, exist_ok=True)
    with open(os.path.join(confdir_fs, f'communication.con'), 'w') as f:
        f.write(src["comm"])
    agentsdir = agentsdir_fs.replace('\\', '/')
    setupsdir = setupsdir_fs.replace('\\', '/')
    confdir   = confdir_fs.replace('\\', '/')
    dali_norm = dali.replace('\\', '/')

    prolog_cmd = 'sicstus' if in_docker else (prolog or 'swipl')

    port = 3010
    logging.info(f"waiting for port {port} to be free")
    while port_busy(port):
        time.sleep(1)
    time.sleep(5)
    server_pl = f"{dali_norm}/active_server_wi.pl"
    user_pl   = f"{dali_norm}/active_user_wi.pl"
    dali_pl   = f"{dali_norm}/active_dali_wi.pl"

    if prolog_cmd == 'sicstus':
        cmds  = {
            "server": f"{prolog_cmd} --noinfo -l \"{server_pl}\" --goal go."
        }
    else:
        cmds  = {
            "server": f"{prolog_cmd} -q -l \"{server_pl}\" -g go"
        }

    for name in src["agents"]:
        with open(os.path.join(agentsdir_fs, f'{name}.txt'), 'w') as f:
            f.write(src['agents'][name]["code"])
        os.chmod(os.path.join(agentsdir_fs, f'{name}.txt'), 0o755)
        setup = f"agent('{agentsdir}/{name}', '{name}','no',italian,['{confdir}/communication'],['{dali_norm}/communication_fipa','{dali_norm}/learning','{dali_norm}/planasp'],'no','{dali_norm}/onto/dali_onto.txt',[])."

        with open(os.path.join(setupsdir_fs, f'{name}.txt'), 'w') as f:
            f.write(setup)
        os.chmod(os.path.join(setupsdir_fs, f'{name}.txt'), 0o755)
        setup_path = os.path.join(setupsdir, f'{name}.txt').replace('\\', '/')
        if prolog_cmd == 'sicstus':
            cmds[f"{name}"] = " ".join([
                prolog_cmd,
                '--noinfo',
                '-l',
                f"\"{dali_pl}\"",
                '--goal',
                f'"start0(\'{setup_path}\')."',
            ])
        else:
            cmds[f"{name}"] = " ".join([
                prolog_cmd,
                '-q',
                '-l',
                f"\"{dali_pl}\"",
                '-g',
                f"start0('{setup_path}')",
                '-t',
                'halt',
            ])
    if prolog_cmd == 'sicstus':
        cmds["user"] = f"{prolog_cmd} --noinfo -l \"{user_pl}\" --goal user_interface."
    else:
        cmds["user"] = f"{prolog_cmd} -q -l \"{user_pl}\" -g utente"

    return cmds


class InteractiveShell(ui.element):
    def __init__(self, *, cmd: str, title: str, value: str ='', _client = None):
        super().__init__('div', _client=_client)
        self.classes("p-4 font-mono bg-black").props("dark")
        with self:
            self.title = title
            self.strip_ansi = AnsiStrip()
            self._use_pty = bool(pty and os.name != 'nt')
            self.master_fd = None
            if self._use_pty:
                self.master_fd, self.slave_fd = pty.openpty()
                self.process = subprocess.Popen(
                    shlex.split(cmd),
                    stdin=self.slave_fd,
                    stdout=self.slave_fd,
                    stderr=self.slave_fd,
                    text=True,
                    bufsize=0,
                )
                os.close(self.slave_fd)
            else:
                self.process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    shell=True,
                )
            rh = Robohash(title)

            if title == 'user':
                roboset='set5'
            elif 'agent' in title:
                roboset='set1'
            else:
                roboset='set2'
            rh.assemble(roboset=roboset)
            with ui.row(align_items='center'):
                with ui.avatar():
                    ui.image(rh.img)
                ui.label(title).classes("text-negative")
            self.output = ui.log().classes(
                "text-green-500 overflow-y-auto break-all"
            ).style('white-space: pre-wrap;')
            self.input = ui.input(value=value, placeholder='?-').on('keydown.enter', self.on_enter).classes(
                "rounded outlined dense"
            ).props('input-style="color: #87CEEB" input-class="font-mono" clearable')
            threading.Thread(target=self.read_output, daemon=True).start()
    async def on_enter(self, e):
        cmd = e.sender.value
        e.sender.value = ""
        if self.process.poll() is not None:
            self.output.push("[process exited]")
            return
        if self._use_pty and self.master_fd is not None:
            os.write(self.master_fd, (cmd + "\n").encode())
        elif self.process.stdin:
            try:
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()
            except Exception as exc:
                logging.exception(exc)
    def read_output(self):
        if self._use_pty and self.master_fd is not None:
            while True:
                try:
                    data = os.read(self.master_fd, 1024).decode(errors='ignore')
                    if data:
                        self.output.push(self.strip_ansi(data))
                    else:
                        msg = f"OSError in {self.title}"
                        break
                except OSError:
                    msg = f"{self.master_fd} unreadable in {self.title}"
                    break
        else:
            while True:
                try:
                    if self.process.stdout is None:
                        msg = f"No stdout for process in {self.title}"
                        break
                    data = self.process.stdout.readline()
                    if not data:
                        if self.process.poll() is not None:
                            msg = f"process exited in {self.title}"
                            break
                        continue
                    self.output.push(self.strip_ansi(data))
                except Exception as exc:
                    msg = f"Error reading stdout in {self.title}: {exc}"
                    break
        logging.exception(msg)
        self.output.push(self.strip_ansi(msg))


class Info(ui.dialog):
    def __init__(self, mapping: dict):
        super().__init__(value=False)
        with self, ui.card().classes('w-[100vw]'):
            ui.icon('close', color='negative', size='lg').props("outlined").on('click', self.close)
            ui.label('LICENSES').tailwind.text_color('orange-600')
            with ui.list().classes("w-full"):
                for title, path  in mapping.items():
                    content = ''
                    try:
                        with open(path, 'r') as f:
                            content = f.read()
                    except Exception as e:
                        logging.exception(e)
                        content = ''
                    if not content:
                        continue
                    with ui.item():
                        with ui.expansion(title).classes('w-full') as exp:
                            exp.tailwind.text_color('pink-400')
                            ui.markdown(content=content).tailwind.text_color('black')
                    ui.separator()
    async def __call__(self):
        self.open()


class Main(ui.row):
    def __init__(self):
        super().__init__()
        self.classes('w-full justify-center items-center').props('dark')
        with self:
            self.grid = ui.grid(columns=2).classes('w-full justify-center items-center').props('dark')
        background_tasks.create(self())
    async def __call__(self):
        with self:
            with ui.column().classes('w-full justify-center items-center').props('dark') as waiting:
                ui.label(f"Building: {os.path.abspath(args.src)}")
                ui.spinner(type='bars', color='positive')
            cmds = await run.cpu_bound(build, src=os.path.abspath(args.src), dali=os.path.abspath(args.dali), prolog=args.prolog)
            self.remove(waiting)
        with self.grid:
            if cmds is not None:
                server = cmds.pop('server')
                logging.info(server)
                InteractiveShell(cmd=server, title='server')
                await asyncio.sleep(5)
                user = cmds.pop('user')
                logging.info(user)
                InteractiveShell(cmd=user, title='user', value="")
                await asyncio.sleep(5)
                for title, cmd in cmds.items():
                    logging.info(cmd)
                    InteractiveShell(cmd=cmd, title=title)
                    await asyncio.sleep(5)


def alreadyopen():
    with ui.dialog().props('persistent') as dialog, ui.card().classes("flex justify-center items-center"):
        ui.icon('error', color='negative').classes('text-5xl')
        ui.label('DALIA is already open somewhere else')
    dialog.open()
active_sessions = set()
@ui.page("/")
async def index(client):
    session_id = client.id
    if active_sessions and client.id not in active_sessions:
        alreadyopen()
        return
    active_sessions.add(session_id)
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
            ui.image(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'DALI_logo.png'))
        ui.label("DALIA").style('color: #FFFFFF; font-size: 200%; font-weight: 900')
        info = Info({
            'DALIA': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'LICENSE'),
            'DALI': os.path.join(os.path.abspath(args.dali), 'LICENSE')
        })
        ui.icon('info', size='lg').on('click', info)
    with ui.card().classes("w-full flex justify-center items-center overflow-auto").props('dark'):
        Main()
    with ui.footer(elevated=True).classes("justify-center items-center"):
        ui.label("Copyrights 2025 Aly Shmahell")
    @client.on_disconnect
    def _():
        active_sessions.discard(session_id)
        logging.info("GUI disconnected...")
        if os.name != 'nt':
            try:
                p = subprocess.Popen("pkill -9 sicstus 2>/dev/null || true", shell=True)
                p.wait()
            except Exception as e:
                logging.exception(e)


if __name__ in {"__main__", "__mp_main__"}:
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--src', type=str,       required=False, default='/src', help="path to the MAS source code (like the example folder)")
    argparser.add_argument('--dali', type=str,      required=False, default='/dali', help="path to the dali directory")
    argparser.add_argument('--prolog', '--sicstus', dest='prolog', type=str, required=False, default='swipl', help="path to the Prolog executable (e.g. swipl)")
    args      = argparser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.StreamHandler()
        ]
    )
    ui.run(
        title='DALIA', 
        favicon=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'DALI_logo.png'),
        storage_secret=uuid.uuid4().hex,
        host="0.0.0.0", 
        port=8118,
        reconnect_timeout=300
    )