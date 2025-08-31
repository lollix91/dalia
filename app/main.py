import os 
import uuid
import git
import glob
import logging
import asyncio
import subprocess
from nicegui import ui


root = ""

def check_port(port):
    result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
    logging.info(result.stdout)
    return f"{port}" not in result.stdout

def check_sicstus():
    sicstus = ""
    path    = os.path.join(root, 'files', 'sicstus', 'bin', 'sicstus')
    if os.path.isfile(path) and os.access(path, os.X_OK):
        sicstus = path
    return sicstus

def enuredali():
    try:
        repodir = os.path.join(root, 'files', 'dali')
        if os.path.exists(repodir):
            git.Repo(repodir).remotes.origin.pull()
        else:
            git.Repo.clone_from(
                'https://github.com/AAAI-DISIM-UnivAQ/DALI',
                repodir,
                branch='main'
            )
        paths = {
            "DALI_HOME": os.path.join(root, 'files', 'dali', 'src'),
            "DALI_MODULAR_HOME": os.path.join(root, 'files', 'dali', 'src'),
            "COMMUNICATION_DIR": os.path.join(root, 'files', 'dali', 'src'),
            "CONF_DIR": os.path.join(root, 'files', 'src', 'conf'),
            "INSTANCES_HOME": os.path.join(root, 'files', 'src', 'mas', 'instances'),
            "TYPES_HOME": os.path.join(root, 'files', 'src', 'mas', 'types')
        }
        logging.info(f"directories: {paths}")
        for name in paths:
            if not os.path.isdir(paths[name]):
                logging.info(f"directory not found: {paths[name]}")
                return False, {}
        extra = {
            "BUILD_HOME": os.path.join(root, 'files', 'src', 'build'),
            "WORK_HOME": os.path.join(root, 'files', 'src', 'build'),
            "TEMP_DIR": os.path.join(root, 'files', 'src', 'temp')
        }
        for name in extra:
            os.makedirs(extra[name], exist_ok=True)
            paths[name] = extra[name]
        return True, paths
    except Exception as e:
        logging.exception(e)
    return False, {}

def build(directories, sicstus):    
    for directory in [
        directories['INSTANCES_HOME']
    ]:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    for instance_filename in glob.glob(os.path.join(directories['INSTANCES_HOME'], '**', '*.txt'), recursive=True):
        if not os.path.isfile(instance_filename):
            return False, f"Error: No instance files found in {directories['INSTANCES_HOME']}"
        logging.info(instance_filename)
        with open(instance_filename, 'r') as f:
            type = f.read().strip()
        type_filename = os.path.join(directories['TYPES_HOME'], f"{type}.txt")
        logging.info(type_filename)
        if not os.path.isfile(type_filename):
            return False, f"Error: Type file {type_filename} not found"
        instance_base = os.path.basename(instance_filename)
        logging.info(instance_base)
        with open(os.path.join(directories['BUILD_HOME'], instance_base), 'w') as f:
            f.write(type_filename)
        os.chmod(os.path.join(directories['BUILD_HOME'], instance_base), 0o755)
    for instance_filename in glob.glob(os.path.join(directories['BUILD_HOME'], '**', '*.*'), recursive=True):
        agent_base = os.path.basename(instance_filename)
        result = subprocess.run([os.path.join(directories['CONF_DIR'], 'makeconf.sh'), agent_base, directories['DALI_HOME']], capture_output=True, text=True)
        logging.info(result)
        result = subprocess.run([os.path.join(directories['CONF_DIR'], 'startagent_modular.sh'), agent_base, sicstus, directories['DALI_HOME']], capture_output=True, text=True)
        logging.info(result)

def waiting():
    with ui.dialog(value=True).props('persistent') as dialog, ui.card().classes("flex justify-center items-center"):
        ui.spinner(type='dots').classes('text-5xl')
        ui.label('We are wating for other services to become available')
    return dialog

def problem(message):
    with ui.dialog(value=True).props('persistent') as dialog, ui.card().classes("flex justify-center items-center"):
        ui.icon('error', color='negative').classes('text-5xl')
        ui.label(message)
    return dialog

@ui.page("/")
async def index():
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
    dialog = waiting()
    while check_port(8080):
        await asyncio.sleep(1)
    dialog.close()
    sicstus = check_sicstus()
    if not sicstus:
        problem("Sicstus was not found")
        return
    is_dali, directories = enuredali()
    logging.info(f"finding directories {directories}")
    if not is_dali:
        problem("DALI was not found")
        return
    build(directories, sicstus)
    with ui.header(elevated=True).classes("justify-between items-center"):
        with ui.avatar():
            ui.image(os.path.join(root, 'files', 'assets', 'DALI_logo.png'))
        ui.label("DALIA").style('color: #FFFFFF; font-size: 200%; font-weight: 900')
        with ui.button(icon='menu'):
            with ui.menu() as menu:
                ui.menu_item(f"Authors")
    with ui.left_drawer(top_corner=True, elevated=True).props("dark"):
        with ui.column().classes("w-full flex justify-center items-center"):
            with ui.tabs().props('vertical').classes('w-full') as tabs:
                ui.tab('h', label='Home', icon='home')
                ui.tab('a', label='About', icon='info')
    with ui.card().classes("w-full h-[85vh] flex justify-center items-center").props('dark'):
        with ui.tab_panels(tabs, value='h').classes('w-full').props('dark'):
            with ui.tab_panel('h'):
                for _ in range(100):
                    ui.chat_message('Hello NiceGUI!',
                        name='Robot',
                        stamp='now',
                        sent=True,
                        avatar='http://localhost:8081/ui')
            with ui.tab_panel('a'):
                ui.label('Infos')

    
if __name__ in ["__main__", "__mp_main__"]:
    root = os.path.dirname(os.path.abspath(__file__))
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler(os.path.join(root, 'files', 'DALIA.log'), mode='a'),
            logging.StreamHandler()
        ]
    )
    ui.run(
        title='DALIA', 
        favicon=os.path.join(root, 'files', 'assets', 'DALI_logo.png'),
        storage_secret=uuid.uuid4().hex,
        host="0.0.0.0", 
        port=8080,
        reconnect_timeout=300
    )