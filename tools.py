import numpy as np
from obj_def import *

class SimpleLoss:
    def __init__(self, battle_field_size):
        #self.configuration = configuration
        self.x_size, self.y_size = battle_field_size
        print(self.x_size, self.y_size)

    def is_inside_cone(self, a, b, diff_vect, dir_wide):
        a_vec = a / np.linalg.norm(a)
        b_vec = b / np.linalg.norm(b)
        diff_vector_norm = diff_vect / np.linalg.norm(diff_vect)
        scalar_a_b = np.sum(np.multiply(a_vec, b_vec), dtype=np.float)
        scalar_a_diff = np.sum(np.multiply(a_vec, diff_vector_norm), dtype=np.float)
        min_scalar = np.cos(np.radians(dir_wide))
        return True if scalar_a_b >= min_scalar and scalar_a_diff >= min_scalar else False

    def loss_result(self, obj, objects):
        obj_id, obj_x, obj_y, obj_dir = obj[ObjectProp.ObjId], obj[ObjectProp.Xcoord], obj[ObjectProp.Ycoord], obj[ObjectProp.Dir]
        #print(obj[ObjectProp.Velocity])
        if obj_x <= Constants.DefaultObjectRadius or obj_x >= self.x_size - Constants.DefaultObjectRadius:
            return -1
        if obj_y <= Constants.DefaultObjectRadius or obj_y >= self.y_size - Constants.DefaultObjectRadius:
            return -1
        team = Teams.team_by_id(obj_id)
        enemy_team = Teams.get_opposite_team(team)
        friend_ids = Teams.get_team_obj_ids(team)
        enemy_ids = Teams.get_team_obj_ids(enemy_team)
        for friend_id in friend_ids:
            if friend_id == obj_id:
                continue
            friend_x, friend_y = objects[friend_id][ObjectProp.Xcoord], objects[friend_id][ObjectProp.Ycoord]
            if np.linalg.norm([obj_x - friend_x, obj_y - friend_y]) <= 2 * Constants.DefaultObjectRadius:
                return -1
        for enemy_id in enemy_ids:
            enemy_x, enemy_y, enemy_dir = objects[enemy_id][ObjectProp.Xcoord], objects[enemy_id][ObjectProp.Ycoord], objects[enemy_id][ObjectProp.Dir]
            if np.linalg.norm([obj_x - enemy_x, obj_y - enemy_y]) <= 2 * Constants.DefaultObjectRadius:
                return -1
            vec1 = np.array([np.cos(np.radians(obj_dir)), np.sin(np.radians(obj_dir))])
            vec2 = np.array([np.cos(np.radians(enemy_dir)), np.sin(np.radians(enemy_dir))])
            diff_vector = np.array([enemy_x - obj_x, enemy_y - obj_y])
            self.distance = np.linalg.norm(diff_vector)
            if self.is_inside_cone(vec1, vec2, diff_vector, Constants.AttackConeWide) and self.distance < Constants.AttackRange:
                return 1
            if self.is_inside_cone(vec2, vec1, -diff_vector, Constants.AttackConeWide) and self.distance < Constants.AttackRange:
                return -1
        return 0


class Loss():
    def __init__(self, whoami=None):
        self.whoami = whoami
        self.battle_field_size = np.array([1000.0, 1000.0])
        #self.set_congiguration(configuration)
        self.n_cuts = 20
        self.qstate = QState(20)
        self.q_data = np.zeros((self.qstate.n_cuts, self.qstate.n_cuts, self.qstate.n_cuts))

        self.qstate.load_history_file(self.qstate.cube_path, self.q_data)

        self.min_x = np.float(0.0)
        self.min_y = np.float(0.0)
        self.norm_min_distance = np.float(0.0)
        self.danger_distance_norm = np.float(0.2) #critical distance to danger objects(normalize)
        self.danger_distance_alies = np.float(0.0)
        self.norm_danger_distance_alies = np.float(0.5)  # value is piece of attack range
        self.max_speed_of_objects = 400
        self.dir = np.float(0.0)
        self.vec = np.array([np.float(0.0), np.float(0.0)])

        #coefs to distance func
        self.a = 0.5*(-self.danger_distance_norm + np.sqrt(self.danger_distance_norm**2 + 4*self.danger_distance_norm))
        self.b = (1-self.a)/self.a
        self.n1, self.n2 = np.array([np.float(0.0), np.float(0.0)]), np.array([np.float(0.0), np.float(0.0)])
        self.n3, self.n4 = np.array([np.float(0.0), np.float(0.0)]), np.array([np.float(0.0), np.float(0.0)])
        self.dist_wall1, self.dist_wall2 = np.float(0.0), np.float(0.0)
        self.dist_wall3, self.dist_wall4 = np.float(0.0), np.float(0.0)
        self.loss_dist1, self.loss_dist2 = np.float(0.0), np.float(0.0)
        self.loss_dist3, self.loss_dist4 = np.float(0.0), np.float(0.0)
        #coefs to distance func

        # coefs to alies func
        self.c = 0.5*(-self.norm_danger_distance_alies + np.sqrt(self.norm_danger_distance_alies**2 + 4*self.norm_danger_distance_alies))
        self.d = (1-self.c)/self.c
        # coefs to alies func

        #parametrs for cube
        self.radiuses_array = np.linspace(0, 2000)
        self.phi_array = np.linspace(0, 180)
        self.ksy_array = np.linspace(0, 180)
        #print(self.radiuses_array, self.phi_array, self.ksy_array)
        #self.cube_of_loos = np.array(self.radiuses_array, self.phi_array, self.ksy_array)
        #parametrs for cube
        #Loss value functions
        self.loss_distance = np.float(0.0)
        self.loss_alies = np.float(0.0)
        self.loss_objects_interaction = np.float(0.0)
        self.loss_amount_in_teams = np.float(0.0)
        self.loss_of_velocity = np.float(0.0)
        self.result = np.float(0.0)

        self.r_i, self.phi_i, self.psi_i = np.int32(0), np.int32(0), np.int32(0)

    def set_congiguration(self, configuration):
        self.configuration = configuration
        if configuration:
            for key in configuration:
                for item in configuration[key]:
                    if key == ObjectType.FieldSize:
                        self.battle_field_size[0], self.battle_field_size[1] = item[0], item[1]

    def calc_loss_of_distance(self, object): #WORKED PERFECT
        self.n1[0], self.n1[1] = self.battle_field_size[0] - object[ObjectProp.Xcoord], 0
        self.n2[0], self.n2[1] = 0, self.battle_field_size[1] - object[ObjectProp.Ycoord]
        self.n3[0], self.n3[1] = -object[ObjectProp.Xcoord], 0
        self.n4[0], self.n4[1] = 0, -object[ObjectProp.Ycoord] #vectors of normal to walls

        self.dir = object[ObjectProp.Dir]
        self.vec[0], self.vec[1] = np.cos(np.radians(self.dir)), np.sin(np.radians(self.dir)) #vector of object

        self.loss_dist1, self.loss_dist2 = np.float(0.0), np.float(0.0)
        self.loss_dist3, self.loss_dist4 = np.float(0.0), np.float(0.0)

        #norm distance to every wall if that in critical range
        if (self.battle_field_size[0] - object[ObjectProp.Xcoord])/self.battle_field_size[0] < self.danger_distance_norm:
            self.dist_wall1 = (self.battle_field_size[0] - object[ObjectProp.Xcoord])/self.battle_field_size[0]
            self.loss_dist1 = (-1 / (self.dist_wall1 + self.a) + self.b) * \
                              ((self.vec[0]*self.n1[0] + self.vec[1]*self.n1[1])/
                               (np.sqrt(pow(self.vec[0], 2) + pow(self.vec[1], 2))*np.sqrt(pow(self.n1[0], 2) + pow(self.n1[1], 2))))
            if self.loss_dist1 >= 0:
                self.loss_dist1 = 0
        else:
            self.dist_wall1 = 0
            self.loss_dist1 = 0
        if (self.battle_field_size[1] - object[ObjectProp.Ycoord])/self.battle_field_size[1] < self.danger_distance_norm:
            self.dist_wall2 = (self.battle_field_size[1] - object[ObjectProp.Ycoord])/self.battle_field_size[1]
            self.loss_dist2 = (-1 / (self.dist_wall2 + self.a) + self.b) * \
                              ((self.vec[0] * self.n2[0] + self.vec[1] * self.n2[1]) /
                               (np.sqrt(pow(self.vec[0], 2) + pow(self.vec[1], 2)) * np.sqrt(
                                   pow(self.n2[0], 2) + pow(self.n2[1], 2))))
            if self.loss_dist2 >= 0:
                self.loss_dist2 = 0
        else:
            self.dist_wall2 = 0
            self.loss_dist2 = 0
        if object[ObjectProp.Xcoord]/self.battle_field_size[0] < self.danger_distance_norm:
            self.dist_wall3 = object[ObjectProp.Xcoord]/self.battle_field_size[0]
            self.loss_dist3 = (-1 / (self.dist_wall3 + self.a) + self.b) * \
                              ((self.vec[0] * self.n3[0] + self.vec[1] * self.n3[1]) /
                               (np.sqrt(pow(self.vec[0], 2) + pow(self.vec[1], 2)) * np.sqrt(
                                   pow(self.n3[0], 2) + pow(self.n3[1], 2))))
            if self.loss_dist3 >= 0:
                self.loss_dist3 = 0
        else:
            self.dist_wall3 = 0
            self.loss_dist3 = 0
        if object[ObjectProp.Ycoord]/self.battle_field_size[1] < self.danger_distance_norm:
            self.dist_wall4 = object[ObjectProp.Ycoord]/self.battle_field_size[1]
            self.loss_dist4 = (-1 / (self.dist_wall4 + self.a) + self.b) * \
                              ((self.vec[0] * self.n4[0] + self.vec[1] * self.n4[1]) /
                               (np.sqrt(pow(self.vec[0], 2) + pow(self.vec[1], 2)) * np.sqrt(
                                   pow(self.n4[0], 2) + pow(self.n4[1], 2))))
            if self.loss_dist4 >= 0:
                self.loss_dist4 = 0
        else:
            self.dist_wall4 = 0
            self.loss_dist4 = 0
        #norm distance to every wall if that in critical range
        return self.loss_dist1 + self.loss_dist2 + self.loss_dist3 + self.loss_dist4

    def calc_loss_amount_teams(self, radiant, dire): #WORKED PERFECT
        self.loss_amount_in_teams = 2*(radiant - dire)/(radiant + dire)
        #print(self.loss_amount_in_teams)
        return self.loss_amount_in_teams

    def calc_loss_of_alies_collision(self, distance):
        self.danger_distance_alies = (distance - 2 * Constants.DefaultObjectRadius) / Constants.AttackRange
        self.loss_alies = -1 / (self.danger_distance_alies + self.c) + self.d if (
                    self.danger_distance_alies < self.norm_danger_distance_alies and
                    self.danger_distance_alies != 0) else 0.0
        return self.loss_alies

    def calc_loss_of_velocity(self, velocity):
        self.loss_of_velocity = velocity / self.max_speed_of_objects
        #print(self.loss_of_velocity)
        return self.loss_of_velocity

    def calc_qstate(self, radius, phi_betw_r, psi_betw_enem):
        r_i, phi_i, psi_i = self.qstate.get_index_by_values(radius, phi_betw_r, psi_betw_enem)
        coefs_list, q_list = [], []
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for k in (-1, 0, 1):
                    new_r, new_phi, new_psi = r_i + i, phi_i + j, psi_i + k
                    if 0 <= new_r < self.n_cuts and 0 <= new_phi < self.n_cuts and 0 <= new_psi < self.n_cuts:
                        #print(new_r, new_phi, new_psi)
                        q = self.q_data[int(new_r), int(new_phi), int(new_psi)]
                        val_r, val_phi, val_psi = self.qstate.get_cell_val_by_index(new_r, new_phi, new_psi)
                        coefs_list.append([val_r, val_phi, val_psi])
                        q_list.append(q)
        params = np.array(coefs_list)
        qarr = np.array(q_list)
        coefs = np.linalg.lstsq(params, qarr, rcond=None)[0]
        val = np.dot(coefs, np.array([radius, phi_betw_r, psi_betw_enem]))
        return val

        #self.loss_objects_interaction = self.q_data[int(self.r_i), int(self.phi_i), int(self.psi_i)]
        #print(int(self.r_i), int(self.phi_i), int(self.psi_i), self.loss_objects_interaction)
        #return self.loss_objects_interaction

    def loss_result(self, object, radius, phi, psi, radiant, dire):
        dist, vel, qstate, amount = 8 * self.calc_loss_of_distance(object),  0.02 * self.calc_loss_of_velocity(object[ObjectProp.Velocity]), \
                                    0.4 * self.calc_qstate(radius, phi, psi), self.calc_loss_amount_teams(radiant, dire)
        self.result = vel + qstate + amount + dist
        if self.whoami is not None:
            self.result = vel + amount + dist - 2*qstate
        #print("dist: {}, vel: {}, qstate: {}, amount: {}".format(dist, vel, qstate, amount))
        return self.result


class QState:
    def __init__(self, n_cuts=20):
        self.cube_path = "C:\\Users\\user\\Documents\\Fly_game\\cubev2(-1).txt"
        #self.loaded_cube = np.zeros(pow(self.n_cuts, 3))
        self.range_phi = (0, 360)
        self.range_psi = (0, 360)
        self.range_r = (0, 1500)
        self.r_obj = Constants.DefaultObjectRadius
        self.attack_range = Constants.AttackRange
        self.n_cuts = n_cuts
        self.n_nearest = 30
        self.r_wide, self.psi_wide, self.phi_wide = self.range_r[1] / (self.n_cuts-1), self.range_psi[1] / (self.n_cuts-1), \
                                                    self.range_phi[1] / (self.n_cuts-1)
        self.coords = []
        self.data_arr = np.zeros((self.n_cuts, self.n_cuts, self.n_cuts))
        self.given_state_vectors = []  # [ (r, phi, psi)_1, ...
        self.give_state_q = []  # [ Q1, ... ]

        self.q_data = np.zeros((self.n_cuts, self.n_cuts, self.n_cuts))


        #self.fill_by_experiment()
        #self.fill_data_arr()
        #self.save_history_file(self.cube_path)

    def get_index_by_values(self, r, phi, psi):

        r_ind_add = 1 if r % self.r_wide > self.r_wide / 2 else 0
        r_ind = int(r // self.r_wide + r_ind_add)

        phi_ind_add = 1 if phi % self.phi_wide > self.phi_wide / 2 else 0
        phi_ind = int(phi % 360 // self.phi_wide + phi_ind_add)

        psi_ind_add = 1 if psi % self.psi_wide > self.psi_wide / 2 else 0
        psi_ind = int(psi % 360 // self.psi_wide + psi_ind_add)

        #print(r, phi % 360, psi % 360 , r_ind, phi_ind, psi_ind)
        return r_ind, phi_ind, psi_ind

    def get_cell_val_by_index(self, r_ind, phi_ind, psi_ind):
        r_cell = self.r_wide // 2 + self.r_wide * r_ind
        phi_cell = self.phi_wide // 2 + self.phi_wide * phi_ind
        psi_wide = self.psi_wide // 2 + self.psi_wide * psi_ind
        return r_cell, phi_cell, psi_wide

    def feed_data(self, state_vector, q_value):
        self.given_state_vectors.append(state_vector)
        self.give_state_q.append(q_value)

    def get_nearest(self, r, phi, psi):
        disted = []
        for point, q in zip(self.given_state_vectors, self.give_state_q):
            dist = np.linalg.norm(np.array(point) - np.array((r, phi, psi)))
            disted.append((dist, point, q))
        interest_points = sorted(disted, key=lambda x: x[0])[:self.n_nearest]
        data_out = []
        func_out = []
        for rawpoint in interest_points:
            data_out.append(rawpoint[1])
            func_out.append(rawpoint[2])
        return np.array(data_out), np.array(func_out)

    def is_near_angle(self, obj, value, accurate=15):
        if ((obj < (value + accurate)) and (obj > (value - accurate))):
            return True
        else:
            return False

    def fill_by_experiment(self):
        for r_i in range(0, self.n_cuts):
            for phi_i in range(0, self.n_cuts):
                for psi_i in range(0, self.n_cuts):
                    self.coords = self.get_cell_val_by_index(r_i, phi_i, psi_i)
                    if self.coords[0] > 4*self.attack_range:
                        self.feed_data(self.coords, 0)
                #There is best position(object in bottom cone but in different R)
                    elif self.is_near_angle(self.coords[1], 0) or self.is_near_angle(self.coords[1], 360): #за спиной
                        if self.is_near_angle(self.coords[2], 0) or self.is_near_angle(self.coords[2], 360): #сонаправлены
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 1)
                            elif self.coords[0] < 3*self.attack_range:
                                self.feed_data(self.coords, 0.7)
                            else:
                                self.feed_data(self.coords, 0.3)
                        elif self.is_near_angle(self.coords[2], 45) or self.is_near_angle(self.coords[2], 315):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.7)
                            elif self.coords[0] < 3*self.attack_range:
                                self.feed_data(self.coords, 0.5)
                            else:
                                self.feed_data(self.coords, 0.3)
                        elif self.is_near_angle(self.coords[2], 90) or self.is_near_angle(self.coords[2], 270):
                            if self.coords[0] < 3*self.r_obj:
                                self.feed_data(self.coords, -0.3)
                            elif self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.4)
                            else:
                                self.feed_data(self.coords, 0.2)
                        elif self.is_near_angle(self.coords[2], 135) or self.is_near_angle(self.coords[2], 225):
                            if self.coords[0] < 3*self.r_obj:
                                self.feed_data(self.coords, -0.5)
                            elif self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.3)
                            else:
                                self.feed_data(self.coords, 0.2)
                        elif self.is_near_angle(self.coords[2], 180):
                            if self.coords[0] < 3*self.r_obj:
                                self.feed_data(self.coords, -0.7)
                            else:
                                self.feed_data(self.coords, 0)
                        # Complete
                # Good
                    elif self.is_near_angle(self.coords[1], 45):
                        if self.is_near_angle(self.coords[2], 0) or self.is_near_angle(self.coords[2], 360):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.6)
                            else:
                                self.feed_data(self.coords, 0.4)
                        elif self.is_near_angle(self.coords[2], 45):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.8) #0.4
                            else:
                                self.feed_data(self.coords, 0.5)
                        elif self.is_near_angle(self.coords[2], 90): #same as 0
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.6) #0.3
                            else:
                                self.feed_data(self.coords, 0.4) #0.1
                        elif self.is_near_angle(self.coords[2], 135):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.4) #-0.2
                            else:
                                self.feed_data(self.coords, 0.2) #-0.1
                        elif self.is_near_angle(self.coords[2], 180):
                            self.feed_data(self.coords, 0)
                        elif self.is_near_angle(self.coords[2], 225):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.2)
                            else:
                                self.feed_data(self.coords, 0.1)
                        elif self.is_near_angle(self.coords[2], 270):
                            #if self.coords[0] < 2*self.attack_range:
                            self.feed_data(self.coords, 0)
                            #else:
                            #    self.feed_data(self.coords, 0)
                        elif self.is_near_angle(self.coords[2], 315):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.5)
                            else:
                                self.feed_data(self.coords, 0.3)
                # Neutral
                    elif self.is_near_angle(self.coords[1], 90):
                        if self.is_near_angle(self.coords[2], 0) or self.is_near_angle(self.coords[2], 360):
                            self.feed_data(self.coords, 0)
                        elif self.is_near_angle(self.coords[2], 45):
                                self.feed_data(self.coords, 0.1)
                        elif self.is_near_angle(self.coords[2], 90):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.2)
                            else:
                                self.feed_data(self.coords, 0.1)
                        elif self.is_near_angle(self.coords[2], 135):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.1)
                            else:
                                self.feed_data(self.coords, 0.08)
                        elif self.is_near_angle(self.coords[2], 180):
                            self.feed_data(self.coords, 0)
                        elif self.is_near_angle(self.coords[2], 225):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.1)
                            else:
                                self.feed_data(self.coords, -0.08)
                        elif self.is_near_angle(self.coords[2], 270):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.2)
                            else:
                                self.feed_data(self.coords, -0.1)
                        elif self.is_near_angle(self.coords[2], 315):
                            self.feed_data(self.coords, -0.1)
                # Bad
                    elif self.is_near_angle(self.coords[1], 135):
                        if self.is_near_angle(self.coords[2], 0) or self.is_near_angle(self.coords[2], 360):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.6)
                            else:
                                self.feed_data(self.coords, -0.4)
                        elif self.is_near_angle(self.coords[2], 45):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.4)
                            else:
                                self.feed_data(self.coords, -0.2)
                        elif self.is_near_angle(self.coords[2], 90):
                            #if self.coords[0] < 2*self.attack_range:
                            self.feed_data(self.coords, 0)
                            #else:
                            #    self.feed_data(self.coords, -0.2)
                        elif self.is_near_angle(self.coords[2], 135):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.1)
                        elif self.is_near_angle(self.coords[2], 180):
                            self.feed_data(self.coords, 0)
                        elif self.is_near_angle(self.coords[2], 225):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.1)
                        elif self.is_near_angle(self.coords[2], 270):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.6)
                            else:
                                self.feed_data(self.coords, -0.3)
                        elif self.is_near_angle(self.coords[2], 315):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.7)
                            elif self.coords[0] < 3*self.attack_range:
                                self.feed_data(self.coords, -0.5)
                            else:
                                self.feed_data(self.coords, -0.3)
                # Worst
                    elif self.is_near_angle(self.coords[1], 180):
                        if self.is_near_angle(self.coords[2], 0) or self.is_near_angle(self.coords[2], 360):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -1)
                            elif self.coords[0] < 3*self.attack_range:
                                self.feed_data(self.coords, -0.7)
                            else:
                                self.feed_data(self.coords, -0.3)
                        elif self.is_near_angle(self.coords[2], 45) or self.is_near_angle(self.coords[2], 315):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.7)
                            elif self.coords[0] < 4*self.attack_range:
                                self.feed_data(self.coords, -0.5)
                            else:
                                self.feed_data(self.coords, -0.3)
                        elif self.is_near_angle(self.coords[2], 90) or self.is_near_angle(self.coords[2], 270):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.4)
                            else:
                                self.feed_data(self.coords, -0.2)
                        elif self.is_near_angle(self.coords[2], 135) or self.is_near_angle(self.coords[2], 225):
                            self.feed_data(self.coords, -0.1)
                        elif self.is_near_angle(self.coords[2], 180):
                            self.feed_data(self.coords, 0)
                        #Complete
                #Bad reverse
                    elif self.is_near_angle(self.coords[1], 225):
                        if self.is_near_angle(self.coords[2], 0) or self.is_near_angle(self.coords[2], 360):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.6)
                            else:
                                self.feed_data(self.coords, -0.4)
                        elif self.is_near_angle(self.coords[2], 315):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.4)
                            else:
                                self.feed_data(self.coords, -0.2)
                        elif self.is_near_angle(self.coords[2], 270):
                            #if self.coords[0] < 2*self.attack_range:
                            self.feed_data(self.coords, 0)
                            #else:
                            #    self.feed_data(self.coords, -0.2)
                        elif self.is_near_angle(self.coords[2], 225):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.1)
                        elif self.is_near_angle(self.coords[2], 180):
                            self.feed_data(self.coords, 0)
                        elif self.is_near_angle(self.coords[2], 135):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.1)
                        elif self.is_near_angle(self.coords[2], 90):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.6)
                            else:
                                self.feed_data(self.coords, -0.3)
                        elif self.is_near_angle(self.coords[2], 45):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.7)
                            elif self.coords[0] < 3*self.attack_range:
                                self.feed_data(self.coords, -0.5)
                            else:
                                self.feed_data(self.coords, -0.3)
                #neutral reverse
                    elif self.is_near_angle(self.coords[1], 270):
                        if self.is_near_angle(self.coords[2], 0) or self.is_near_angle(self.coords[2], 360):
                            self.feed_data(self.coords, 0)
                        elif self.is_near_angle(self.coords[2], 315):
                                self.feed_data(self.coords, 0.1)
                        elif self.is_near_angle(self.coords[2], 270):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.2)
                            else:
                                self.feed_data(self.coords, 0.1)
                        elif self.is_near_angle(self.coords[2], 225):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.1)
                            else:
                                self.feed_data(self.coords, 0.08)
                        elif self.is_near_angle(self.coords[2], 180):
                            self.feed_data(self.coords, 0)
                        elif self.is_near_angle(self.coords[2], 135):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.1)
                            else:
                                self.feed_data(self.coords, -0.08)
                        elif self.is_near_angle(self.coords[2], 90):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, -0.2)
                            else:
                                self.feed_data(self.coords, -0.1)
                        elif self.is_near_angle(self.coords[2], 45):
                            self.feed_data(self.coords, -0.1)
                #good reverse
                    elif self.is_near_angle(self.coords[1], 315):
                        if self.is_near_angle(self.coords[2], 0) or self.is_near_angle(self.coords[2], 360):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.6)
                            else:
                                self.feed_data(self.coords, 0.4)
                        elif self.is_near_angle(self.coords[2], 315):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.8)
                            else:
                                self.feed_data(self.coords, 0.5)
                        elif self.is_near_angle(self.coords[2], 270):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.6)
                            else:
                                self.feed_data(self.coords, 0.4)
                        elif self.is_near_angle(self.coords[2], 225):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.4)
                            else:
                                self.feed_data(self.coords, 0.2)
                        elif self.is_near_angle(self.coords[2], 180):
                            self.feed_data(self.coords, 0)
                        elif self.is_near_angle(self.coords[2], 135):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.2)
                            else:
                                self.feed_data(self.coords, 0.1)
                        elif self.is_near_angle(self.coords[2], 90):
                            #if self.coords[0] < 2*self.attack_range:
                            self.feed_data(self.coords, 0)
                            #else:
                            #    self.feed_data(self.coords, 0.3)
                        elif self.is_near_angle(self.coords[2], 45):
                            if self.coords[0] < 2*self.attack_range:
                                self.feed_data(self.coords, 0.5)
                            else:
                                self.feed_data(self.coords, 0.3)

    def fill_data_arr(self):
        for r_i in range(0, self.n_cuts):
            for phi_i in range(0, self.n_cuts):
                for psi_i in range(0, self.n_cuts):
                    nearest_coords = self.get_cell_val_by_index(r_i, phi_i, psi_i)
                    nearest_points, nearest_vals = self.get_nearest(*nearest_coords)
                    coefs = np.linalg.lstsq(nearest_points, nearest_vals, rcond=None)[0]
                    val = np.dot(coefs, nearest_coords)
                    print(val, (r_i*100+phi_i*10+psi_i)/self.n_cuts, '% completed fill cube')
                    self.data_arr[r_i, phi_i, psi_i] = val


    def load_history_file(self, file, q_data):
        with open(file, 'r') as fd:
            state_str = fd.readlines()
        strind = 0
        for line in state_str:
            numsback_str = line.split(',')
            indexes = self.get_index_by_values(int(numsback_str[0]), int(numsback_str[1]), int(numsback_str[2]))
            q_data[indexes[0], indexes[1], indexes[2]] = float(numsback_str[3])
            strind += 1

    def save_history_file(self, file_name):
        q_str = ''
        for r_i in range(0, self.n_cuts):
            for phi_i in range(0, self.n_cuts):
                for psi_i in range(0, self.n_cuts):
                    nearest_coords = self.get_cell_val_by_index(r_i, phi_i, psi_i)
                    q_str += '{0},{1},{2},{3}\n'.format(int(nearest_coords[0]), int(nearest_coords[1]), int(nearest_coords[2]), self.data_arr[r_i, phi_i, psi_i])
        q_str = q_str[:-1]
        with open(file_name, 'w') as f:
            f.write(q_str + '\n')


def calc_polar_grid(self, objects, width, height, step_number=16, player_number=13, max_range=605):
    self.steps = [25, 35, 45, 65, 85, 105, 155, 205, 255, 305, 355, 405, 455, 505, 555, 605]
    self.player = objects[player_number]
    if self.player[ObjectProp.ObjType] == ObjectType.Absent:
        return
    self.polar_grid = np.zeros((step_number + 1, step_number))  # fi , range
    self.max_range = max_range
    self._dir = self.player[ObjectProp.Dir] - 90 if self.player[ObjectProp.Dir] >= 90 \
                                                else 270 + self.player[ObjectProp.Dir]

    for _step in range(0, step_number):
        self.current_angle = _step * 360 / step_number*np.pi/180 # проходим по уголу
        self.current_angle += (self._dir - 90)*np.pi/180
        if self.current_angle > 360 * np.pi / 180:
            self.current_angle -= 360 * np.pi / 180
        if self.current_angle < 0:
            self.current_angle += 360 * np.pi / 180
        if self.current_angle*180/np.pi >= 0 and self.current_angle*180/np.pi <= 90:
            self.h = height - self.player[ObjectProp.Ycoord], width - self.player[ObjectProp.Xcoord]
        elif self.current_angle *180/np.pi >= 90 and self.current_angle *180/np.pi <= 180:
            self.h = height - self.player[ObjectProp.Ycoord], self.player[ObjectProp.Xcoord]
        elif self.current_angle*180/np.pi >= 180 and self.current_angle*180/np.pi <= 270:
            self.h = self.player[ObjectProp.Ycoord], self.player[ObjectProp.Xcoord]
        elif self.current_angle*180/np.pi >= 270 and self.current_angle*180/np.pi <= 360:
            self.h = self.player[ObjectProp.Ycoord], width - self.player[ObjectProp.Xcoord]
        self.current_range_to_wall = min(
            self.h[0] / abs(np.sin(self.current_angle)+Constants.epsilon),
            self.h[1] / abs(np.cos(self.current_angle)+Constants.epsilon))

        #print("self.current_range_to_wall = ",self.current_range_to_wall, " _step = ", _step)

        #print(self.current_angle * 180 / np.pi, "   ", self.h)

        self.next_angle = 0 if _step == step_number - 1 else (_step + 1) * 360 / step_number * np.pi / 180  # проходим по уголу
        self.next_angle += (self._dir - 90)*np.pi/180
        if self.next_angle > 360 * np.pi / 180:
            self.next_angle -= 360 * np.pi / 180
        if self.current_angle < 0:
            self.current_angle += 360 * np.pi / 180
        if self.next_angle * 180 / np.pi >= 0 and self.next_angle * 180 / np.pi <= 90:
            self.h = height - self.player[ObjectProp.Ycoord], width - self.player[ObjectProp.Xcoord]
        elif self.next_angle * 180 / np.pi >= 90 and self.next_angle * 180 / np.pi <= 180:
            self.h = height - self.player[ObjectProp.Ycoord], self.player[ObjectProp.Xcoord]
        elif self.next_angle * 180 / np.pi >= 180 and self.next_angle * 180 / np.pi <= 270:
            self.h = self.player[ObjectProp.Ycoord], self.player[ObjectProp.Xcoord]
        elif self.next_angle * 180 / np.pi >= 270 and self.next_angle * 180 / np.pi <= 360:
            self.h = self.player[ObjectProp.Ycoord], width - self.player[ObjectProp.Xcoord]
        self.next_range_to_wall = min(
            self.h[0] / abs(np.sin(self.next_angle) + Constants.epsilon),
            self.h[1] / abs(np.cos(self.next_angle) + Constants.epsilon))
        #print(self.current_angle * 180 / np.pi, "   ", self.h)

        self.current_range_to_wall = int(min(self.current_range_to_wall, self.next_range_to_wall))

        current_discrete_range_to_wall = step_number
        for i in range(0, step_number):
            if self.current_range_to_wall < self.steps[i]:
                current_discrete_range_to_wall = i
                break

        #self.current_discrete_range_to_wall = int(self.current_range_to_wall * step_number / self.max_range)
        #print(self.current_range_to_wall, step_number)
        #if self.current_discrete_range_to_wall > step_number:
        #    self.current_discrete_range_to_wall = step_number
        #print(self.current_range_to_wall, self.current_discrete_range_to_wall)
        for r in range(current_discrete_range_to_wall, step_number+1):
            #print(step_number , r)
            self.polar_grid[step_number - r][_step] = -1
        #print(self.player[ObjectProp.Xcoord], self.player[ObjectProp.Ycoord], self.current_range_to_wall, "  ",_step)

    for index in range(0, ObjectType.ObjArrayTotal):
        if objects[index][ObjectProp.ObjType] != ObjectType.Absent and index != player_number:
            self.another_x = objects[index][ObjectProp.Xcoord] - self.player[ObjectProp.Xcoord]
            self.another_y = objects[index][ObjectProp.Ycoord] - self.player[ObjectProp.Ycoord]
            self.fi = np.arctan2(self.another_y, self.another_x) * 180 / np.pi
            self.fi -= (self._dir - 90)
            if self.fi > 360:
                self.fi -= 360
            self.fi_discrete = int(self.fi*step_number/360) if self.fi >= 0 else step_number - 1 + int(self.fi*step_number/360)
            self.range = int(np.sqrt(self.another_x**2+self.another_y**2))
            for i in range(0, step_number):
                if self.range < self.steps[i]:
                    self.range_discrete = i
                    break
            if self.range > self.max_range:
                self.range_discrete = step_number

            self.polar_grid[step_number - self.range_discrete][self.fi_discrete] = objects[index][ObjectProp.ObjType] \
                if self.polar_grid[step_number - self.range_discrete][self.fi_discrete] == -1 else\
                    self.polar_grid[step_number - self.range_discrete][self.fi_discrete]*10 +\
                    objects[index][ObjectProp.ObjType]
    #print(self.polar_grid)

