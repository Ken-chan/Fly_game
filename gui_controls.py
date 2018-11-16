from multiprocessing import Process
from pyglet.window import key as pygletkey


class GUIcontrolsState:
    Start, InGame, Exit = range(3)


class GUIcontrols(Process):
    def __init__(self, messenger, queue):
        super(GUIcontrols, self).__init__()
        self.gui_state = GUIcontrolsState.InGame
        self.messenger = messenger
        self.game = None
        self.command_queue = queue
        self.queue_open = True
        self.objects = None

        self.player_direction_x = 0
        self.player_direction_y = 0
        self.cycles = 0
        self.kb_control = KbControl(1, self.messenger)
        self.gui_state = GUIcontrolsState.InGame
        self.functions = {'quit': self.stop_gui,
                          'start': self.start_game,
                          'handle_kb_event': self.handle_kb_event}

    def link_objects(self, objects, game):
        self.game = game
        self.objects = objects
        self.kb_control.link_objects(objects, game)

    def run(self):
        while self.gui_state != GUIcontrolsState.Exit:
            while True:
                data = self.messenger.get_message(self.command_queue)
                if not data:
                    break
                self.functions[data['func']](**data['args']) if 'args' in data else self.functions[data['func']]()

    def start_game(self, asynced=False):
        if asynced:
            if self.queue_open:
                self.messenger.send_message(self.command_queue, 'start')
            return
        self.gui_state = GUIcontrolsState.InGame

    def stop_gui(self, asynced=False):
        if asynced:
            if self.queue_open:
                self.messenger.send_message(self.command_queue, 'quit')
            return
        print("terminating controls")
        self.gui_state = GUIcontrolsState.Exit
        self.queue_open = False
        while True:
            data = self.messenger.get_message(self.command_queue)
            if not data:
                break

    def handle_kb_event(self, pushed, key, asynced=False):
        print("handle kb: {}, {}, {}".format(pushed,key,asynced))
        if asynced:
            if self.queue_open:
                self.messenger.send_message(self.command_queue, 'handle_kb_event', {'pushed': pushed, 'key': key})
        if self.gui_state == GUIcontrolsState.InGame:
            self.kb_control.dispatch_kb_event(pushed, key)


class BaseControl:
    def __init__(self, player, messenger):
        self.messenger = messenger
        self.game = None
        self.objects = None
        self.x_ratio = None
        self.y_ratio = None
        self.player = player
        self.game_is_paused = False


class KbControl(BaseControl):
    def __init__(self, player, messenger):
        super(KbControl, self).__init__(player, messenger)

    def link_objects(self, objects, game):
        self.game = game
        self.objects = objects

    def dispatch_kb_event(self, pushed, key):
        if key in (pygletkey.UP, pygletkey.DOWN, pygletkey.RIGHT, pygletkey.LEFT):
            self.change_player1_direction(pushed, key)
        elif key in (pygletkey.W, pygletkey.D, pygletkey.A, pygletkey.S):
            self.change_player2_direction(pushed, key)
        elif key == pygletkey.P and pushed:
            if not self.game_is_paused:
                self.game.game_pause_simulation(asynced=True)
            else:
                self.game.game_unpaused(asynced=True)
            self.game_is_paused = not self.game_is_paused

    def change_player1_direction(self, pushed, key):
        self.objects.set_pressed_key1(pushed, key, asynced=True)

    def change_player2_direction(self, pushed, key):
        self.objects.set_pressed_key2(pushed, key, asynced=True)

