import os 
import uuid
import logging
import asyncio
import subprocess
from nicegui import ui

class InteractiveShell(ui.element):
    def __init__(self, *, appname, title, _client = None):
        super().__init__('div', _client=_client)
        self.classes("p-10 font-mono bg-black").props("dark")
        with self:
            self.process = subprocess.Popen(
                [appname],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
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
                break
            self.output.push(line.rstrip())
            await asyncio.sleep(.1)


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
    with ui.header(elevated=True).classes("justify-between items-center"):
        with ui.avatar():
            ui.image(os.path.join(root, 'files', 'assets', 'DALI_logo.png'))
        ui.label("DALIA").style('color: #FFFFFF; font-size: 200%; font-weight: 900')
        with ui.button(icon='menu'):
            with ui.menu() as menu:
                ui.menu_item(f"Authors")
    with ui.card().classes("w-full flex justify-center items-center").props('dark'):
        with ui.grid(columns=2).classes('w-full').props('dark'):
            for idx in range(8):
                InteractiveShell(appname="sicstus", title=f"agent_{idx}")

    
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