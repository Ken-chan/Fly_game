from multiprocessing import Process
import pyglet
from obj_def import *
from random import *

class AIcontrolsState:
    Start, Run, Exit = range(3)


class AIcontrols(Process):
    def __init__(self, messenger, queue):
        super(AIcontrols, self).__init__()
        self.ai_state = AIcontrolsState.Start
        self.messenger = messenger
        self.objects_obj = None
        self.command_queue = queue
        self.queue_open = True
        self.objects_copy = None
        self.functions = {'quit': self.stop_ai,
                          'update_objects': self.update_objects,
                          'start': self.start_ai_controls}

        pyglet.clock.schedule_interval(self.read_mes, 1.0 / 30.0)
        pyglet.clock.schedule_interval(self.recalc, 1.0 / 30.0)

    def link_objects(self, objects_obj):
        self.objects_obj = objects_obj

    def read_mes(self, dt):
        if self.ai_state != AIcontrolsState.Exit:
            while True:
                data = self.messenger.get_message(self.command_queue)
                if not data:
                    break
                self.functions[data['func']](**data['args']) if 'args' in data else self.functions[data['func']]()

    def start_ai_controls(self, asynced=False):
        if asynced:
            if self.queue_open:
                self.messenger.send_message(self.command_queue, 'start')
            return
        self.ai_state = AIcontrolsState.Run

    def stop_ai(self, asynced=False):
        if asynced:
            if self.queue_open:
                self.messenger.send_message(self.command_queue, 'quit')
            return
        self.queue_open = False
        print("terminating ai controls")
        self.ai_state = AIcontrolsState.Exit
        while True:
            data = self.messenger.get_message(self.command_queue)
            if not data:
                break

    def update_objects(self, objects_copy, asynced=False):
        if asynced:
            if self.queue_open:
                self.messenger.send_message(self.command_queue, 'update_objects', {'objects_copy': objects_copy})
            return
        self.objects_copy = objects_copy

    def recalc(self, dt):
        if self.ai_state == AIcontrolsState.Run and self.objects_copy is not None:
            for index in range(0, ObjectType.ObjArrayTotal):
                if self.objects_copy[index][ObjectProp.ObjType] == ObjectType.Bot2:
                    pressed = 0
                    if self.objects_copy[index][ObjectProp.Velocity] < 20:
                        pressed = random() * 2 - 0.5
                    key = randint(1, 4)
                    #self.messenger.bot2_set_pressed_key(pressed, key)
                    self.objects_obj.set_bot_pressed_key2(pressed, key, asynced=True)
