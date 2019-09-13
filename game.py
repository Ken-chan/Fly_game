import pyglet
from multiprocessing import Pool
from multiprocessing import Process
from view import Renderer
from messages import Messenger
from gui_controls import GUIcontrols
from ai_controls import AIcontrols, AItype
import messages
import argparse
import datetime
from objects import Objects
from obj_def import *
from tools import Helper
import gc
import cProfile



def profiler(func):
    """Decorator for run function profile"""
    def wrapper(*args, **kwargs):
        profile_filename = func.__name__ + '.prof'
        profiler = cProfile.Profile()
        result = profiler.runcall(func, *args, **kwargs)
        profiler.dump_stats(profile_filename)
        return result
    ### write it in console to get profile
    # import pstats
    # p = pstats.Stats('run_game.prof')
    # p.sort_stats('tottime').print_stats() #'calls' and etc
    return wrapper

class GameState:
    Start, ActiveGame, Menu, Exit, Pause = range(5)

class Game:
    def __init__(self, screen_width, screen_height, history_path=None, train_mode=False, prefix=None, tries=1,
                 cube=None, alies_cube=None, queue_res=None, params=None, team_strategy=None):
        gc.disable()
        self.game_state = GameState.Start
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.train_mode = train_mode

        self.cube = cube
        self.alies_cube = alies_cube
        self.queue_res = queue_res
        self.params = params
        self.team_strategy = team_strategy

        self.battle_field_size = (1000, 1000)
        self.radiant_bots = 0
        self.dire_bots = 1
        self.is_player1_play = True
        self.is_player2_play = False
        self.radiant = self.radiant_bots + self.is_player1_play
        self.dire = self.dire_bots + self.is_player2_play
        self.is_it_move_from_history = False
        if history_path is None:
            now_time = datetime.datetime.now()
            self.history_path = now_time.strftime("%Y_%m_%d_%H_%M_%S")+'.txt'
            #self.history_path = 'delete_me_pls.txt'
            #if prefix:
            #    self.history_path = '{}_{}'.format(prefix, self.history_path)
            #    self.clear_file(self.history_path)
            #    self.is_it_move_from_history = False
        else:
            self.history_path = history_path
            self.is_it_move_from_history = True
        # self.fps_display = pyglet.clock.ClockDisplay()
        self.playtime = 0
        self.framerate = 60
        self.configuration = {ObjectType.FieldSize: [],
                              ObjectType.Bot1: [],
                              ObjectType.Player1: [],
                              ObjectType.Bot2: [],
                              ObjectType.Player2: []}
        self.configuration[ObjectType.FieldSize].append(self.battle_field_size)
        self.prepare_config(self.radiant_bots, self.dire_bots, self.is_player1_play, self.is_player2_play,
                            self.battle_field_size[0], self.battle_field_size[1])
        self.messenger = Messenger()
        if self.train_mode:
            self.ai_controls = AIcontrols(self.configuration, messenger=self.messenger, train_mode=True, cube=self.cube, alies_cube=self.alies_cube,
                                          params=self.params, team_strategy=self.team_strategy)
            self.Objects = Objects(self.configuration, self.radiant, self.dire, history_path=self.history_path,
                                   messenger=self.messenger, ai_controls=self.ai_controls, tries=tries,
                                   bot1=self.radiant_bots, bot2=self.dire_bots, player1=self.is_player1_play,
                                   player2=self.is_player2_play, sizeX=self.battle_field_size[0], sizeY=self.battle_field_size[1],
                                   queue_res=self.queue_res)
        else:
            self.ai_controls = AIcontrols(self.configuration, messenger=self.messenger, cube=self.cube, alies_cube=self.alies_cube, team_strategy=self.team_strategy)
            self.Objects = Objects(self.configuration, self.radiant, self.dire, history_path=self.history_path,
                                   messenger=self.messenger)
            self.renderer = Renderer(self.screen_width, self.screen_height, self.battle_field_size)
            self.gui_controls = GUIcontrols(self.messenger)
        self.game_window = None
        self.objects = None
        self.history_list = []
        self.functions = {messages.Game.Quit: self.quit,
                          messages.Game.UpdateObjects: self.update_objects,
                          messages.Game.Pause: self.game_pause_simulation,
                          messages.Game.Polar_grid: self.show_polar_grid,
                          messages.Game.Message_clouds: self.show_message_clouds,
                          messages.Game.ActiveGame: self.game_unpaused}

        self.run_game()

    def prepare_config(self, bot1, bot2, player1, player2, sizeX, sizeY):
        pos1 = sizeX / (bot1 + player1 + 1)
        delta_y = 75
        pos2 = sizeX / (bot2 + player2 + 1)
        if player1:
            self.configuration[ObjectType.Player1].append((pos1, delta_y,
                                                       90, ObjectSubtype.Plane, Constants.DefaultObjectRadius))
        if player2:
            self.configuration[ObjectType.Player2].append((pos2, sizeY - delta_y,
                                                       270, ObjectSubtype.Plane, Constants.DefaultObjectRadius))

        for i in range(1, bot1 + 1):
            self.configuration[ObjectType.Bot1].append((pos1 * (i + player1), delta_y,
                 90, ObjectSubtype.Plane, Constants.DefaultObjectRadius, AItype.GreedAi))

        for i in range(1, bot2 + 1):
            self.configuration[ObjectType.Bot2].append((pos2 * (i + player2), sizeY - delta_y,
                 270, ObjectSubtype.Plane, Constants.DefaultObjectRadius, AItype.DumbAi))


    def clear_file(self, file_path):
        with open(file_path, "w") as file:  # just to open with argument which clean file
            pass

    def quit(self):
        self.game_state = GameState.Exit
        self.messenger.shutdown()
        pyglet.app.exit()

    def game_pause_simulation(self):
        self.game_state = GameState.Pause

    def game_unpaused(self):
        self.game_state = GameState.ActiveGame

    def show_polar_grid(self):
        if(self.game_window.width ==  self.screen_width):
            self.game_window.set_size(self.screen_width + 500, self.screen_height)
            self.renderer.show_polar_grid()
        else:
            self.game_window.set_size(self.screen_width, self.screen_height)
            self.renderer.show_polar_grid()

    def show_message_clouds(self):
        self.renderer.show_message_clouds()

    def read_messages(self, dt):
        while True:
            data = self.messenger.get_message(messages.Game)
            if not data:
                return
            self.functions[data['func']](**data['args']) if 'args' in data else self.functions[data['func']]()

    def update_graphics(self, dt):
        if self.game_state != GameState.Pause:
            self.renderer.update_graphics()
            #self.game_window.clear()
            #self.renderer.batch.draw()

    def update_objects(self, objects_copy):
        if self.game_state != GameState.Pause:
            self.objects = objects_copy
            self.renderer.update_objects(objects_copy)
            self.renderer.update_graphics()

    #@profiler
    def run_game(self):
        if self.train_mode:
            pyglet.clock.schedule_interval(self.read_messages, 1.0 / 2)
            pyglet.app.run()
            return 0
        if self.team_strategy:
            if self.team_strategy == TeamInteractions.Dynamical_choose:
                print('-> Now strategy of red team is: Dynamical choose of target ')
            elif self.team_strategy == TeamInteractions.All_for_one:
                print('-> Now strategy of red team is: All team attack one target ')
            elif self.team_strategy == TeamInteractions.OneGoal_oneTarget:
                print('-> Now strategy of red team is: Static choose of target ')
        self.game_window = pyglet.window.Window(self.screen_width, self.screen_height, resizable=True)
        pyglet.gl.glClearColor(0.9, 0.9, 0.9, 0)
        self.game_window.set_location(350, 35)
        self.game_state = GameState.ActiveGame
        if self.is_it_move_from_history:
            self.messenger.objects_run_from_file_simulation()
        else:
            self.messenger.objects_run_simulation()
        self.messenger.ai_start_game()

        @self.game_window.event
        def on_draw():
            self.game_window.clear()
            self.renderer.batch.draw()

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
        pyglet.clock.schedule_interval(self.read_messages, 1.0 / self.framerate)
        pyglet.clock.schedule_interval(self.update_graphics, 1.0 / self.framerate)
        pyglet.app.run()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--history_path", type=str, required=False,
                    help="path to history file")
    ap.add_argument("-t", "--train_mode", required=False, action='store_true',
                    help="training mode")
    ap.add_argument("-p", '--prefix', type=str, required=False,
                    help='prefix for history file')
    #ap.add_argument("-m", '--tries', type=int, required=False,
    #                help='number of total retries in one session')
    args = vars(ap.parse_args())
    args["screen_width"] = 1000
    args["screen_height"] = 1000
    print("{}".format(args))

    Game(**args, team_strategy=TeamInteractions.Dynamical_choose)