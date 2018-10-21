#initialize the screen
import pyglet
from bot import Bot
from player import Player
from pyglet.window import key
from messages import Messenger
import messages
from controller import GUIcontrols
import sys

class GameState:
    Start, ActiveGame, Menu, Exit = range(4)

class Game:
    def __init__(self, screen_width, screen_height):
        self.game_state = GameState.Start
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.messenger = Messenger()
        self.player = Player(100, 100)
        self.bot = Bot(500, 800)
        self.gui_controls = GUIcontrols(self.messenger, screen_width, screen_height)
        self.gui_controls.start()

        self.functions = {messages.Game.Quit: self.quit,
                          messages.Objects.PlayerSetDirection: self.update_player}


    def quit(self):
        self.game_state = GameState.Exit
        self.messenger.shutdown()
        self.gui_controls.join()
        pyglet.app.exit()

    def read_messages(self, dt):
        while True:
            data = self.messenger.get_message(messages.Game)
            if not data:
                data = self.messenger.get_message(messages.Objects)
                if not data:
                    return

            self.functions[data['func']](**data['args']) if 'args' in data else self.functions[data['func']]()

    def update_player(self, delta_speed, delta_angle):
        self.player.speed += delta_speed
        self.player.direction += delta_angle

    def run_game(self):
        self.game_window = pyglet.window.Window(self.screen_width, self.screen_height)
        pyglet.gl.glClearColor(0, 0, 1, 1)

        self.game_state = GameState.ActiveGame


        def update(dt):
            self.bot.update(dt)
            self.player.update(dt)


        """@self.game_window.event
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

        @self.game_window.event
        def on_key_release(symbol, modifiers):
            if symbol == key.RIGHT:
                player.k_right = 0
            elif symbol == key.LEFT:
                player.k_left = 0
            elif symbol == key.DOWN:
                player.k_down = 0
            elif symbol == key.UP:
                player.k_up = 0"""

        @self.game_window.event
        def on_key_press(key, modif):
            self.messenger.controls_handle_key(True, key)

        @self.game_window.event
        def on_key_release(key, modif):
            self.messenger.controls_handle_key(False, key)

        @self.game_window.event
        def on_draw():
            self.game_window.clear()
            self.bot.Bot_sprite.draw()
            self.player.Player_sprite.draw()

        @self.game_window.event
        def on_close():
            self.quit()

        pyglet.clock.schedule_interval(update, 1.0 / 30)
        pyglet.clock.schedule_interval(self.read_messages, 1/30.0)
        pyglet.app.run()




game = Game(1024,768)
game.run_game()










