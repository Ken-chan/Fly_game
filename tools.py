import numpy as np
from obj_def import *

class Loss():
    def __init__(self, configuration):
        self.configuration = None
        self.battle_field_size = np.array([0.0, 0.0])
        self.set_congiguration(configuration)
        self.qstate = QState()

        self.min_x = np.float(0.0)
        self.min_y = np.float(0.0)
        self.norm_min_distance = np.float(0.0)
        self.danger_distance_norm = np.float(0.1) #critical distance to danger objects(normalize)

        #coefs to distance func
        self.a = 0.5*(-self.danger_distance_norm + np.sqrt(self.danger_distance_norm**2 + 4*self.danger_distance_norm))
        self.b = (1-self.a)/self.a
        #coefs to distance func
        #parametrs for cube
        self.radiuses_array = np.linspace(0, 2000)
        self.phi_array = np.linspace(0, 180)
        self.ksy_array = np.linspace(0, 180)
        #print(self.radiuses_array, self.phi_array, self.ksy_array)
        #self.cube_of_loos = np.array(self.radiuses_array, self.phi_array, self.ksy_array)
        #parametrs for cube
        #Loss value functions
        self.loss_distance = np.float(0.0)
        self.loss_distance_enemy = np.float(0.0)
        self.loss_distance_comrade = np.float(0.0)
        self.loss_amount_in_teams = np.float(0.0)

    def set_congiguration(self, configuration):
        self.configuration = configuration
        if configuration:
            for key in configuration:
                for item in configuration[key]:
                    if key == ObjectType.FieldSize:
                        self.battle_field_size[0], self.battle_field_size[1] = item[0], item[1]

    def calc_loss_of_distance(self, object): #WORKED PERFECT
        if object[ObjectProp.Xcoord] <= np.fabs(self.battle_field_size[0] - object[ObjectProp.Xcoord]):
            self.min_x = object[ObjectProp.Xcoord]
        else:
            self.min_x = np.fabs(self.battle_field_size[0] - object[ObjectProp.Xcoord])
        if object[ObjectProp.Ycoord] <= np.fabs(self.battle_field_size[1] - object[ObjectProp.Ycoord]):
            self.min_y = object[ObjectProp.Ycoord]
        else:
            self.min_y = np.fabs(self.battle_field_size[1] - object[ObjectProp.Ycoord])

        if self.min_x <= self.min_y:
            self.norm_min_distance = self.min_x / self.battle_field_size[0] #normalize distance to field size
        else:
            self.norm_min_distance = self.min_y / self.battle_field_size[1]

        self.loss_distance = -1/(self.norm_min_distance + self.a) + self.b if (self.norm_min_distance < self.danger_distance_norm and
                                                                               self.norm_min_distance != 0) else 0.0
        #print(self.loss_distance, '<- loss function of distance to walls')

    def calc_loss_amount_teams(self, radiant, dire): #WORKED PERFECT
        self.loss_amount_in_teams = 2*(radiant - dire)/(radiant + dire)
        #print(self.loss_amount_in_teams)

    def calc_qstate(self, radius, phi_betw_r, psi_betw_enem):
        r_i, phi_i, psi_i = self.qstate.get_index_by_values(radius, phi_betw_r, psi_betw_enem)
        return self.qstate.data_arr[int(r_i), int(phi_i), int(psi_i)]


class QState:
    def __init__(self):
        self.range_phi = (0, 360)
        self.range_psi = (0, 360)
        self.range_r = (0, 1500)
        self.R_obj = Constants.DefaultObjectRadius
        self.Attack_range = Constants.AttackRange
        self.n_cuts = 6
        self.n_nearest = 30
        self.r_wide, self.psi_wide, self.phi_wide = self.range_r[1] // self.n_cuts, self.range_psi[1] // self.n_cuts, \
                                                    self.range_phi[1] // self.n_cuts
        self.data_arr = np.zeros((self.n_cuts, self.n_cuts, self.n_cuts))
        self.given_state_vectors = []  # [ (r, phi, psi)_1, ... ]
        self.give_state_q = []  # [ Q1, ... ]

        self.fill_by_experiment()
        #print(self.given_state_vectors, self.give_state_q)
        self.fill_data_arr()


    def get_index_by_values(self, r, phi, psi):
        r_ind = r // (self.range_r[1] // self.n_cuts)
        phi_ind = phi % 360 // (self.range_phi[1] // self.n_cuts)
        psi_ind = psi % 360 // (self.range_psi[1] // self.n_cuts)
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

    def is_near(self, obj, value, accurate = 10):
        return ((obj < (value + accurate)) or (obj > (value - accurate)))

    def fill_by_experiment(self):
        for r_i in range(0, self.n_cuts):
            for phi_i in range(0, self.n_cuts):
                for psi_i in range(0, self.n_cuts):
                    coords = self.get_cell_val_by_index(r_i, phi_i, psi_i)
                    # r, phi, psi = coords[0], coords[1], coords[2]
                    #for Radius experiments
                    if coords[0] < 2*self.R_obj:
                        self.feed_data(coords, -1)
                    elif coords[0] < 4 * self.R_obj:
                        self.feed_data(coords, 0)
                    elif coords[0] < 7 * self.R_obj and self.is_near(coords[1], 0, 40):
                        self.feed_data(coords, 1)
                    elif coords[0] < self.Attack_range:
                        self.feed_data(coords, 0.5)
                    elif coords[0] > 1300: ##uslovno
                        self.feed_data(coords, 0)

                    # For Phi (angle between object and Radius) Experimence
                    elif self.is_near(coords[1], 0, 30) and self.is_near(coords[2], 45, 15):
                        self.feed_data(coords, 0.5)
                    elif self.is_near(coords[1], 180, 15):
                        if self.is_near(coords[2], 0):
                            self.feed_data(coords, -0.5)
                        elif self.is_near(coords[2], 180, 15):
                            self.feed_data(coords, 0)
                    elif self.is_near(coords[1], 90, 20):
                        self.feed_data(coords, 0)
                    elif self.is_near(coords[1], 135, 20) and self.is_near(coords[2], 45, 15):
                        self.feed_data(coords, -0.5)
                    elif self.is_near(coords[1], coords[2]):
                        self.feed_data(coords, 0.2)

                    # For Psi (Difference between our and enemy directions) Experimence

    def fill_data_arr(self):
        for r_i in range(0, self.n_cuts):
            for phi_i in range(0, self.n_cuts):
                for psi_i in range(0, self.n_cuts):
                    nearest_coords = self.get_cell_val_by_index(r_i, phi_i, psi_i)
                    nearest_points, nearest_vals = self.get_nearest(*nearest_coords)
                    coefs = np.linalg.lstsq(nearest_points, nearest_vals)[0]
                    val = np.dot(coefs, nearest_coords)
                    print(val, (r_i*100+phi_i*10+psi_i)/10, '% completed fill cube')
                    self.data_arr[r_i, phi_i, psi_i] = val





