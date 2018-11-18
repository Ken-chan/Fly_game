from multiprocessing import Process, Queue
from pyglet.window import key as pygletkey
from obj_def import ObjectType, ObjectProp


class GUIcontrolsState:
    Start, InGame, Exit = range(3)


class GUIcontrols(Process):
    def __init__(self, messenger):
        super(GUIcontrols, self).__init__()
        self.gui_state = GUIcontrolsState.InGame
        self.messenger = messenger
        self.game = None
        self.command_queue = Queue()
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
            self.messenger.send_message(self.command_queue, 'start')
            return
        self.gui_state = GUIcontrolsState.InGame

    def stop_gui(self, asynced=False):
        if asynced:
            self.messenger.send_message(self.command_queue, 'quit')
            return
        print("terminating controls")
        self.gui_state = GUIcontrolsState.Exit
        self.command_queue.close()
        while True:
            data = self.messenger.get_message(self.command_queue)
            if not data:
                break

    def handle_kb_event(self, pushed, key, asynced=False):
        if asynced:
            self.messenger.send_message(self.command_queue, 'handle_kb_event', {'pushed': pushed, 'key': key})
            return
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
        self.player_controls = {ObjectType.Player1: [0, 0],
                                ObjectType.Player2: [0, 0]}
        self.key_bind = {}

    def link_objects(self, objects, game):
        self.game = game
        self.objects = objects

    def dispatch_kb_event(self, pushed, key):
        if key in (pygletkey.UP, pygletkey.DOWN, pygletkey.RIGHT, pygletkey.LEFT):
            self.change_player_control(ObjectType.Player1, pushed, key)
        elif key in (pygletkey.W, pygletkey.D, pygletkey.A, pygletkey.S):
            self.change_player_control(ObjectType.Player2, pushed, key)
        elif key == pygletkey.P and pushed:
            if not self.game_is_paused:
                self.game.game_pause_simulation(asynced=True)
            else:
                self.game.game_unpaused(asynced=True)
            self.game_is_paused = not self.game_is_paused

    def change_player_control(self, team, pushed, key):
        vel, turn = self.player_controls[team]
        new_vel, new_turn = None, None
        if key in (pygletkey.UP, pygletkey.W):
            new_vel = vel+1 if pushed else vel-1
        if key in (pygletkey.DOWN, pygletkey.S):
            new_vel = vel-1 if pushed else vel+1
        if key in (pygletkey.D, pygletkey.RIGHT):
            new_turn = turn+1 if pushed else turn-1
        if key in (pygletkey.A, pygletkey.LEFT):
            new_turn = turn-1 if pushed else turn+1
        if new_turn is not None and new_turn != turn:
            self.objects.set_control_signal(ObjectType.offset(team)[0], ObjectProp.TurnControl, new_turn, asynced=True)
            self.player_controls[team][1] = new_turn
        if new_vel is not None and new_vel != vel:
            self.objects.set_control_signal(ObjectType.offset(team)[0], ObjectProp.VelControl, new_vel, asynced=True)
            self.player_controls[team][0] = new_vel
