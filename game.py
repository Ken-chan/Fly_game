import pyglet, json
from view import Renderer
import messages
from messages import Messenger
import argparse
import datetime
import time
from gui_controls import GUIcontrols
from ai_controls import AIcontrols, AItype
from objects import Objects
from obj_def import *

class GameState:
    Start, ActiveGame, Menu, Exit, Pause = range(5)


class Game:
    def __init__(self, screen_width, screen_height, history_path=None):
        super(Game, self).__init__()
        self.game_state = GameState.Start
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.battle_field_size = (1000, 1000)
        if history_path is None:
            now_time = datetime.datetime.now()
            self.history_path = now_time.strftime("%Y_%m_%d_%H_%M_%S")+'.txt'
            # self.history_path = 'history.txt'
            self.clear_file(self.history_path)
            self.is_it_move_from_history = False
        else:
            self.history_path = history_path
            self.is_it_move_from_history = True
        self.fps_display = pyglet.clock.ClockDisplay()

        self.configuration = {ObjectType.FieldSize: [],
                         ObjectType.Bot1: [],
                         ObjectType.Player1: [],
                         ObjectType.Bot2: [],
                         ObjectType.Player2: []}
        self.configuration[ObjectType.FieldSize].append(self.battle_field_size)
        self.configuration[ObjectType.Player1].append((500, 0, 90, ObjectSubtype.Plane, Constants.DefaultObjectRadius))
        self.configuration[ObjectType.Bot1].append(
            (400, 0, 90, ObjectSubtype.Plane, Constants.DefaultObjectRadius, AItype.DumbAi))
        self.configuration[ObjectType.Bot1].append(
            (700, 0, 90, ObjectSubtype.Plane, Constants.DefaultObjectRadius, AItype.DumbAi))
        self.configuration[ObjectType.Bot1].append(
            (200, 0, 90, ObjectSubtype.Plane, Constants.DefaultObjectRadius, AItype.DumbAi))
        self.configuration[ObjectType.Bot1].append(
            (300, 0, 90, ObjectSubtype.Plane, Constants.DefaultObjectRadius, AItype.DumbAi))
        self.configuration[ObjectType.Bot1].append(
            (600, 0, 90, ObjectSubtype.Plane, Constants.DefaultObjectRadius, AItype.DumbAi))

        self.configuration[ObjectType.Bot2].append(
            (500, 1000, 270, ObjectSubtype.Plane, Constants.DefaultObjectRadius, AItype.DumbAi))
        self.configuration[ObjectType.Bot2].append(
            (400, 1000, 270, ObjectSubtype.Plane, Constants.DefaultObjectRadius, AItype.DumbAi))
        self.configuration[ObjectType.Bot2].append(
            (300, 1000, 270, ObjectSubtype.Plane, Constants.DefaultObjectRadius, AItype.DumbAi))
        self.configuration[ObjectType.Bot2].append(
            (200, 1000, 270, ObjectSubtype.Plane, Constants.DefaultObjectRadius, AItype.DumbAi))
        self.configuration[ObjectType.Bot2].append(
            (700, 1000, 270, ObjectSubtype.Plane, Constants.DefaultObjectRadius, AItype.DumbAi))
        #self.configuration[ObjectType.Player2].append((600, 1000, 270, ObjectSubtype.Plane, Constants.DefaultObjectRadius))

        self.messenger = Messenger()
        self.Objects = Objects(self.messenger, self.configuration, history_path=self.history_path)
        self.ai_controls = AIcontrols(self.messenger, self.configuration)
        self.gui_controls = GUIcontrols(self.messenger)

        self.renderer = Renderer(self.screen_width, self.screen_height)

        self.objects = None
        self.history_list = []
        self.functions = {messages.Game.Quit: self.quit,
                          messages.Game.UpdateObjects: self.update_objects,
                          messages.Game.Pause: self.game_pause_simulation,
                          messages.Game.ActiveGame: self.game_unpaused}
                          #messages.Game.RestartGame: self.game_restart}

    # /Part of working with log files starts

    def clear_file(self, file_path):
        with open(file_path, "w") as file:  # just to open with argument which clean file
            pass

    # /Part of working with log files ends
    def quit(self):
        self.game_state = GameState.Exit
        self.messenger.shutdown()
        pyglet.app.exit()

    def game_pause_simulation(self):
        self.game_state = GameState.Pause

    def game_unpaused(self):
        self.game_state = GameState.ActiveGame

    #def game_restart(self):
    #    #self.quit()
    #    pyglet.app.exit()
    #    time.sleep(1)
    #    self.run_game() #THINKING ABOUT IT(HOW TO MAKE CORRECT)


    def read_messages(self, dt):
        while True:
            data = self.messenger.get_message(messages.Game)
            if not data:
                return
            self.functions[data['func']](**data['args']) if 'args' in data else self.functions[data['func']]()

    def update_graphics(self, dt):
        if self.game_state != GameState.Pause:
            self.renderer.update_graphics()
            self.game_window.clear()
            self.renderer.batch.draw()

    def update_objects(self, objects_copy):
        if self.game_state != GameState.Pause:
            self.objects = objects_copy
            self.renderer.update_objects(objects_copy)
            self.renderer.update_graphics()

    def run_game(self):

        self.game_window = pyglet.window.Window(self.screen_width, self.screen_height)
        pyglet.gl.glClearColor(0.6, 0.6, 0.6, 0)
        self.game_window.set_location(200, 50)
        self.game_state = GameState.ActiveGame
        self.renderer.set_battle_field_size(self.battle_field_size[0], self.battle_field_size[1])
        if self.is_it_move_from_history:
            self.messenger.objects_run_from_file_simulation()
        else:
            self.messenger.objects_run_simulation()
        self.messenger.ai_start_game()

        @self.game_window.event
        def on_draw():
            if self.game_state != GameState.Pause:
                self.fps_display.draw()

        @self.game_window.event
        def on_key_press(key, modif):
            self.messenger.controls_handle_key(True, key)

        @self.game_window.event
        def on_key_release(key, modif):
            self.messenger.controls_handle_key(False, key)

        @self.game_window.event
        def on_close():
            self.quit()

        # we need to remember about hard nailed graphics. much later we should fix it somehow
        pyglet.clock.schedule_interval(self.read_messages, 1.0 / 60.0)
        pyglet.clock.schedule_interval(self.update_graphics, 1.0 / 60.0)
        pyglet.app.run()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--file", type=str, required=False,
                    help="path to history file")
    args = vars(ap.parse_args())
    if 'file' in args:
        game = Game(1000, 1000, args['file'])
    else:
        game = Game(1000, 1000)
    game.run_game()
