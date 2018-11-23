import messages
from multiprocessing import Process
from pyglet.window import key as pygletkey
from obj_def import ObjectType, ObjectProp


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
                self.messenger.game_pause()
            else:
                self.messenger.game_unpause()
            self.game_is_paused = not self.game_is_paused
        elif key == pygletkey.R and pushed:
            self.messenger.restart_game()

    def change_player_control(self, team, pushed, key):
        vel, turn = self.player_controls[team]
        new_vel, new_turn = None, None
        if key in (pygletkey.UP, pygletkey.W):
            new_vel = vel+1 if pushed else vel-1
        if key in (pygletkey.DOWN, pygletkey.S):
            new_vel = vel-1 if pushed else vel+1
        if key in (pygletkey.D, pygletkey.RIGHT):
            new_turn = turn-1 if pushed else turn+1
        if key in (pygletkey.A, pygletkey.LEFT):
            new_turn = turn+1 if pushed else turn-1
        if new_turn is not None and new_turn != turn:
            self.messenger.objects_set_control_signal(ObjectType.offset(team)[0], ObjectProp.TurnControl, new_turn)
            self.player_controls[team][1] = new_turn
        if new_vel is not None and new_vel != vel:
            self.messenger.objects_set_control_signal(ObjectType.offset(team)[0], ObjectProp.VelControl, new_vel)
            self.player_controls[team][0] = new_vel
