#initialize the screen
import pyglet
from Bot import Bot
from Player import Player
from pyglet.window import key
import sys


window = pyglet.window.Window(1024,768)
pyglet.gl.glClearColor(0, 0, 1, 1)

@window.event
def on_key_press(symbol, modifiers):
    if symbol == key.RIGHT:
        player.k_right = 1
    elif symbol == key.LEFT:
        player.k_left = 1
    elif symbol == key.DOWN:
        player.k_down = 1
    elif symbol == key.UP:
        player.k_up = 1

    elif symbol == key.ESCAPE:
        sys.exit(0)


player = Player(100,100)
bot = Bot(500,800)

@window.event
def on_draw():
    window.clear()
    bot.Bot_sprite.draw()
    player.Player_sprite.draw()

def update(dt):
    bot.update()
    player.update()

if __name__ == "__main__":
    pyglet.clock.schedule_interval(update, 1.0/60)
    pyglet.app.run()

