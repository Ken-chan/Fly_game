import numpy as np
from obj_def import *

class Loss():
    def __init__(self, configuration):
        self.configuration = None
        self.battle_field_size = np.array([0.0, 0.0])
        self.set_congiguration(configuration)

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

    def make_4D_square(self):
        #self.r
        pass


    def calc_point_in_squad(self, cube):
        pass




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
