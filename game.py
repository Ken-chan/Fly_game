import pyglet, json
from multiprocessing import Queue
from view import Renderer
from messages import Messenger
import time
from gui_controls import GUIcontrols
from ai_controls import AIcontrols
from objects import Objects
from obj_def import *

class GameState:
    Start, ActiveGame, Menu, Exit, Pause = range(5)


class Game:
    def __init__(self, screen_width, screen_height):
        super(Game, self).__init__()
        self.game_state = GameState.Start
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.fps_display = pyglet.clock.ClockDisplay()
        self.command_queue = Queue()

        self.messenger = Messenger()
        self.Objects = Objects(self.messenger)
        self.ai_controls = AIcontrols(self.messenger)
        self.gui_controls = GUIcontrols(self.messenger)

        #self.Objects.link_objects(self.ai_controls, self)
        #self.ai_controls.link_objects(self.Objects)
        #self.gui_controls.link_objects(self.Objects, self)

        self.renderer = Renderer(self.screen_width, self.screen_height)

        self.Objects.start()
        self.ai_controls.start()
        self.gui_controls.start()

        self.objects = None
        self.history_list = []
        self.is_it_move_from_history = False

        self.functions = {'quit': self.quit,
                          'update_objects': self.update_objects,
                          'pause': self.game_pause_simulation,
                          'unpause': self.game_unpaused}

    # /Part of working with log files starts

    def clear_file(self, file):
        with open(file, "w") as file:  # just to open with argument which clean file
            pass

    def save_history_file_txt(self, file, str):
        with open(file, 'a') as f:
            f.write(str + ' ')

    def save_history_json(self, history_file, objects_data):
        with open(history_file, 'a', encoding="utf-8") as file:
            json.dump(objects_data, file)
            file.write('\n')

    # /Part of working with log files ends
    def quit(self, asynced=False):
        if asynced:
            self.messenger.send_message(self.command_queue, 'quit')
            return
        self.game_state = GameState.Exit
        self.Objects.quit(asynced=True)
        self.gui_controls.stop_gui(asynced=True)
        self.ai_controls.stop_ai(asynced=True)
        self.command_queue.close()
        while True:
            data = self.messenger.get_message(self.command_queue)
            if not data:
                break
        for t in range(0, 2):
            print("waiting for queues: {}".format(t))
            time.sleep(0.1)

        self.Objects.join()
        self.gui_controls.join()
        self.ai_controls.join()
        pyglet.app.exit()

    def game_pause_simulation(self, asynced=False):
        if asynced:
            self.messenger.send_message(self.command_queue, 'pause')
            return
        self.game_state = GameState.Pause

    def game_unpaused(self, asynced=False):
        if asynced:
            self.messenger.send_message(self.command_queue, 'unpause')
            return
        self.game_state = GameState.ActiveGame

    def read_messages(self, dt):
        while True:
            data = self.messenger.get_message(self.command_queue)
            if not data:
                return
            self.functions[data['func']](**data['args']) if 'args' in data else self.functions[data['func']]()

    def update_graphics(self, dt):
        if self.game_state != GameState.Pause:
            self.renderer.update_graphics()
            self.game_window.clear()
            self.renderer.batch.draw()

    def update_objects(self, objects_copy, asynced=False):
        if asynced:
            self.messenger.send_message(self.command_queue, 'update_objects', {'objects_copy': objects_copy})
            return
        if self.game_state != GameState.Pause:
            self.objects = objects_copy
            self.renderer.update_objects(objects_copy)
            self.renderer.update_graphics()

            # saving movement
            # self.save_history_file_txt("history.txt", objects_copy[1][ObjectProp.Xcoord], objects_copy[1][ObjectProp.Ycoord], objects_copy[1][ObjectProp.Dir])
            string_object = ''
            for index in range(0, ObjectType.ObjArrayTotal):
                if objects_copy[index][ObjectProp.ObjType] != ObjectType.Absent:
                    for i in range(0 , len(objects_copy[index])):
                        string_object += str(objects_copy[index][i]) + ' ' #make string of properies of every object(not absent)
            string_object += '\n'
            self.save_history_file_txt("history.txt", string_object)
        # no need to update graphics on every objects refreshment event
        # we sheduled it on 1/30 s. right?

    def run_game(self):
        #Save movement
        #print("previous history file was deleted", '\n', "Creating new file...")
        self.clear_file("history.txt")
        self.is_it_move_from_history = False

        self.game_window = pyglet.window.Window(self.screen_width, self.screen_height)
        pyglet.gl.glClearColor(0.6, 0.6, 0.6, 0)
        self.game_window.set_location(200, 50)
        battle_field_size = (1000,1000)
        # later we should make configuration loader from config file
        configuration = {ObjectType.FieldSize: [],
                         ObjectType.Bot1: [],
                         ObjectType.Player1: [],
                         ObjectType.Bot2: [],
                         ObjectType.Player2: []}
        configuration[ObjectType.FieldSize].append(battle_field_size)
        configuration[ObjectType.Player1].append((500, 50, 15))
        #configuration[ObjectType.Player2].append((500, 450))
        configuration[ObjectType.Bot2].append((500, 450, 15))

        self.game_state = GameState.ActiveGame
        self.renderer.set_battle_fiel_size(battle_field_size[0],battle_field_size[1])
        if self.is_it_move_from_history:
            self.Objects.run_history(asynced=True)
        else:
            self.Objects.run_simulation(asynced=True)
        self.Objects.update_game_settings(configuration, asynced=True)
        self.ai_controls.start_ai_controls(asynced=True)

        @self.game_window.event
        def on_draw():
            if self.game_state != GameState.Pause:
                self.fps_display.draw()

        @self.game_window.event
        def on_key_press(key, modif):
            self.gui_controls.handle_kb_event(True, key, asynced=True)

        @self.game_window.event
        def on_key_release(key, modif):
            self.gui_controls.handle_kb_event(False, key, asynced=True)

        @self.game_window.event
        def on_close():
            self.quit()

        # we need to remember about hard nailed graphics. much later we should fix it somehow
        pyglet.clock.schedule_interval(self.read_messages, 1.0 / 60.0)
        pyglet.clock.schedule_interval(self.update_graphics, 1.0 / 60.0)
        pyglet.app.run()


if __name__ == "__main__":
    game = Game(800, 600)
    game.run_game()
