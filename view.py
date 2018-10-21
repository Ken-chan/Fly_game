from game import Game, GameState
from multiprocessing import Process
import pyglet
from pyglet.window import key

def run_gui(self):
    game_window = pyglet.window.Window(self.screen_width, self.screen_height)
    keys = key.KeyStateHandler()
    game_window.push_handlers(keys)

    pyglet.gl.glClearColor(0, 0, 1, 1)
    self.main_batch = pyglet.graphics.Batch()
    self.counter = pyglet.clock.ClockDisplay()

    @self.game_window.event
    def on_draw():
        self.game_window.clear()

    @self.game_window.event
    def on_close():
        self.quit()