from multiprocessing import Process
import messages
from pyglet.window import key as pygletkey


class GUIcontrolsState:
    Start, InGame, Exit = range(3)


class GUIcontrols(Process):
    def __init__(self, messenger):
        super(GUIcontrols, self).__init__()
        self.gui_state = GUIcontrolsState.InGame
        self.messenger = messenger

        self.player_direction_x = 0
        self.player_direction_y = 0
        self.cycles = 0
        self.kb_control = KbControl(1, self.messenger)
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
    def __init__(self, player, messenger):
        self.messenger = messenger
        self.x_ratio = None
        self.y_ratio = None
        self.player = player

class KbControl(BaseControl):
    def __init__(self, player, messenger):
        super(KbControl, self).__init__(player, messenger)

    def dispatch_kb_event(self, pushed, key):
        if key in (pygletkey.UP, pygletkey.DOWN, pygletkey.RIGHT, pygletkey.LEFT):
            self.change_player1_direction(pushed, key)
        elif key in (pygletkey.W, pygletkey.D, pygletkey.A, pygletkey.S):
            self.change_player2_direction(pushed, key)

    def change_player1_direction(self, pushed, key):
        self.messenger.player1_set_pressed_key(pushed, key)

    def change_player2_direction(self, pushed, key):
        self.messenger.player2_set_pressed_key(pushed, key)

