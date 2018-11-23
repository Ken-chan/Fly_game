import pyglet, json
from view import Renderer
import messages
from messages import Messenger
import argparse
import datetime
import time
from gui_controls import GUIcontrols
from ai_controls import AIcontrols
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
            #self.history_path = now_time.strftime("history")+'.txt' #wtf is this. you didn't even look what does it mean
            self.history_path = 'history.txt'
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
        self.configuration[ObjectType.Player1].append((500, 50, 90, ObjectSubtype.Plane, Constants.DefaultObjectRadius))
        # configuration[ObjectType.Player2].append((500, 450))
        self.configuration[ObjectType.Player2].append(
            (500, 950, 270, ObjectSubtype.Helicopter, Constants.DefaultObjectRadius))

        self.messenger = Messenger()
        self.Objects = Objects(self.messenger, self.configuration, history_path=self.history_path)
        self.ai_controls = AIcontrols(self.messenger)
        self.gui_controls = GUIcontrols(self.messenger)

        self.renderer = Renderer(self.screen_width, self.screen_height)

        self.Objects.start()
        self.ai_controls.start()
        self.gui_controls.start()

        self.objects = None
        self.history_list = []
        self.functions = {messages.Game.Quit: self.quit,
                          messages.Game.UpdateObjects: self.update_objects,
                          messages.Game.Pause: self.game_pause_simulation,
                          messages.Game.ActiveGame: self.game_unpaused}

    # /Part of working with log files starts

    def clear_file(self, file_path):
        with open(file_path, "w") as file:  # just to open with argument which clean file
            pass

    # /Part of working with log files ends
    def quit(self):
        self.game_state = GameState.Exit
        self.messenger.shutdown()
        self.Objects.join()
        self.gui_controls.join()
        self.ai_controls.join()
        pyglet.app.exit()

    def game_pause_simulation(self):
        self.game_state = GameState.Pause

    def game_unpaused(self):
        self.game_state = GameState.ActiveGame

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

            # saving movement
            # self.save_history_file_txt("history.txt", objects_copy[1][ObjectProp.Xcoord], objects_copy[1][ObjectProp.Ycoord], objects_copy[1][ObjectProp.Dir])
            #string_object = ''
            #for index in range(0, ObjectType.ObjArrayTotal):
            #    if objects_copy[index][ObjectProp.ObjType] != ObjectType.Absent:
            #        for i in range(0 , len(objects_copy[index])):
            #            string_object += str(objects_copy[index][i]) + ' ' #make string of properies of every object(not absent)
            #string_object += '\n'
            #self.save_history_file_txt("history.txt", string_object)

    def run_game(self):
        #Save movement
        #print("previous history file was deleted", '\n', "Creating new file...")

        self.game_window = pyglet.window.Window(self.screen_width, self.screen_height)
        pyglet.gl.glClearColor(0.6, 0.6, 0.6, 0)
        self.game_window.set_location(200, 50)
        # later we should make configuration loader from config file

        self.game_state = GameState.ActiveGame
        self.renderer.set_battle_field_size(self.battle_field_size[0], self.battle_field_size[1])
        if self.is_it_move_from_history:
            self.messenger.objects_run_from_file_simulation()
        else:
            self.messenger.objects_run_simulation()
        self.messenger.objects_set_game_settings(self.configuration)
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
        game = Game(800,600, args['file'])
    else:
        game = Game(800, 600)
    game.run_game()
