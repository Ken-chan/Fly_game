from multiprocessing import Process, Queue
import pyglet
import messages
from obj_def import *


class ObjectsState:
    Start, Pause, Run, Exit, RunFromFile, FileEnd = range(6)


class ObjectArray:
    def __init__(self):
        self.objects_width = None
        self.objects_height = None
        self.battle_field_width = 0
        self.battle_field_height = 0
        self.current_objects = None
        self.generate_empty_objects()

    def set_objects_settings(self, configuration=None):
        if configuration:
            for key in configuration:
                for item in configuration[key]:
                    if len(item) == 5:
                        x, y, direction, vehicle_type, r = item
                        self.add_object(key, x, y, direction, vehicle_type, r)
                    elif len(item) == 6:
                        x, y, direction, vehicle_type, r, aitype = item
                    else:
                        x, y = item
                        direction, vehicle_type, r = 0, 0, 0
                    self.add_object(key, x, y, direction, vehicle_type, r)

    def generate_empty_objects(self):
        self.current_objects = np.zeros((ObjectType.ObjArrayTotal, ObjectProp.Total))
        self.current_objects[:, 0] = np.arange(ObjectType.ObjArrayTotal)

    def generate_new_object(self, ind, obj_type, x, y, direction, size, vehicle_type):
        return np.array([ind, obj_type, x, y, direction, 0, 0, 0, 0, 0, 0, 0, size, vehicle_type])

    def add_object(self, unit_type, x, y, direction, vehicle_type, r):
        if unit_type == ObjectType.FieldSize:
            self.battle_field_width = x
            self.battle_field_height = y
            return True
        start, end = ObjectType.offset(unit_type)
        for ind in range(start, end+1):
            #search for empty space for object
            if self.current_objects[ind][ObjectProp.ObjType] == ObjectType.Absent:
                self.current_objects[ind] = self.generate_new_object(ind, unit_type, x, y, direction, r, vehicle_type)
                return True
        return False

    def substitute_objects(self, new_objects):
        self.current_objects = new_objects
        return

    def get_objects(self, link_only=False):
        if link_only:
            return self.current_objects
        return np.copy(self.current_objects)



class Objects:
    def __init__(self, messenger, configuration, history_path):
        #super(Objects, self).__init__()
        self.objects_state = ObjectsState.Run
        self.messenger = messenger
        self.configuration = None
        self.battle_field_width = 0
        self.battle_field_height = 0
        self.objects = ObjectArray()
        self.update_game_settings(configuration)
        self.index_moving = 0
        self.hist_file_name = history_path
        self.loaded_history = None
        self.history_index = 0
        self.history_time_len = 0
        self.time = 0
        self.currentVelocityforNext = .0
        self.history_mode = False
        self.restart_counter = 0
        self.playtime = 0
        self.framerate = 30
        self.maxplaytime = 60 * self.framerate
        self.team1_survives = None
        self.team2_survives = None
        #self.player_action = PlayerAction(self.objects)
        self.functions = {messages.Objects.Quit: self.quit,
                          messages.Objects.AddObject: self.objects.add_object,
                          messages.Objects.SetControlSignal: self.set_control_signal,
                          messages.Objects.Pause: self.pause_simulation,
                          messages.Objects.Run: self.run_simulation,
                          messages.Objects.RunFromFile: self.run_history,
                          messages.Objects.Restart: self.restart,
                          messages.Objects.UpdateGameSettings: self.update_game_settings}
        #self.objects_state = ObjectsState.Pause

        pyglet.clock.schedule_interval(self.read_mes, 1.0 / self.framerate)
        pyglet.clock.schedule_interval(self.update_units, 1.0 / self.framerate)

    def quit(self):
        self.objects_state = ObjectsState.Exit

    def pause_simulation(self):
        self.objects_state = ObjectsState.Pause

    def run_simulation(self):
        self.objects_state = ObjectsState.Run

    def restart(self):
        if self.history_mode:
            return
        self.objects.generate_empty_objects()
        self.objects.set_objects_settings(self.configuration)
        self.objects_state = ObjectsState.Run
        self.restart_counter += 1
        self.playtime = 0

    def run_history(self):
        self.objects_state = ObjectsState.RunFromFile
        self.history_mode = True

    def load_history_file(self, file):
        with open(file, 'r') as fd:
            state_str = fd.readlines()
        time_len = len(state_str)
        self.loaded_history = np.zeros((time_len, ObjectType.ObjArrayTotal, ObjectProp.Total))
        strind = 0
        for line in state_str:
            numsback_str = line.split(',')
            numsback = np.array([float(item) for item in numsback_str])
            reshaped = np.reshape(numsback, (ObjectType.ObjArrayTotal, ObjectProp.Total))
            self.loaded_history[strind] = reshaped
            strind += 1
        self.history_time_len = time_len

    def save_history_file(self, file_name, obj_array):
        flat_obj = np.reshape(obj_array, ObjectType.ObjArrayTotal * ObjectProp.Total)
        obj_str = ''
        for item in flat_obj:
            obj_str += '{},'.format(item)
        obj_str = obj_str[:-1]
        if self.restart_counter != 0:
            file_name = str(self.restart_counter)+'_'+ file_name
        with open(file_name, 'a') as f:
            f.write(obj_str + '\n')

    def update_game_settings(self, configuration):
        if self.objects_state == ObjectsState.Run or self.objects_state == ObjectsState.RunFromFile:
            self.configuration = configuration
            self.objects.set_objects_settings(configuration)
            self.battle_field_height = self.objects.battle_field_height
            self.battle_field_width = self.objects.battle_field_width

    def set_control_signal(self, obj_index, sig_type, sig_val):
        if self.objects_state == ObjectsState.Run and -1 <= sig_val <= 1 and sig_type in (ObjectProp.TurnControl, ObjectProp.VelControl):
            objects = self.objects.get_objects(link_only=True)
            objects[obj_index][sig_type] = sig_val

    def is_inside_cone(self, a, b, diff_vector, dir_wide):
        self.a = a / np.linalg.norm(a)
        self.b = b / np.linalg.norm(b)
        diff_vector = diff_vector / np.linalg.norm(diff_vector)
        scalar_a_b = np.sum(np.multiply(self.a, self.b))
        scalar_a_diff = np.sum(np.multiply(self.a, diff_vector))
        min_scalar = np.cos(np.radians(dir_wide))
        return True if scalar_a_b >= min_scalar and scalar_a_diff >= min_scalar else False

    def check_kill_and_end_of_game(self):
        self.team1_survives, self.team2_survives = 0, 0
        self.dir1, self.vec1 = None, None
        self.dir2, self.vec2 = None, None
        self.diff_vector, self.distance = None, None
        if self.objects_state == ObjectsState.Run or self.objects_state == ObjectsState.RunFromFile:
            objects = self.objects.get_objects(link_only=True)

            for index in range(0, ObjectType.ObjArrayTotal):
                if objects[index][ObjectProp.ObjType] != ObjectType.Absent:
                    x1, y1 = objects[index][ObjectProp.Xcoord], objects[index][ObjectProp.Ycoord]
                    if x1 > self.battle_field_width or y1 > self.battle_field_height or x1 < 0 or y1 < 0:
                        self.delete_object(index, objects)
                        continue
                    self.dir1 = objects[index][ObjectProp.Dir]
                    self.vec1 = np.array([np.cos(np.radians(self.dir1)), np.sin(np.radians(self.dir1))])

                    for jndex in range(0, ObjectType.ObjArrayTotal):
                        if objects[jndex][ObjectProp.ObjType] != ObjectType.Absent and index != jndex:
                            x2, y2 = objects[jndex][ObjectProp.Xcoord], objects[jndex][ObjectProp.Ycoord]
                            self.dir2 = objects[jndex][ObjectProp.Dir]
                            self.vec2 = np.array([np.cos(np.radians(self.dir2)), np.sin(np.radians(self.dir2))])
                            self.diff_vector = np.array([x2 - x1, y2 - y1])
                            self.distance = np.linalg.norm(self.diff_vector)
                            if self.distance <= objects[index][ObjectProp.R_size] + objects[jndex][ObjectProp.R_size]:
                                self.delete_object(index, objects)
                                self.delete_object(jndex, objects)
                                break

                            if Teams.team_by_id(index)!= Teams.team_by_id(jndex) and self.distance < Constants.AttackRange and \
                                    self.is_inside_cone(self.vec1, self.vec2, self.diff_vector, Constants.AttackConeWide):
                                self.delete_object(jndex, objects)

                            #Count survives to check end of game
                            if Teams.team_by_id(jndex) == Teams.Team1:
                                self.team1_survives += 1
                            elif Teams.team_by_id(jndex) == Teams.Team2:
                                self.team2_survives += 1
            # END_OF_GAME_TRIGGERED
            if self.team1_survives < 1 or self.team2_survives < 1:
                self.messenger.end_of_game()

    def delete_object(self, jndex, objects):
        print("Killed unit number ", jndex)
        for kndex in range(1, ObjectProp.Total):
            objects[jndex][kndex] = 0

    def add_object(self, unit_type, x, y, direction, vehicle_type, r):
        self.objects.add_object(unit_type, x, y, direction, vehicle_type, r)

    def calc_v_diff(self, object_state):
        min_v_add = 0
        if object_state[ObjectProp.VehicleType] == ObjectSubtype.Plane:
            min_v_add = Constants.MinVelAccCoef * np.abs(object_state[ObjectProp.Velocity] - Constants.MinPlaneVel) if object_state[ObjectProp.Velocity] < Constants.MinPlaneVel else 0
        dv = Constants.VelAccCoef * (object_state[ObjectProp.VelControl]) - Constants.TurnDissipationCoef * np.abs(object_state[ObjectProp.AngleVel]) * \
             object_state[ObjectProp.Velocity] - Constants.AirResistanceCoef * object_state[ObjectProp.Velocity] + min_v_add
        w = Constants.TurnAccCoef * object_state[ObjectProp.TurnControl]
        return dv, w

    def update_units(self, dt):
        objects = self.objects.get_objects(link_only=True)
        self.dv, self.w = None, None
        if self.objects_state == ObjectsState.Run:
            for index in range(0, ObjectType.ObjArrayTotal):
                if objects[index][ObjectProp.ObjType] != ObjectType.Absent:
                    objects[index][ObjectProp.PrevVelocity] = objects[index][ObjectProp.Velocity]
                    objects[index][ObjectProp.PrevAngleVel] = objects[index][ObjectProp.AngleVel]
                    self.dv, self.w = self.calc_v_diff(objects[index])
                    objects[index][ObjectProp.Velocity] = self.dv * dt + objects[index][ObjectProp.PrevVelocity]
                    objects[index][ObjectProp.AngleVel] = self.w
                    objects[index][ObjectProp.Dir] += objects[index][ObjectProp.AngleVel] * dt
                    objects[index][ObjectProp.Dir] = objects[index][ObjectProp.Dir] % 360
                    rad = np.radians(objects[index][ObjectProp.Dir])
                    objects[index][ObjectProp.Xcoord] += objects[index][ObjectProp.Velocity] * np.cos(rad) * dt
                    objects[index][ObjectProp.Ycoord] += objects[index][ObjectProp.Velocity] * np.sin(rad) * dt
            self.save_history_file(self.hist_file_name, objects)
            self.check_kill_and_end_of_game()
            self.objects.current_objects = objects
            self.messenger.game_update_objects(self.objects.get_objects())
            self.messenger.ai_update_objects(self.objects.get_objects())
            self.playtime += 1
            if self.playtime >= self.maxplaytime:
                self.messenger.end_of_game()

        if self.objects_state == ObjectsState.RunFromFile:
            if self.loaded_history is None:
                self.load_history_file(self.hist_file_name)
                self.history_index = 0
            if self.history_time_len <= self.history_index:
                self.objects_state = ObjectsState.FileEnd
                self.messenger.game_quit()
                return
            self.objects.substitute_objects(self.loaded_history[self.history_index])
            self.history_index += 1
            self.messenger.game_update_objects(self.objects.get_objects())
            self.messenger.ai_update_objects(self.objects.get_objects())

    def read_mes(self, dt):
        if self.objects_state != ObjectsState.Exit:
            while True:
                data = self.messenger.get_message(messages.Objects)
                if data is None:
                    break
                self.functions[data['func']](**data['args']) if 'args' in data else self.functions[data['func']]()


