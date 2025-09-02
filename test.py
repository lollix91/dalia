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

    InteractiveShell(appname='swipl', title="Agent1")

ui.run(title="Prolog Terminal")
