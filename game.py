import pyglet, json
from view import Renderer
from messages import Messenger
import messages
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
        self.messenger = Messenger()
        self.renderer = Renderer(self.screen_width, self.screen_height)
        self.gui_controls = GUIcontrols(self.messenger)
        self.gui_controls.start()
        self.ai_controls = AIcontrols(self.messenger)
        self.ai_controls.start()

        self.Objects = Objects(messenger=self.messenger)
        self.Objects.start()
        self.objects = None

        self.functions = {messages.Game.Quit: self.quit,
                          messages.Game.UpdateObjects: self.update_objects,
                          messages.Game.Pause: self.game_pause_simulation,
                          messages.Game.ActiveGame: self.game_unpaused}

    # /Part of working with log files starts

    def clear_file(self, file):
        with open(file, "w") as file:  # just to open with argument which clean file
            pass

    def save_history_file_txt(self, file, coordx, coordy, angle):
        with open(file, 'a') as f:
            f.write(str(int(coordx)) + '  ')
            f.write(str(int(coordy)) + ' ')
            f.write(str(angle) + '\n')

    def save_history_json(self, history_file, objects_data):
        with open(history_file, 'a', encoding="utf-8") as file:
            json.dump(objects_data, file)
            file.write('\n')

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
            for index in range(0, ObjectType.ObjArrayTotal):
                if objects_copy[index][ObjectProp.ObjType] != ObjectType.Absent:
                    data = {'ObjectID': objects_copy[index][ObjectProp.ObjId],
                            'X_coord':  objects_copy[index][ObjectProp.Xcoord],
                            'y_coord':  objects_copy[index][ObjectProp.Ycoord],
                            'Direction':objects_copy[index][ObjectProp.Dir]
                            }
                    self.save_history_json("history.txt", data)
        # no need to update graphics on every objects refreshment event
        # we sheduled it on 1/30 s. right?

    def run_game(self):
        #Save movement
        print("previous history file was deleted", '\n', "Creating new file...")
        self.clear_file("history.txt")

        self.game_window = pyglet.window.Window(self.screen_width, self.screen_height)
        pyglet.gl.glClearColor(0.6, 0.6, 0.6, 0)
        self.game_window.set_location(400, 150)
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
        self.messenger.objects_run_simulation()
        self.messenger.objects_set_game_settings(configuration)
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
    game = Game(1024, 768)
    game.run_game()
