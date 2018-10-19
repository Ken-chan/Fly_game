import game
import pyglet
from pyglet.window import key
import sys

window = pyglet.window.Window(1024,768)

@window.event
def on_key_press(symbol, modifiers):
    if symbol == key.SPACE:
        window.close()
        game1 = game.Game(1024,768)
        game1.run_game()

    elif symbol == key.ESCAPE:
        sys.exit(0)

image = pyglet.resource.image("images/Plane_start_pic.png")

@window.event
def on_draw():
    window.clear()
    image.blit(0, 0)

pyglet.app.run()


