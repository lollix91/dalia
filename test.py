import asyncio
import subprocess
from nicegui import ui


class InteractiveShell(ui.element):
    def __init__(self, *, appname, _client = None):
        super().__init__('div', _client=_client)
        with self:
            self.process = subprocess.Popen(
                [appname],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.output = ui.log(max_lines=1000).classes(
                "bg-black text-green-500 p-2 font-mono h-[500px] overflow-auto"
            )
            ui.input("?-").on('keydown.enter', self.on_enter).classes(
                "w-full bg-gray-900"
            ).props('input-style="color: white" input-class="font-mono"')
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

    InteractiveShell(appname='swipl')

ui.run(title="Prolog Terminal")
