from multiprocessing import Queue
import time

class Game:
    Quit, UpdateField, UpdateObjects, RunNewGame, Pause, ActiveGame, RestartGame = range(7)
class GuiControls:
    StopGui, StartGame, UpdateField, UpdateObjects, HandleMouse, HandleKey = range(6)
class GuiScreen:
    TerminateScreen, StartNewGame, UpdateRenderedSurface = range(3)
class Objects:
    Quit, UpdateField, AddObject, SetControlSignal, KingChangeItem, Pause, Run, Restart,\
    UpdateGameSettings, TrainUnit, Polar_grid, UseItem, UpdateObjects, RunFromFile = range(14)
class AIcontrols:
    Quit, Pause, Run, UpdateObjects, UpdateAiSettings = range(5)


class Messenger:
    def __init__(self):
        self.gui_screen_queue = Queue()
        self.game_queue = Queue()
        self.gui_controls_queue = Queue()
        self.objects_queue = Queue()
        self.ai_controls_queue = Queue()
        self.writable = True
        self.binding = {GuiScreen:  self.gui_screen_queue,
                        Game: self.game_queue,
                        Objects: self.objects_queue,
                        GuiControls: self.gui_controls_queue,
                        AIcontrols: self.ai_controls_queue}

    def send_message(self, queue, func, args=None):
        if not self.writable:
            return
        mess = {'func': func}
        if args:
            mess['args'] = args
        try:
            queue.put(mess)
        except Exception as e:
            print("send exception: {}".format(e))
            pass

    def get_message(self, obj_type):
        try:
            data = self.binding[obj_type].get(False)
            return data
        except Exception as e:
            return None

    def game_quit(self):
        self.send_message(self.game_queue, Game.Quit)

    def game_pause(self):
        self.send_message(self.game_queue, Game.Pause)
        self.send_message(self.objects_queue, Objects.Pause)

    def game_unpause(self):
        self.send_message(self.game_queue, Game.ActiveGame)
        self.send_message(self.objects_queue, Objects.Run)

    def restart_game(self):
        self.send_message(self.objects_queue, Objects.Restart)
        self.game_unpause()
        print('Restart game')

    def end_of_game(self):
        print("End of game")
        self.game_pause() #THINKING ABOUT THAT

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

    def objects_set_control_signal(self, index, sig_type, sig_val):
        self.send_message(self.objects_queue, Objects.SetControlSignal, {'obj_index': index, 'sig_type': sig_type, 'sig_val': sig_val})

    # we do it with initialization w/o messages
    #def objects_set_game_settings(self, configuration):
    #    self.send_message(self.objects_queue, Objects.UpdateGameSettings, {'configuration': configuration})

    def objects_run_simulation(self):
        self.send_message(self.objects_queue, Objects.Run)

    def objects_restart_simulation(self):
        self.send_message(self.objects_queue, Objects.Restart)

    def objects_run_from_file_simulation(self):
        self.send_message(self.objects_queue, Objects.RunFromFile)

    def game_update_objects(self, objects_copy):
        self.send_message(self.game_queue, Game.UpdateObjects, {'objects_copy': objects_copy})

    def ai_start_game(self):
        self.send_message(self.ai_controls_queue, AIcontrols.Run)

    def show_polar_grid(self):
        self.send_message(self.objects_queue, Objects.Polar_grid)

    def ai_update_objects(self, objects_copy):
        self.send_message(self.ai_controls_queue, AIcontrols.UpdateObjects, {'objects_copy': objects_copy})

    def shutdown(self):
        print("terminate controls")
        self.controls_terminate()
        print("terminate screen")
        self.screen_terminate()

        self.writable = False
        #make sure threads ended
        for t in range(0, 2):
            print("waiting for queues: {}".format(t))
            time.sleep(0.1)

        for key in self.binding:
            while True:
                data = self.get_message(key)
                if not data:
                    break
            self.binding[key].close()
        print("all data is read. write is locked")