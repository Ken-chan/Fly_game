from multiprocessing import Queue
import time

class Game:
    Quit, UpdateField, UpdateObjects, RunNewGame = range(4)
class GuiControls:
    StopGui, StartGame, UpdateField, UpdateObjects, HandleMouse, HandleKey = range(6)
class GuiScreen:
    TerminateScreen, StartNewGame, UpdateRenderedSurface = range(3)
class Objects:
    Quit, UpdateField, AddObject, KingSetDestination, Player1SetPressedKey, Player2SetPressedKey, \
    KingChangeItem, Pause, Run, UpdateGameSettings, TrainUnit, BuyItem, UseItem, UpdateObjects = range(14)


class Messenger:
    def __init__(self):
        self.gui_screen_queue = Queue()
        self.game_queue = Queue()
        self.gui_controls_queue = Queue()
        self.objects_queue = Queue()
        self.writable = True
        self.binding = {GuiScreen:  self.gui_screen_queue,
                        Game: self.game_queue,
                        Objects: self.objects_queue,
                        GuiControls: self.gui_controls_queue}

    def send_message(self, queue, func, args=None):
        if not self.writable:
            return
        mess = {'func': func}
        if args:
            mess['args'] = args
        try:
            queue.put(mess)
        except Exception as e:
            print("send excetion: {}".format(e))
            pass

    def get_message(self, obj_type):
        try:
            data = self.binding[obj_type].get(False)
            return data
        except Exception as e:
            return None

    def game_quit(self):
        self.send_message(self.game_queue, Game.Quit)

    #def player_pressed_key(self, pressed, key):
     #   self.send_message(self.objects_queue, Objects.PlayerPressedKey, {'pressed': pressed, 'key': key})

    def screen_terminate(self):
        self.send_message(self.gui_screen_queue, GuiScreen.TerminateScreen)

    def controls_handle_key(self, pushed, key):
        self.send_message(self.gui_controls_queue, GuiControls.HandleKey, {'pushed': pushed, 'key': key})

    def controls_terminate(self):
        self.send_message(self.gui_controls_queue, GuiControls.StopGui)

    def controls_start_game(self):
        self.send_message(self.gui_controls_queue, GuiControls.StartGame)

    def player1_set_pressed_key(self, pushed, key):
        self.send_message(self.objects_queue, Objects.Player1SetPressedKey, {'pushed': pushed, 'key': key})

    def player2_set_pressed_key(self, pushed, key):
        self.send_message(self.objects_queue, Objects.Player2SetPressedKey, {'pushed': pushed, 'key': key})

    def objects_set_game_settings(self, configuration):
        self.send_message(self.objects_queue, Objects.UpdateGameSettings, {'configuration': configuration})

    def objects_run_simulation(self):
        self.send_message(self.objects_queue, Objects.Run)

    def game_update_objects(self, objects_copy):
        self.send_message(self.game_queue, Game.UpdateObjects, {'objects_copy': objects_copy})

    def shutdown(self):
        print("terminate controls")
        self.controls_terminate()
        print("terminate screen")
        self.screen_terminate()

        self.writable = False
        #make sure threads ended
        for t in range(0, 2):
            print("waiting for queues: {}".format(t))
            time.sleep(1)

        for key in self.binding:
            while True:
                data = self.get_message(key)
                if not data:
                    break
        print("all data is read. write is locked")