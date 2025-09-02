import os
import re
import pty
import subprocess
import threading
from nicegui import ui


ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def strip_ansi(text: str) -> str:
    return ansi_escape.sub('', text)

class Terminal:
    def __init__(self, cmd: str, parent):
        with parent:
            # Create PTY
            self.master_fd, self.slave_fd = pty.openpty()
            
            # Start the external interpreter
            self.process = subprocess.Popen(
                cmd.split(),   # list of args
                stdin=self.slave_fd,
                stdout=self.slave_fd,
                stderr=self.slave_fd,
                text=True,
                bufsize=0,     # unbuffered
            )
            os.close(self.slave_fd)  # close slave in parent
            
            # Create UI elements
            self.output = ui.log(max_lines=1000).classes(
                "bg-black text-green-500 p-2 font-mono h-[400px] overflow-auto"
            ).style('white-space: pre;')
            self.input = ui.input("?-").classes(
                "w-full bg-gray-900 text-white font-mono p-2 rounded"
            ).on('keydown.enter', self.send_command)
        
        
        # Start reading output in background
        threading.Thread(target=self.read_output, daemon=True).start()
    
    def read_output(self):
        """Continuously read from the PTY master and push to UI"""
        while True:
            try:
                data = os.read(self.master_fd, 1024).decode(errors='ignore')
                if data:
                    self.output.push(strip_ansi(data))
                else:
                    break
            except OSError:
                break
    
    def send_command(self, e):
        """Send input to the interpreter"""
        cmd = e.sender.value
        e.sender.value = ""
        if self.process.poll() is not None:
            self.output.push("[process exited]")
            return
        os.write(self.master_fd, (cmd + "\n").encode())

# UI layout
ui.label("Multi-Terminal Prolog Example").classes("text-xl font-bold mb-2")
terminals_container = ui.column()

# Example: create two terminals
Terminal("swipl -q --no-tty", terminals_container)
Terminal("swipl -q --no-tty", terminals_container)

ui.run(title="Multi-Terminal Prolog")
