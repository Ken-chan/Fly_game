import pyglet
from multiprocessing import Process
from view import Renderer
from messages import Messenger
import messages
from gui_controls import GUIcontrols
from objects import Objects
from obj_def import *
import math

class GameState:
    Start, ActiveGame, Menu, Exit = range(4)



class Game(Process):
    def __init__(self, screen_width, screen_height):
        super(Game, self).__init__()
        self.game_state = GameState.Start
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.messenger = Messenger()
        self.renderer = Renderer(self.screen_width, self.screen_height)
        self.gui_controls = GUIcontrols(self.messenger, screen_width, screen_height)
        self.gui_controls.start()

        self.objects = Objects(messenger=self.messenger)
        self.objects.start()

        self.functions = {messages.Game.Quit: self.quit,
                          messages.Game.UpdateObjects: self.update_objects}

    def quit(self):
        self.game_state = GameState.Exit
        self.messenger.shutdown()
        self.objects.join()
        self.gui_controls.join()
        pyglet.app.exit()

    def read_messages(self, dt):
        while True:
            data = self.messenger.get_message(messages.Game)
            if not data:
                return

            self.functions[data['func']](**data['args']) if 'args' in data else self.functions[data['func']]()


    def update_graphics(self, dt):
        self.renderer.update_graphics()
        self.game_window.clear()
        self.renderer.batch.draw()

    def update_objects(self, objects_copy):
        self.objects = objects_copy
        self.renderer.update_objects(objects_copy)

    def run_game(self):
        self.game_window = pyglet.window.Window(self.screen_width, self.screen_height)
        pyglet.gl.glClearColor(0, 1, 1, 1)

        configuration = {ObjectType.Team1: [],
                         ObjectType.Bot1: [],
                         ObjectType.Player1: [],
                         ObjectType.Team2: [],
                         ObjectType.Bot2: [],
                         ObjectType.Player2: []}
        configuration[ObjectType.Player1].append((500, 100))


        self.game_state = GameState.ActiveGame
        self.messenger.objects_run_simulation()
        self.messenger.objects_set_game_settings(configuration)

        @self.game_window.event
        def on_key_press(key, modif):
            self.messenger.controls_handle_key(True, key)

        @self.game_window.event
        def on_key_release(key, modif):
            self.messenger.controls_handle_key(False, key)

        @self.game_window.event
        def on_close():
            self.quit()



        pyglet.clock.schedule_interval(self.update_graphics, 1.0 / 30)
        pyglet.clock.schedule_interval(self.read_messages, 1/30.0)
        pyglet.app.run()

if __name__ == "__main__":
    game = Game(1024,768)
    game.run_game()










