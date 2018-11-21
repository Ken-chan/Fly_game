from multiprocessing import Process, Queue
import pyglet
from pyglet.window import key as pygletkey
from obj_def import *
import json

alpha = 60
range_of_atack = 200
attack_cone_wide = 20


class ObjectsState:
    Start, Pause, Run, Exit, RunFromFile = range(5)


class ObjectArray:
    def __init__(self):
        self.objects_width = None
        self.objects_height = None
        self.battle_field_width = 0
        self.battle_field_height = 0
        self.current_objects = self.generate_empty_objects()

    def set_objects_settings(self, configuration=None):
        if configuration:
            for key in configuration:
                for item in configuration[key]:
                    if len(item) == 3:
                        x, y, r = item
                        self.add_object(key, x, y, r)
                    else:
                        x, y = item
                        self.add_object(key, x, y, 0)

    def generate_empty_objects(self):
        current_objects = np.zeros((ObjectType.ObjArrayTotal, ObjectProp.Total))
        current_objects[:, 0] = np.arange(ObjectType.ObjArrayTotal)
        return current_objects

    def generate_new_object(self, ind, obj_type, x, y, dir, size):
        return np.array([ind, obj_type, x, y, dir, 0, 0, 0, 0, 0, 0, 0, size])

    def add_object(self, unit_type, x, y, r):
        print("add object: {} {} {} {}".format(unit_type,x,y,r))
        if unit_type == ObjectType.FieldSize:
            self.battle_field_width = x
            self.battle_field_height = y
            return True
        start, end = ObjectType.offset(unit_type)
        for ind in range(start, end+1):
            #search for empty space for object
            if self.current_objects[ind][ObjectProp.ObjType] == ObjectType.Absent:
                if unit_type == ObjectType.Player1 or unit_type == ObjectType.Bot1:
                    dir = 0
                else:
                    dir = 180
                #self.current_objects[ind][ObjectProp.R_size] = 20
                self.current_objects[ind] = self.generate_new_object(ind, unit_type, x, y, dir, r)
                return True
        return False

    def get_objects(self, link_only=False):
        if link_only:
            return self.current_objects
        return np.copy(self.current_objects)



class Objects(Process):
    def __init__(self, messenger):
        super(Objects, self).__init__()
        self.objects_state = ObjectsState.Run
        self.messenger = messenger
        self.game = None
        self.ai = None
        self.command_queue = Queue()
        self.configuration = None
        self.battle_field_width = 0
        self.battle_field_height = 0
        self.objects = ObjectArray()
        self.history_list = self.make_history_list_of_moving("history.txt")
        self.time = 0
        self.currentVelocityforNext = .0
        #self.player_action = PlayerAction(self.objects)
        self.functions = {'quit': self.quit,
                          'add_object': self.objects.add_object,
                          'pause': self.pause_simulation,
                          'run': self.run_simulation,
                          'run_from_file': self.run_history,
                          'update_game_settings': self.update_game_settings,
                          'set_control_signal': self.set_control_signal}
        #self.objects_state = ObjectsState.Pause

        pyglet.clock.schedule_interval(self.read_mes, 1.0 / 30.0)
        pyglet.clock.schedule_interval(self.update_units, 1.0 / 30.0)

    def link_objects(self, ai, game):
        self.ai = ai
        self.game = game

    def quit(self, asynced=False):
        if asynced:
            self.messenger.send_message(self.command_queue, 'quit')
            return
        self.command_queue.close()
        self.objects_state = ObjectsState.Exit
        while True:
            data = self.messenger.get_message(self.command_queue)
            if not data:
                break

    def pause_simulation(self, asynced=False):
        if asynced:
            self.messenger.send_message(self.command_queue, 'pause')
            return
        self.objects_state = ObjectsState.Pause

    def run_simulation(self, asynced=False):
        if asynced:
            self.messenger.send_message(self.command_queue, 'run')
            return
        self.objects_state = ObjectsState.Run

    def run_history(self, asynced=False):
        if asynced:
            self.messenger.send_message(self.command_queue, 'run_from_file')
            return
        self.objects_state = ObjectsState.RunFromFile

    def make_history_list_of_moving(self, history_file):
        with open(history_file, 'r') as file:
            history_list = file.readlines()
        return history_list

    def update_game_settings(self, configuration, asynced=False):
        if asynced:
            self.messenger.send_message(self.command_queue, 'update_game_settings', {'configuration': configuration})
            return
        if self.objects_state == ObjectsState.Run or self.objects_state == ObjectsState.RunFromFile:
            self.configuration = configuration
            self.objects.set_objects_settings(configuration)
            self.battle_field_height = self.objects.battle_field_height
            self.battle_field_width = self.objects.battle_field_width

    def set_control_signal(self, obj_index, control_key, value, asynced=False):
        if asynced:
            self.messenger.send_message(self.command_queue, 'set_control_signal', {'obj_index': obj_index, 'control_key': control_key, 'value': value})
            return
        if self.objects_state == ObjectsState.Run and -1 <= value <= 1 and control_key in (ObjectProp.TurnControl, ObjectProp.VelControl):
            objects = self.objects.get_objects(link_only=True)
            objects[obj_index][control_key] = value

    def is_inside_cone(self, a, b, dir_wide):
        a = a / np.linalg.norm(a)
        b = b / np.linalg.norm(b)
        scalar = np.sum(np.multiply(a, b))
        min_scalar = np.cos(np.pi/180 * dir_wide)
        return True if scalar >= min_scalar else False

    def check_kill(self):
        if self.objects_state == ObjectsState.Run or self.objects_state == ObjectsState.RunFromFile:
            objects = self.objects.get_objects(link_only=True)

            for index in range(0, ObjectType.ObjArrayTotal):
                if objects[index][ObjectProp.ObjType] != ObjectType.Absent:
                    x1, y1 = objects[index][ObjectProp.Xcoord], objects[index][ObjectProp.Ycoord]
                    if (x1 > self.battle_field_width or y1 > self.battle_field_height or x1 < 0 or y1 < 0):
                        self.delete_object(index, objects)
                    dir1 = objects[index][ObjectProp.Dir]
                    vec1 = np.array([np.cos(dir1 * np.pi/180), np.sin(dir1 * np.pi/180)])

                    for jndex in range(0, ObjectType.ObjArrayTotal):
                        if objects[jndex][1] != ObjectType.Absent and index != jndex:
                            x2, y2 = objects[jndex][ObjectProp.Xcoord], objects[jndex][ObjectProp.Ycoord]
                            dir2 = objects[jndex][ObjectProp.Dir]
                            vec2 = np.array([np.cos(dir2 * np.pi / 180), np.sin(dir2 * np.pi / 180)])
                            diff_vector = np.array([x2 - x1, y2 - y1])
                            distance = np.linalg.norm(diff_vector)
                            if distance <= objects[index][ObjectProp.R_size] + objects[jndex][ObjectProp.R_size]:
                                self.delete_object(index, objects)
                                self.delete_object(jndex, objects)
                                break
                            if distance < range_of_atack and self.is_inside_cone(vec1, vec2, attack_cone_wide):
                                self.delete_object(jndex, objects)

    def delete_object(self, jndex, objects):
        print("Killed unit number ", jndex)
        for kndex in range(1, ObjectProp.Total):
            objects[jndex][kndex] = 0

    def add_object(self, unit_type, x, y, r, asynced=False):
        if asynced:
            self.messenger.send_message(self.command_queue, 'add_object', {'unit_type': unit_type, 'x': x, 'y': y, 'r': r})
            return
        self.objects.add_object(unit_type, x, y, r)

    def update_units(self, dt):
        if self.objects_state == ObjectsState.Run:
            objects = self.objects.get_objects(link_only=True)
            for index in range(0, ObjectType.ObjArrayTotal):
                if objects[index][1] != ObjectType.Absent:
                    objects[index][ObjectProp.PrevVelocity] = objects[index][ObjectProp.Velocity]
                    objects[index][ObjectProp.PrevAngleVel] = objects[index][ObjectProp.AngleVel]

                    k1 = 130
                    k2 = 0.01
                    k3 = 0.05
                    k4 = 110 #Yep
                    k5 = 0.01

                    a = k1 * objects[index][ObjectProp.VelControl] - k2 * np.abs(objects[index][ObjectProp.AngleVel]) * objects[index][ObjectProp.Velocity] - \
                        k3 * objects[index][ObjectProp.Velocity]

                    b = k4 * objects[index][ObjectProp.TurnControl] - k5 * objects[index][ObjectProp.AngleVel]
                    #velocity of angle
                    objects[index][ObjectProp.Velocity] = a * dt + objects[index][ObjectProp.PrevVelocity]
                    #objects[index][ObjectProp.AngleVel] = b * dt + objects[index][ObjectProp.PrevAngleVel]
                    objects[index][ObjectProp.AngleVel] = k4 * objects[index][ObjectProp.TurnControl]

                    objects[index][ObjectProp.Dir] += objects[index][ObjectProp.AngleVel] * dt

                    objects[index][ObjectProp.Dir] = objects[index][ObjectProp.Dir] % 360
                    rad = objects[index][ObjectProp.Dir] * np.pi / 180

                    objects[index][ObjectProp.Xcoord] += objects[index][ObjectProp.Velocity] * np.sin(rad) * dt
                    objects[index][ObjectProp.Ycoord] += objects[index][ObjectProp.Velocity] * np.cos(rad) * dt

            self.check_kill()
            self.objects.current_objects = objects
            self.ai.update_objects(self.objects.get_objects(), asynced=True)
            self.game.update_objects(self.objects.get_objects(), asynced=True)
            return

        if self.objects_state == ObjectsState.RunFromFile:
            objects = self.objects.get_objects(link_only=True)
            for index in range(0, ObjectType.ObjArrayTotal):
                if objects[index][1] != ObjectType.Absent:
                    if self.index_moving != len(self.history_list):
                        json_string = self.history_list[self.index_moving]
                        parsed = json.loads(json_string)
                        if int(parsed['ObjectID']) == objects[index][ObjectProp.ObjId]:
                            objects[index][ObjectProp.Xcoord] = parsed['Xcoord']
                            objects[index][ObjectProp.Ycoord] = parsed['Ycoord']
                            objects[index][ObjectProp.Dir] = parsed['Direction']
                        self.index_moving += 1
                    else:
                        self.index_moving = 0

            self.check_kill()
            self.objects.current_objects = objects
            self.game.update_objects(self.objects.get_objects(), asynced=True)
            self.ai.update_objects(self.objects.get_objects(), asynced=True)

    def read_mes(self, dt):
        if self.objects_state != ObjectsState.Exit:
            while True:
                data = self.messenger.get_message(self.command_queue)
                if data is None:
                    break
                self.functions[data['func']](**data['args']) if 'args' in data else self.functions[data['func']]()

