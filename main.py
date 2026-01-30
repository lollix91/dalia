import os 
import re
import pty
import uuid
import time
import json
import shlex
import logging
import asyncio
import tempfile
import argparse
import socket
import threading
# Removed: import requests
import openai
import subprocess
from robohash import Robohash
from nicegui import ui, background_tasks, run, app

# --- CONFIGURAZIONE LLM BRIDGE ---
LLM_PORT = 9000 

def query_llm_service(prompt):
    """Logica per chiamare l'LLM (OpenAI)"""
    try:
        api_key = args.openai_key or os.environ.get("OPENAI_API_KEY")
        
        if not api_key or api_key.strip() == "":
            logging.info(f"Ricevuta richiesta '{prompt[:10]}...' ma LLM disabilitato.")
            # Default fallback in formato Prolog se offline
            return "advice(stay_safe)." 

        client = openai.OpenAI(api_key=api_key)
        
        # --- MODIFICA PROMPT: FORZIAMO L'OUTPUT PROLOG ---
        system_instruction = (
            "Sei un modulo logico per un agente DALI. "
            "Il tuo output deve essere UNICAMENTE un fatto Prolog valido terminato da punto. "
            "Nessun testo, nessun markdown, nessuna spiegazione. "
            "Esempio: suggestion(evacuate_immediately)."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Context: {prompt}. What is the best strategic fact?"}
            ],
            max_tokens=50,
            temperature=0.3 # Bassa temperatura per essere più deterministici
        )
        
        content = response.choices[0].message.content.strip()
        
        # Pulizia extra: rimuove eventuali backticks del markdown se l'LLM disubbidisce
        content = content.replace("```prolog", "").replace("```", "").strip()
        
        return content
        
    except Exception as e:
        logging.error(f"OpenAI Exception: {e}")
        # Fallback di errore in formato Prolog
        return "error(api_failure)."

def llm_client_handler(conn, addr):
    logging.info(f"LLM Bridge: Connessione da {addr}")
    try:
        data = conn.recv(4096).decode('utf-8')
        if data:
            clean_text = data.strip().rstrip('.')
            logging.info(f"LLM Bridge: Richiesta -> {clean_text}")
            
            response = query_llm_service(clean_text)
            
            # Formattazione per Prolog: rimuove apici e caratteri che rompono la sintassi
            safe_response = response.replace("'", "").replace('"', "").replace("\n", " ")
            prolog_msg = f"'{safe_response}'.\n"
            
            conn.sendall(prolog_msg.encode('utf-8'))
    except Exception as e:
        logging.error(f"LLM Bridge Error: {e}")
    finally:
        conn.close()

def run_server_loop():
    """Il loop infinito del server TCP"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(('127.0.0.1', LLM_PORT))
        server.listen(5)
        logging.info(f"✅ LLM SERVER PRONTO SU 127.0.0.1:{LLM_PORT}")
        
        while True:
            try:
                conn, addr = server.accept()
                threading.Thread(target=llm_client_handler, args=(conn, addr), daemon=True).start()
            except Exception as inner_e:
                logging.error(f"Errore connessione: {inner_e}")
                
    except OSError:
        logging.warning(f"⚠️ Porta {LLM_PORT} occupata. Probabile reload di NiceGUI. Il server dovrebbe essere già attivo.")

def start_llm_background():
    """Avvia il thread in background all'avvio di NiceGUI"""
    threading.Thread(target=run_server_loop, daemon=True).start()

# --- CLASSI DI UTILITÀ DALIA ---
class AnsiStrip:
    def __init__(self):
        self.ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    def __call__(self, text: str) -> str:
        return self.ansi_escape.sub('', text)

def has_port(text: str, port: int) -> bool:
    pattern = rf"(?<!\d):?{port}\b"
    return re.search(pattern, text) is not None

def port_busy(port):
    result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
    return has_port(result.stdout, port)

def load_src(dirpath):
    result = {"agents": dict(), "comm": ""}
    instancespath = os.path.join(dirpath, 'instances.json')
    try:
        with open(instancespath, 'r') as f:
            instances = json.loads(f.read())
    except: return {} 
    
    try:
        for name, type in instances.items():
            path = os.path.join(dirpath, 'types', f'{type}.txt') 
            with open(path, 'r') as f:
                code = f.read().strip()
            result["agents"][name] = {"type": type, "code": code}
    except: return {} 
    
    commpath = os.path.join(dirpath, 'conf', f'communication.con')
    try:
        with open(commpath, 'r') as f:
            result["comm"] = f.read().strip()
    except: return {} 
    return result

def rmdir(path):
    if os.path.exists(path) and os.path.isdir(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for file in files: os.remove(os.path.join(root, file))
            for dir in dirs: os.rmdir(os.path.join(root, dir))
        os.rmdir(path)

def build(*, src, dali):
    src_data = load_src(src)
    if not src_data: return
    
    workdir = tempfile.mkdtemp()
    subprocess.run("pkill -9 sicstus 2>/dev/null || true", shell=True)
    
    dali_src = os.path.join(dali, 'src')
    sicstus = 'sicstus'
    
    rmdir(workdir)
    agentsdir = os.path.join(workdir, 'agents')
    setupsdir = os.path.join(workdir, 'setups')
    confdir = os.path.join(workdir, 'conf')
    logdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
    
    rmdir(logdir)
    for d in [logdir, setupsdir, agentsdir, confdir]:
        os.makedirs(d, exist_ok=True)
        
    with open(os.path.join(confdir, f'communication.con'), 'w') as f:
        f.write(src_data["comm"])
        
    port = 3010
    while port_busy(port): time.sleep(1)
    time.sleep(2)
    
    cmds = {"server": f"{sicstus} --noinfo -l {os.path.join(dali_src, 'active_server_wi.pl')} --goal go."}
    
    for name in src_data["agents"]:
        with open(os.path.join(agentsdir, f'{name}.txt'), 'w') as f:
            f.write(src_data['agents'][name]["code"])
        os.chmod(os.path.join(agentsdir, f'{name}.txt'), 0o755)
        
        setup = f"agent('{agentsdir}/{name}', '{name}','no',italian,['{confdir}/communication'],['{dali_src}/communication_fipa','{dali_src}/learning','{dali_src}/planasp'],'no','{dali_src}/onto/dali_onto.txt',[])."
        
        with open(os.path.join(setupsdir, f'{name}.txt'), 'w') as f:
            f.write(setup)
        os.chmod(os.path.join(setupsdir, f'{name}.txt'), 0o755)
        
        cmds[f"{name}"] = " ".join([sicstus, '--noinfo', '-l', os.path.join(dali_src, 'active_dali_wi.pl'), '--goal', f'"start0(\'{os.path.join(setupsdir, f'{name}.txt')}\')."'])
        
    cmds["user"] = f"{sicstus} --noinfo -l {os.path.join(dali_src, 'active_user_wi.pl')} --goal user_interface."
    return cmds

class InteractiveShell(ui.element):
    def __init__(self, *, cmd: str, title: str, value: str ='', _client = None):
        super().__init__('div', _client=_client)
        self.classes("p-4 font-mono bg-black").props("dark")
        with self:
            self.title = title
            self.strip_ansi = AnsiStrip()
            self.master_fd, self.slave_fd = pty.openpty()
            self.process = subprocess.Popen(shlex.split(cmd), stdin=self.slave_fd, stdout=self.slave_fd, stderr=self.slave_fd, text=True, bufsize=0)
            os.close(self.slave_fd)
            
            rh = Robohash(title)
            roboset = 'set5' if title == 'user' else ('set1' if 'agent' in title else 'set2')
            rh.assemble(roboset=roboset)
            
            with ui.row(align_items='center'):
                with ui.avatar(): ui.image(rh.img)
                ui.label(title).classes("text-negative")
            
            self.output = ui.log().classes("text-green-500 overflow-y-auto break-all").style('white-space: pre-wrap;')
            self.input = ui.input(value=value, placeholder='?-').on('keydown.enter', self.on_enter).classes("rounded outlined dense").props('input-style="color: #87CEEB" input-class="font-mono" clearable')
            threading.Thread(target=self.read_output, daemon=True).start()

    async def on_enter(self, e):
        cmd = e.sender.value
        e.sender.value = ""
        if self.process.poll() is not None:
            self.output.push("[process exited]")
            return
        os.write(self.master_fd, (cmd + "\n").encode())

    def read_output(self):
        while True:
            try:
                data = os.read(self.master_fd, 1024).decode(errors='ignore')
                if data: self.output.push(self.strip_ansi(data))
                else: break
            except OSError: break

class Info(ui.dialog):
    def __init__(self, mapping: dict):
        super().__init__(value=False)
        with self, ui.card().classes('w-[100vw]'):
            ui.icon('close', color='negative', size='lg').props("outlined").on('click', self.close)
            with ui.list().classes("w-full"):
                for title, path in mapping.items():
                    try:
                        with open(path, 'r') as f: content = f.read()
                    except: content = ''
                    if content:
                        with ui.item(), ui.expansion(title).classes('w-full') as exp:
                            exp.tailwind.text_color('pink-400')
                            ui.markdown(content=content)

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
            cmds = await run.cpu_bound(build, src=os.path.abspath(args.src), dali=os.path.abspath(args.dali))
            self.remove(waiting)
        with self.grid:
            if cmds:
                server = cmds.pop('server')
                InteractiveShell(cmd=server, title='server')
                await asyncio.sleep(5)
                user = cmds.pop('user')
                InteractiveShell(cmd=user, title='user', value="")
                await asyncio.sleep(5)
                for title, cmd in cmds.items():
                    InteractiveShell(cmd=cmd, title=title)
                    await asyncio.sleep(5)

@ui.page("/")
async def index(client):
    ui.colors(primary='#000')
    ui.add_css(r'body { background: #1D1D1D; }')
    with ui.header(elevated=True).classes("justify-between items-center"):
        ui.label("DALIA").style('color: #FFFFFF; font-size: 200%; font-weight: 900')
    with ui.card().classes("w-full flex justify-center items-center overflow-auto").props('dark'):
        Main()

if __name__ in {"__main__", "__mp_main__"}:
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--src', type=str, required=not os.environ.get('docker', False), default='/src')
    argparser.add_argument('--dali', type=str, required=not os.environ.get('docker', False), default='/dali')
    argparser.add_argument('--sicstus', type=str, required=not os.environ.get('docker', False), default='/sicstus')
    
    # Prende la chiave dalla variabile d'ambiente (se settata da run.bat)
    argparser.add_argument('--openai_key', type=str, default=os.environ.get('OPENAI_API_KEY'))
    
    args = argparser.parse_args()
    logging.basicConfig(level=logging.INFO)

    # Avvia il server LLM (che sarà "muto" se non c'è la chiave)
    app.on_startup(start_llm_background)
    
    ui.run(title='DALIA', host="0.0.0.0", port=8118, reconnect_timeout=300)