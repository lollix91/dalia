from robohash import Robohash
from nicegui import ui 

hash = "bob"
rh = Robohash(hash)
rh.assemble(roboset='set5')
with ui.avatar():
    ui.image(rh.img)

ui.run()