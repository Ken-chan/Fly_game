import pyglet
import messages
from obj_def import *
from tools import Loss, Helper
from ai_controls import AItype
import numpy as np


class ObjectsState:
    Start, Pause, Run, Exit, RunFromFile, FileEnd = range(6)


class ObjectArray:
    def __init__(self):
        self.objects_width = None
        self.objects_height = None
        self.battle_field_width = 0
        self.battle_field_height = 0
        self.current_objects = None
        self.start_ind, self.end_ind = None, None
        self.generate_empty_objects()

    def set_objects_settings(self, configuration=None, shuffled=False, count_in_teams=0):
        if configuration:
            for key in configuration:
                for item in configuration[key]:
                    if len(item) == 5:
                        x, y, direction, vehicle_type, r = item
                    elif len(item) == 6:
                        x, y, direction, vehicle_type, r, aitype = item
                        if shuffled:
                            delta_x = int(0.8*self.battle_field_width//2//(1+count_in_teams))
                            x += np.random.randint(-delta_x, delta_x)
                            y += np.random.randint(-20, 20)
                            direction += np.random.randint(-15, 15)
                    else:
                        x, y = item
                        direction, vehicle_type, r = 0, 0, 0
                    #print('{}: x = {}, y = {}, dir = {}'.format('restarted', x, y, direction))
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
        self.start_ind, self.end_ind = ObjectType.offset(unit_type)
        for ind in range(self.start_ind, self.end_ind+1):
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
    def __init__(self, configuration, radiant, dire, history_path, messenger=None, ai_controls=None, tries=None,
                 bot1=None, bot2=None, player1=None, player2=None, sizeX=None, sizeY=None, queue_res=None):
        self.objects_state = ObjectsState.Run
        self.train_mode = True
        if ai_controls == None:
            self.train_mode = False
        self.in_game = True
        self.tries = tries
        self.current_try = 1
        self.messenger = messenger
        self.radiant_start = radiant
        self.dire_start = dire
        self.radiant = self.radiant_start
        self.dire = self.dire_start
        self.max_in_one_team = np.maximum(self.radiant_start, self.dire_start)
        self.configuration = configuration
        self.ai_controls = ai_controls
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
        self.maxplaytime = 25 #* self.framerate

        #self.loss = Loss() #loss take config from objects(not from game)
        self.angle_between_objects = np.float(0.0)
        self.angle_between_radius = np.float(0.0)
        #initialization starts
        #self.team1_survives = np.int32(0)
        #self.team2_survives = np.int32(0)
        self.x1, self.x2, self.y1, self.y2 = np.float(0.0), np.float(0.0), np.float(0.0), np.float(0.0)
        self.radius = np.float(0.0)
        self.a_vec, self.b_vec = None, None
        self.vec1 = np.array([0.0, 0.0])
        self.vec2 = np.array([0.0, 0.0])
        self.dir2 = np.float(0.0)
        self.dir1 = np.float(0.0)
        self.distance = np.float(0.0)
        self.diff_vector = np.array([0.0, 0.0])
        self.diff_vector_norm = None
        self.scalar_a_b = np.float(0.0)
        self.scalar_a_diff = np.float(0.0)
        self.min_scalar = np.float(0.0)

        self.min_v_add = np.int32(0)
        self.dv, self.w = np.float(0.0), np.float(0.0)
        self.dv_calc, self.w_calc = np.float(0.0), np.float(0.0)
        self.cur_rad = np.float(0.0)
        self.is_game_freezed = False
        self.queue_res = queue_res
        #initialization ends


        self.functions = {messages.Objects.Quit: self.quit,
                          messages.Objects.AddObject: self.objects.add_object,
                          messages.Objects.SetControlSignal: self.set_control_signal,
                          messages.Objects.Pause: self.pause_simulation,
                          messages.Objects.Run: self.run_simulation,
                          messages.Objects.RunFromFile: self.run_history,
                          messages.Objects.Restart: self.restart,
                          messages.Objects.UpdateGameSettings: self.update_game_settings}
        #self.objects_state = ObjectsState.Pause

        self.bot1 = np.int32(0)
        self.bot2 = np.int32(0)
        self.player1 = np.int32(0)
        self.player2 = np.int32(0)
        self.sizeX = np.int32(self.battle_field_width)
        self.sizeY = np.int32(self.battle_field_width)
        self.pos1 = self.sizeX // 2
        self.pos2 = self.sizeX // 2
        self.victories = np.int32(0)
        self.defeats = np.int32(0)
        self.draws = np.int32(0)
        self.norm_red_team = np.float(0.0)
        self.norm_blue_team = np.float(0.0)
        self.time_succ = np.float(0.0)
        self.is_it_draw = False

        self.success = np.float(0.0)
        self.package_from_games = None
        self.helper = Helper()
        self.dict_score = self.helper.create_dict_score(self.radiant_start, self.dire_start)

        if self.train_mode:
            self._index, self._vel_ctrl, self._turn_ctrl = 0, 0, 0
            self.ai_controls.start_ai_controls()
            pyglet.clock.schedule(self.update_units)

            #for time ###################
            self.bot1 = bot1
            self.bot2 = bot2
            self.player1 = player1
            self.player2 = player2
            self.sizeX = sizeX
            self.sizeY = sizeY
            ######################

        else:
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
        if not self.train_mode or (self.tries is not None and self.restart_counter + 1 < self.tries):
            self.objects_state = ObjectsState.Run
            if self.train_mode:
                self.objects.generate_empty_objects()
                self.update_game_settings(self.configuration, shuffled=True, count_in_teams=self.max_in_one_team)
                self.ai_controls.update_ai_settings(self.configuration)
            else:
                self.objects.generate_empty_objects()
                self.objects.set_objects_settings(self.configuration, shuffled=True, count_in_teams=self.max_in_one_team)
            self.restart_counter += 1
            self.playtime = 0
            self.radiant = self.radiant_start
            self.dire = self.dire_start
        else:
            self.messenger.game_quit()

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
        return
        flat_obj = np.reshape(obj_array, ObjectType.ObjArrayTotal * ObjectProp.Total)
        obj_str = ''
        for item in flat_obj:
            obj_str += '{},'.format(item)
        obj_str = obj_str[:-1]
        if self.restart_counter != 0:
            file_name = str(self.restart_counter)+'_'+ file_name
        with open(file_name, 'a') as f:
            f.write(obj_str + '\n')

    def update_game_settings(self, configuration, shuffled=False, count_in_teams=0):
        if self.objects_state == ObjectsState.Run or self.objects_state == ObjectsState.RunFromFile:
            self.configuration = configuration
            self.objects.set_objects_settings(configuration, shuffled=shuffled, count_in_teams=count_in_teams)
            self.battle_field_height = self.objects.battle_field_height
            self.battle_field_width = self.objects.battle_field_width

    def set_control_signal(self, obj_index, sig_type, sig_val):
        if self.objects_state == ObjectsState.Run and -1 <= sig_val <= 1 and sig_type in (ObjectProp.TurnControl, ObjectProp.VelControl):
            objects = self.objects.get_objects(link_only=True)
            objects[obj_index][sig_type] = sig_val

    def is_inside_cone(self, a, b, diff_vect, dir_wide):
        self.a_vec = a / np.linalg.norm(a)
        self.b_vec = b / np.linalg.norm(b)
        self.diff_vector_norm = diff_vect / np.linalg.norm(diff_vect)
        self.scalar_a_b = np.sum(np.multiply(self.a_vec, self.b_vec), dtype=np.float)
        self.scalar_a_diff = np.sum(np.multiply(self.a_vec, self.diff_vector_norm), dtype=np.float)
        self.min_scalar = np.cos(np.radians(dir_wide))
        return True if self.scalar_a_b >= self.min_scalar and self.scalar_a_diff >= self.min_scalar else False

    def check_kill_and_end_of_game(self):
        #self.team1_survives, self.team2_survives = 0, 0 #not triggered end of game
        if self.objects_state == ObjectsState.Run or self.objects_state == ObjectsState.RunFromFile:
            objects = self.objects.get_objects(link_only=True)
            #print(objects, "   curr obj")

            for index in range(0, ObjectType.ObjArrayTotal):
                if objects[index][ObjectProp.ObjType] != ObjectType.Absent:
                    self.x1, self.y1 = objects[index][ObjectProp.Xcoord], objects[index][ObjectProp.Ycoord]
                    self.radius = objects[index][ObjectProp.R_size]
                    if self.x1 >= self.battle_field_width - self.radius - 1 or self.y1 >= self.battle_field_height - self.radius - 1 or \
                            self.x1 <= self.radius + 1 or self.y1 <= self.radius + 1:
                        self.delete_object(index, objects)
                        continue
                    self.dir1 = objects[index][ObjectProp.Dir]
                    self.vec1[0], self.vec1[1] = np.cos(np.radians(self.dir1)), np.sin(np.radians(self.dir1))

                    for jndex in range(0, ObjectType.ObjArrayTotal):
                        if objects[jndex][ObjectProp.ObjType] != ObjectType.Absent and index != jndex:
                            self.x2, self.y2 = objects[jndex][ObjectProp.Xcoord], objects[jndex][ObjectProp.Ycoord]
                            self.dir2 = objects[jndex][ObjectProp.Dir]
                            self.vec2 = np.array([np.cos(np.radians(self.dir2)), np.sin(np.radians(self.dir2))])
                            self.diff_vector[0], self.diff_vector[1] = self.x2 - self.x1, self.y2 - self.y1
                            self.distance = np.linalg.norm(self.diff_vector)
                            if self.distance <= self.radius + objects[jndex][ObjectProp.R_size]:
                                self.delete_object(index, objects, second_unit=jndex)
                                #self.delete_object(jndex, objects)
                                break

                            if Teams.team_by_id(index)!= Teams.team_by_id(jndex) and self.distance < Constants.AttackRange and \
                                    self.is_inside_cone(self.vec1, self.vec2, self.diff_vector, Constants.AttackConeWide):
                                self.delete_object(jndex, objects)

            ### Strings to calculate succes with enof of game score
            if (self.radiant < 1 and self.dire < 1) or self.playtime >= self.maxplaytime:
                self.draws += 1
                self.time_succ += 0.5
            elif self.radiant < 1:
                self.defeats += 1
                self.time_succ += 1
            elif self.dire < 1:
                self.victories += 1

            # END_OF_GAME_TRIGGERED
            if self.radiant < 1 or self.dire < 1 or (self.playtime >= self.maxplaytime):
                self.time_succ += self.playtime / self.maxplaytime
                self.norm_red_team += self.radiant/self.radiant_start
                self.norm_blue_team += self.dire/self.dire_start

                self.dict_score["Red '{}':Blue '{}'".format(self.radiant, self.dire)] += 1

                self.messenger.end_of_game(trainmode=self.train_mode)
                self.objects_state = ObjectsState.Pause

                if self.train_mode:
                    #print('-> Wins:{}, Loses:{}, Draws:{}, Time Succ:{:.5f}. > Restarted game number:{}{}'.format(self.victories, self.defeats, self.draws, self.time_succ, self.restart_counter,'_'))
                    if self.victories+self.defeats+self.draws == self.tries:
                        #self.success = (self.victories - self.defeats - 0.5*self.draws - 0.5*self.time_succ)/self.tries #w time

                        self.success = (self.norm_red_team - self.norm_blue_team)/self.tries
                        self.package_from_games = [self.success, self.dict_score]
                        self.queue_res.put(self.package_from_games)
                    self.restart()


    def delete_object(self, jndex, objects, second_unit=None):
        if not self.train_mode:
            team_alone = "Blue" if Teams.team_by_id(jndex) == 1 else "Red"
            print("Killed '{}' unit from {} team with number: {}"\
                .format(ObjectType.name_of_type_by_id(jndex), team_alone, jndex))

        for kndex in range(1, ObjectProp.Total):
            objects[jndex][kndex] = 0
        if Teams.team_by_id(jndex) == Teams.Team1:
            self.radiant -= 1
        elif Teams.team_by_id(jndex) == Teams.Team2:
            self.dire -= 1

        if second_unit is not None:
            if not self.train_mode:
                team_twice = "Blue" if Teams.team_by_id(second_unit) == 1 else "Red"
                print("Killed '{}' unit from {} team with number: {}"\
                    .format(ObjectType.name_of_type_by_id(second_unit), team_twice, second_unit))
            for kndex in range(1, ObjectProp.Total):
                objects[second_unit][kndex] = 0
            if Teams.team_by_id(second_unit) == Teams.Team1:
                self.radiant -= 1
            elif Teams.team_by_id(second_unit) == Teams.Team2:
                self.dire -= 1

    def add_object(self, unit_type, x, y, direction, vehicle_type, r):
        self.objects.add_object(unit_type, x, y, direction, vehicle_type, r)

    def calc_v_diff(self, object_state):
        self.min_v_add = 0
        if object_state[ObjectProp.VehicleType] == ObjectSubtype.Plane:
            self.min_v_add = Constants.MinVelAccCoef * np.abs(object_state[ObjectProp.Velocity] - Constants.MinPlaneVel) if object_state[ObjectProp.Velocity] < Constants.MinPlaneVel else 0
        self.dv_calc = Constants.VelAccCoef * (object_state[ObjectProp.VelControl]) - Constants.TurnDissipationCoef * np.abs(object_state[ObjectProp.AngleVel]) * \
             object_state[ObjectProp.Velocity] - Constants.AirResistanceCoef * object_state[ObjectProp.Velocity] + self.min_v_add
        self.w_calc = Constants.TurnAccCoef * object_state[ObjectProp.TurnControl]
        return self.dv_calc, self.w_calc

    def update_units(self, dt):
        if self.train_mode:
            dt = 1.0 / self.framerate
        objects = self.objects.get_objects(link_only=True)
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
                    self.cur_rad = np.radians(objects[index][ObjectProp.Dir])
                    objects[index][ObjectProp.Xcoord] += objects[index][ObjectProp.Velocity] * np.cos(self.cur_rad) * dt
                    if objects[index][ObjectProp.Xcoord] >= self.battle_field_width:
                        objects[index][ObjectProp.Xcoord] = self.battle_field_width - 1
                    if objects[index][ObjectProp.Xcoord] <= 0:
                        objects[index][ObjectProp.Xcoord] = 1
                    objects[index][ObjectProp.Ycoord] += objects[index][ObjectProp.Velocity] * np.sin(self.cur_rad) * dt
                    if objects[index][ObjectProp.Ycoord] >= self.battle_field_height:
                        objects[index][ObjectProp.Ycoord] = self.battle_field_height - 1
                    if objects[index][ObjectProp.Ycoord] <= 0:
                        objects[index][ObjectProp.Ycoord] = 1
            self.save_history_file(self.hist_file_name, objects)
            self.objects.current_objects = objects

            self.check_kill_and_end_of_game()
            if not self.train_mode:
                self.messenger.game_update_objects(self.objects.get_objects())
                self.messenger.ai_update_objects(self.objects.get_objects())
            else:
                #print("x = ", self.objects.current_objects[2][ObjectProp.Xcoord], " y = ", self.objects.current_objects[2][ObjectProp.Ycoord])
                #print("x = ", self.objects.current_objects[13][ObjectProp.Xcoord], " y = ",
                #      self.objects.current_objects[13][ObjectProp.Ycoord])
                self.result = self.ai_controls.recalc(1/self.framerate, self.objects.current_objects)
                for key in self.result:
                    self.set_control_signal(key[0], ObjectProp.VelControl, key[1])
                    self.set_control_signal(key[0], ObjectProp.TurnControl, key[2])
                #pass
            self.playtime += 1/self.framerate
            #print(self.playtime, " maxplaytime = ", self.maxplaytime)

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
