from multiprocessing import Process
import messages
from pyglet.window import key as pygletkey


class GUIcontrolsState:
    Start, InGame, Exit = range(3)


class GUIcontrols(Process):
    def __init__(self, messenger, screen_width, screen_height):
        super(GUIcontrols, self).__init__()
        self.gui_state = GUIcontrolsState.InGame
        self.messenger = messenger
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.player_direction_x = 0
        self.player_direction_y = 0
        self.cycles = 0
        self.kb_control = KbControl(1, screen_width, screen_height, self.messenger)
        self.gui_state = GUIcontrolsState.InGame
        self.functions = {messages.GuiControls.StopGui: self.stop_gui,
                          messages.GuiControls.StartGame: self.start_game,
                          messages.GuiControls.HandleKey: self.handle_kb_event}

    def run(self):
        while self.gui_state != GUIcontrolsState.Exit:
            while True:
                data = self.messenger.get_message(messages.GuiControls)
                if not data:
                    break
                self.functions[data['func']](**data['args']) if 'args' in data else self.functions[data['func']]()


    def start_game(self):
        self.gui_state = GUIcontrolsState.InGame

    def stop_gui(self):
        print("terminating controls")
        self.gui_state = GUIcontrolsState.Exit

    def handle_kb_event(self, pushed, key):
        if self.gui_state == GUIcontrolsState.InGame:
            self.kb_control.dispatch_kb_event(pushed, key)


class BaseControl:
    def __init__(self, player, screen_width, screen_height, messenger):
        self.messenger = messenger
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x_ratio = None
        self.y_ratio = None
        self.player = player

class KbControl(BaseControl):
    def __init__(self, player, screen_width, screen_height, messenger):
        super(KbControl, self).__init__(player, screen_width, screen_height, messenger)

    def dispatch_kb_event(self, pushed, key):
        if key in (pygletkey.UP, pygletkey.DOWN, pygletkey.RIGHT, pygletkey.LEFT):
            self.recalc_player_direction(pushed, key)

    def recalc_player_direction(self, pushed, key):
        delta_speed = 0
        delta_angle = 0
        if pushed:
            if key == pygletkey.UP:
                delta_speed = 50
            elif key == pygletkey.DOWN:
                delta_speed = -50
            elif key == pygletkey.RIGHT:
                delta_angle = 20
            elif key == pygletkey.LEFT:
                delta_angle = -20
        self.change_player_direction(delta_speed, delta_angle)


    def change_player_direction(self, delta_speed, delta_angle):
        self.messenger.player_set_direction(delta_speed, delta_angle)

