import os
import pty
import shlex
import threading
import asyncio
import subprocess
from nicegui import ui


class InteractiveShell(ui.element):
    def __init__(self, *, cmd, title, _client = None):
        super().__init__('div', _client=_client)
        self.classes("p-10 font-mono bg-black").props("dark")
        with self:
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
            ui.label(title).classes("text-negative")
            self.output = ui.log(max_lines=1000).classes(
                "text-green-500 overflow-auto"
            )
            ui.input("?-", placeholder='start typing').on('keydown.enter', self.on_enter).classes(
                "rounded outlined dense"
            ).props('input-style="color: #87CEEB" input-class="font-mono"')
            threading.Thread(target=self.read_output, daemon=True).start()
    async def on_enter(self, e):
        cmd = e.sender.value
        e.sender.value = ""
        if self.process.poll() is not None:
            self.output.push("[process exited]")
            return
        self.output.push(f"?- {cmd}")
        os.write(self.master_fd, (cmd + "\n").encode())
    def read_output(self):
        while True:
            try:
                data = os.read(self.master_fd, 20000).decode(errors='ignore')
                if data:
                    self.output.push(data)
                else:
                    break
            except OSError:
                break

@ui.page("/")
async def index():

    InteractiveShell(cmd='swipl', title="Agent1")

ui.run(title="Prolog Terminal")
