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
        self.max_speed_of_objects = 400

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
        self.loss_objects_interaction = np.float(0.0)
        self.loss_amount_in_teams = np.float(0.0)
        self.loss_of_velocity = np.float(0.0)

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

    def calc_loss_of_velocity(self, velocity):
        self.loss_of_velocity = velocity / self.max_speed_of_objects
        #print(self.loss_of_velocity)

    def calc_qstate(self, radius, phi_betw_r, psi_betw_enem):
        r_i, phi_i, psi_i = self.qstate.get_index_by_values(radius, phi_betw_r, psi_betw_enem)
        self.loss_objects_interaction = self.qstate.data_arr[int(r_i), int(phi_i), int(psi_i)]
        #print(self.loss_objects_interaction)


class QState:
    def __init__(self):
        self.range_phi = (0, 360)
        self.range_psi = (0, 360)
        self.range_r = (0, 1500)
        self.r_obj = Constants.DefaultObjectRadius
        self.attack_range = Constants.AttackRange
        self.n_cuts = 10
        self.n_nearest = 30
        self.r_wide, self.psi_wide, self.phi_wide = self.range_r[1] // self.n_cuts, self.range_psi[1] // self.n_cuts, \
                                                    self.range_phi[1] // self.n_cuts
        self.data_arr = np.zeros((self.n_cuts, self.n_cuts, self.n_cuts))
        self.given_state_vectors = []  # [ (r, phi, psi)_1, ... ]
        self.give_state_q = []  # [ Q1, ... ]

        #self.fill_by_experiment()
        #self.fill_data_arr()


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

    def is_near_angle(self, obj, value, accurate=10):
        return ((obj < (value + accurate)) or (obj > (value - accurate)))

    def fill_by_experiment(self):
        for r_i in range(0, self.n_cuts):
            for phi_i in range(0, self.n_cuts):
                for psi_i in range(0, self.n_cuts):
                    coords = self.get_cell_val_by_index(r_i, phi_i, psi_i)
                    #print(coords)
                    if coords[0] > self.range_r[1]:
                        self.feed_data(coords, 0)
                    elif coords[0] < self.r_obj:
                        self.feed_data(coords, -0.5)
                    elif self.is_near_angle(coords[2], 180):
                        self.feed_data(coords, -0.1)
                    #There is best position(object in bottom cone but in different R)
                    elif self.is_near_angle(coords[1], 0, 20) and self.is_near_angle(coords[2], 0, 20):
                        if coords[0] < self.attack_range:
                            self.feed_data(coords, 1)
                        elif coords[0] < 4*self.attack_range:
                            self.feed_data(coords, 0.5)
                        elif coords[0] < 8*self.attack_range:
                            self.feed_data(coords, 0.2)
                        else:
                            self.feed_data(coords, 0)
                    #There is good position
                    elif self.is_near_angle(coords[1], 45, 15) and self.is_near_angle(coords[2], 45, 15):
                        if coords[0] < self.attack_range:
                            self.feed_data(coords, 0.7)
                        elif coords[0] < 4*self.attack_range:
                            self.feed_data(coords, 0.3)
                        elif coords[0] < 8*self.attack_range:
                            self.feed_data(coords, 0.05)
                        else:
                            self.feed_data(coords, 0)
                    #There is neutral position
                    elif self.is_near_angle(coords[1], 90, 20):
                        if self.is_near_angle(coords[2], 90, 20):
                            self.feed_data(coords, 0)
                        elif self.is_near_angle(coords[2], 45, 20):
                            self.feed_data(coords, 0.2)
                        elif self.is_near_angle(coords[2], 135, 20):
                            self.feed_data(coords, -0.2)
                    #There is bad position
                    elif self.is_near_angle(coords[1], 135, 20):
                        if self.is_near_angle(coords[2], 90, 20):
                            self.feed_data(coords, 0)
                        elif self.is_near_angle(coords[2], 45, 20):
                            self.feed_data(coords, -0.3)
                        elif self.is_near_angle(coords[2], 135, 20):
                            self.feed_data(coords, 0.3)
                    #There is worst position
                    elif self.is_near_angle(coords[1], 180, 15):
                        if self.is_near_angle(coords[2], 0, 15):
                            self.feed_data(coords, -1)
                        elif self.is_near_angle(coords[2], 45, 20):
                            self.feed_data(coords, -0.5)
                        elif self.is_near_angle(coords[2], 90, 20):
                            self.feed_data(coords, -0.3)
                        elif self.is_near_angle(coords[2], 135, 20):
                            self.feed_data(coords, -0.1)

    def fill_data_arr(self):
        for r_i in range(0, self.n_cuts):
            for phi_i in range(0, self.n_cuts):
                for psi_i in range(0, self.n_cuts):
                    nearest_coords = self.get_cell_val_by_index(r_i, phi_i, psi_i)
                    nearest_points, nearest_vals = self.get_nearest(*nearest_coords)
                    coefs = np.linalg.lstsq(nearest_points, nearest_vals, rcond=None)[0]
                    val = np.dot(coefs, nearest_coords)
                    #print(val, (r_i*100+phi_i*10+psi_i)/10, '% completed fill cube')
                    self.data_arr[r_i, phi_i, psi_i] = val








def calc_polar_grid(self, objects, width, height, step_number=16, player_number=0, max_range=600):
    import pyglet
    self.player = objects[player_number]
    if self.player[ObjectProp.ObjType] == ObjectType.Absent:
        return
    self.polar_grid = np.zeros((step_number, step_number + 1))  # fi , range
    self.max_range = max_range
    self._dir = self.player[ObjectProp.Dir] - 90 if self.player[ObjectProp.Dir] >= 90 \
                                                else 270 + self.player[ObjectProp.Dir]

    for _step in range(0, step_number):
        self.current_angle = _step * 360 / step_number*np.pi/180 # проходим по уголу
        self.current_angle += self._dir*np.pi/180
        if self.current_angle > 360 * np.pi / 180:
            self.current_angle -= 360 * np.pi / 180
        if self.current_angle*180/np.pi >= 0 and self.current_angle*180/np.pi <= 90:
            self.h = height - self.player[ObjectProp.Ycoord], width - self.player[ObjectProp.Xcoord]
        elif self.current_angle *180/np.pi >= 90 and self.current_angle *180/np.pi <= 180:
            self.h = height - self.player[ObjectProp.Ycoord], self.player[ObjectProp.Xcoord]
        elif self.current_angle*180/np.pi >= 180 and self.current_angle*180/np.pi <= 270:
            self.h = self.player[ObjectProp.Ycoord], self.player[ObjectProp.Xcoord]
        elif self.current_angle*180/np.pi >= 270 and self.current_angle*180/np.pi <= 360:
            self.h = self.player[ObjectProp.Ycoord], width - self.player[ObjectProp.Xcoord]
        self.current_range_to_wall = min(
            self.h[0] / abs(np.sin(self.current_angle)+self.epsilon),
            self.h[1] / abs(np.cos(self.current_angle)+self.epsilon))

        #print("self.current_range_to_wall = ",self.current_range_to_wall, " _step = ", _step)
        #print(self.current_angle*180/np.pi,"   ",self.h)

        self.next_angle = 0 if _step == step_number - 1 else (_step + 1) * 360 / step_number * np.pi / 180  # проходим по уголу
        self.next_angle += self._dir*np.pi/180
        if self.next_angle > 360 * np.pi / 180:
            self.next_angle -= 360 * np.pi / 180
        if self.next_angle * 180 / np.pi >= 0 and self.next_angle * 180 / np.pi <= 90:
            self.h = height - self.player[ObjectProp.Ycoord], width - self.player[ObjectProp.Xcoord]
        elif self.next_angle * 180 / np.pi >= 90 and self.next_angle * 180 / np.pi <= 180:
            self.h = height - self.player[ObjectProp.Ycoord], self.player[ObjectProp.Xcoord]
        elif self.next_angle * 180 / np.pi >= 180 and self.next_angle * 180 / np.pi <= 270:
            self.h = self.player[ObjectProp.Ycoord], self.player[ObjectProp.Xcoord]
        elif self.next_angle * 180 / np.pi >= 270 and self.next_angle * 180 / np.pi <= 360:
            self.h = self.player[ObjectProp.Ycoord], width - self.player[ObjectProp.Xcoord]
        self.next_range_to_wall = min(
            self.h[0] / abs(np.sin(self.next_angle) + self.epsilon),
            self.h[1] / abs(np.cos(self.next_angle) + self.epsilon))

        self.current_range_to_wall = min(self.current_range_to_wall , self.next_range_to_wall)
        self.current_discrete_range_to_wall = int(self.current_range_to_wall * step_number / max_range)
        if self.current_discrete_range_to_wall > step_number:
            self.current_discrete_range_to_wall = step_number
        for r in range(self.current_discrete_range_to_wall, step_number+1):
            self.polar_grid[_step][r] = -1
        #print(self.player[ObjectProp.Xcoord], self.player[ObjectProp.Ycoord], self.current_range_to_wall, "  ",_step)

    for index in range(0, ObjectType.ObjArrayTotal):
        if objects[index][ObjectProp.ObjType] != ObjectType.Absent and index != player_number:
            self.another_x = objects[index][ObjectProp.Xcoord] - self.player[ObjectProp.Xcoord]
            self.another_y = objects[index][ObjectProp.Ycoord] - self.player[ObjectProp.Ycoord]
            self.fi = np.arctan2(self.another_y, self.another_x) * 180 / np.pi
            self.fi -= self._dir
            if self.fi > 360:
                self.fi -= 360
            self.fi_discrete = int(self.fi*step_number/360) if self.fi >= 0 else step_number - 1 + int(self.fi*step_number/360)
            self.range_discrete = int(np.sqrt(self.another_x**2+self.another_y**2)*step_number/self.max_range)
            if self.range_discrete > step_number - 1:
                self.range_discrete = step_number

            self.polar_grid[self.fi_discrete][self.range_discrete] = objects[index][ObjectProp.ObjType] \
                if self.polar_grid[self.fi_discrete][self.range_discrete] == -1 else\
                    self.polar_grid[self.fi_discrete][self.range_discrete]*10 +\
                    objects[index][ObjectProp.ObjType]
    #print(self.polar_grid)
    self.x0 = 1000
    self.y0 = 990
    self.dx = 29
    self.dy = 25
    self.draw = True
    for i in range(0,step_number):
        for j in range(0, step_number+1):
            color = [255, 255, 255, 255] * 4
            points = (self.x0 + j * self.dx, self.y0 - i * self.dy - self.dy,
                      self.x0 + j * self.dx, self.y0 - i * self.dy,
                      self.x0 + j * self.dx + self.dx, self.y0 - i * self.dy,
                      self.x0 + j * self.dx + self.dx, self.y0 - i * self.dy - self.dy)
            if self.polar_grid[i][j] == -1:
                color = [0, 0, 0, 255] * 4
            if self.polar_grid[i][j] == 5:
                color = [0, 0, 255, 255] * 4
            if self.polar_grid[i][j] == 3:
                color = [255, 0, 255, 255] * 4
            if self.polar_grid[i][j] == 2:
                color = [255, 0, 0, 255] * 4

            pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                                 ('v2i', points),
                                 ('c4B', color))

            if i == 0 and self.draw:
                self._range = str(j) if j < step_number else 'inf'
                label = pyglet.text.Label(self._range,
                                          font_name='Times New Roman',
                                          font_size=16,
                                          x=self.x0 + self.dx * j + self.dx//2,
                                          y=self.y0 - self.dy * step_number - self.dy//2,
                                          anchor_x='center', anchor_y='center')
                label.draw()
        if self.draw:
            label = pyglet.text.Label(str(360*i/step_number),
                                      font_name='Times New Roman',
                                      font_size=16,
                                      x = self.x0 - self.dx,
                                      y = self.y0 - self.dy * i - self.dy//2,
                                      anchor_x='center', anchor_y='center')
            label.draw()
    self.draw = False
