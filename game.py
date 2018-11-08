import pyglet
from view import Renderer
from messages import Messenger
import messages
from gui_controls import GUIcontrols
from ai_controls import AIcontrols
from objects import Objects
from obj_def import *

class GameState:
    Start, ActiveGame, Menu, Exit = range(4)


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
                          messages.Game.UpdateObjects: self.update_objects}

    def quit(self):
        self.game_state = GameState.Exit
        self.messenger.shutdown()
        self.Objects.join()
        self.gui_controls.join()
        self.ai_controls.join()
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
        pyglet.gl.glClearColor(1, 1, 1, 0)
        battle_field_size = (1000,1000)
        # later we should make configuration loader from config file
        configuration = {ObjectType.FieldSize: [],
                         ObjectType.Bot1: [],
                         ObjectType.Player1: [],
                         ObjectType.Bot2: [],
                         ObjectType.Player2: []}
        configuration[ObjectType.FieldSize].append(battle_field_size)
        configuration[ObjectType.Player1].append((500, 50))
        configuration[ObjectType.Player2].append((500, 450))
        #configuration[ObjectType.Bot2].append((5000, 4500))

        self.game_state = GameState.ActiveGame
        self.renderer.set_battle_fiel_size(battle_field_size[0],battle_field_size[1])
        self.messenger.objects_run_simulation()
        self.messenger.objects_set_game_settings(configuration)
        self.messenger.ai_start_game()

        @self.game_window.event
        def on_draw():
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
        pyglet.clock.schedule_interval(self.read_messages, 1.0 / 30.0)
        pyglet.clock.schedule_interval(self.update_graphics, 1.0 / 30.0)
        pyglet.app.run()


if __name__ == "__main__":
    game = Game(1000, 1000)
    game.run_game()
