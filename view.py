import pyglet
from obj_def import *
from tools import calc_polar_grid, Loss
from PIL import Image, ImageDraw

class RendererState:
    Start, Pause, Game, Menu, Exit = range(5)

class Renderer:
    def __init__(self, screen_width, screen_height, battle_field_size):
        self.renderer_state = RendererState.Start
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.objects_copy = None
        self.battle_field_width = battle_field_size[0]
        self.battle_field_height = battle_field_size[1]
        self.scaling_factor = np.float(0.0)

        self.objects_sprites = None
        self.cone_sprites = None
        self.rev_cone_sprites = None
        self.new_obj_sprite = None
        self.cone, self.rev_cone = None, None
        self.objects_type = None
        self.current_object = None
        self.size_proportion_width = np.float(0.0)
        self.size_proportion_height = np.float(0.0)
        #self.loss_function = Loss()
        self.x0 = 980
        self.y0 = 1000
        self.dx = 31
        self.dy = 25

        self.step_number = 16
        self.polar_grid = np.zeros((self.step_number, self.step_number + 1))
        self._polar_grid = False                    ### changeable
        self.recalc = 1
        self.draw = True
        self.pil_img = None
        self.pil_img_sprite = None

        self.batch = pyglet.graphics.Batch()
        #self.fl_label = pyglet.text.Label("оценка функции полезности: ",
        #                                  font_name='Times New Roman',
        #                                  font_size=16,
        #                                  color=((0, 0, 0, 255)),
        #                                  x=self.x0 + 30,
        #                                  y=self.y0 - self.dy * 19,
        #                                  anchor_x='left', anchor_y='top', batch=self.batch)
        #self.fl_label.visible = False

        self.init_sprites()
        self.renderer_state = RendererState.Game

    def init_sprites(self):
        self.objects_sprites = []
        self.cone_sprites = []
        self.rev_cone_sprites = []
        self.labels = []
        self.scaling_factor = self.screen_width / self.battle_field_width

        for index in range(0, ObjectType.ObjArrayTotal):
            self.objects_type = ObjectType.type_by_id(index)

            self.new_obj_sprite = Sprite(object=self.objects_type, batch=self.batch)
            self.cone = Sprite(ObjectType.Cone_sprite, batch=self.batch)
            self.rev_cone = Sprite(ObjectType.Cone_sprite, batch=self.batch)

            self.objects_sprites.append(self.new_obj_sprite)
            self.rev_cone_sprites.append(self.rev_cone)
            self.cone_sprites.append(self.cone)


    def show_polar_grid(self):
        self._polar_grid = False if self._polar_grid else True

    def update_objects(self, objects):
        self.objects_copy = objects

    def update_graphics(self):
        if self.renderer_state == RendererState.Game and self.objects_copy is not None:
            for index in range(0, len(self.objects_sprites)):
                if self.objects_copy[index][ObjectProp.ObjType] == ObjectType.Absent:
                    self.objects_sprites[index].visible = False
                    self.cone_sprites[index].visible = False
                    self.rev_cone_sprites[index].visible = False
                else:
                    self.objects_sprites[index].visible = True
                    self.cone_sprites[index].visible = True
                    self.rev_cone_sprites[index].visible = False
                    self.current_object = self.objects_copy[index]
                    self.size_proportion_width = self.screen_width / self.battle_field_width
                    self.size_proportion_height = self.screen_height / self.battle_field_height
                    # size_proportion_dir = self.screen_width / self.screen_height

                    self.objects_sprites[index].update(x=self.size_proportion_width * (self.current_object[ObjectProp.Xcoord]),
                                                       y=self.size_proportion_height * (self.current_object[ObjectProp.Ycoord]),
                                                       rotation= -self.current_object[ObjectProp.Dir])

                    self.cone_sprites[index].update(x=self.size_proportion_width * (self.current_object[ObjectProp.Xcoord]),
                                                        # 100 * np.cos(-np.radians(current_object[ObjectProp.Dir]))),
                                                        # This, to move center of cone on the bottom of objects
                                                    y=self.size_proportion_height * (self.current_object[ObjectProp.Ycoord]),
                                                        # 100 * np.sin(-np.radians(current_object[ObjectProp.Dir]))),
                                                        # Do not need this, cause of make anchors
                                                    rotation=-self.current_object[ObjectProp.Dir])

                    self.rev_cone_sprites[index].update(x=self.size_proportion_width * (self.current_object[ObjectProp.Xcoord]),
                                                        y=self.size_proportion_height * (self.current_object[ObjectProp.Ycoord]),
                                                        rotation=-self.current_object[ObjectProp.Dir] + 180)

            if self._polar_grid:
                if self.recalc == 1:
                    self.recalc = 0
                    calc_polar_grid(self, self.objects_copy, self.battle_field_width, self.battle_field_height)
                    for label in self.labels:
                        label.visible = True
                    img = Image.new('RGB',(self.dx*self.step_number,self.dy*(self.step_number+1)), (255,255,255))
                    draw = ImageDraw.Draw(img)
                    for i in range(0, self.step_number + 1):
                        for j in range(0, self.step_number):
                            if self.polar_grid[self.step_number - i][self.step_number - j - 1] == -1:
                                draw.rectangle([(j * self.dx, i * self.dy),
                                                (j * self.dx + self.dx, i * self.dy + self.dy)],
                                               fill=(0, 0, 0))
                            if self.polar_grid[self.step_number - i][self.step_number - j - 1] == 5:
                                draw.rectangle([(j * self.dx, i * self.dy),
                                                (j * self.dx + self.dx, i * self.dy + self.dy)],
                                               fill=(0, 0, 255))
                            if self.polar_grid[self.step_number - i][self.step_number - j - 1] == 3:
                                draw.rectangle([(j * self.dx, i * self.dy),
                                                (j * self.dx + self.dx, i * self.dy + self.dy)],
                                               fill=(255, 0, 255))
                            if self.polar_grid[self.step_number - i][self.step_number - j - 1] == 2:
                                draw.rectangle([(j * self.dx, i * self.dy),
                                                (j * self.dx + self.dx, i * self.dy + self.dy)],
                                               fill=(255,0,0))

                        if self.draw:
                            self._range = str(self.step_number - i) if i != 0 else 'inf'
                            label = pyglet.text.Label(self._range,
                                                      font_name='Times New Roman',
                                                      font_size=16,
                                                      color=(0, 0, 0, 255),
                                                      x=self.x0 - self.dx,
                                                      y=self.y0 - self.dy * i - self.dy // 3,
                                                      anchor_x='left', anchor_y='top', batch=self.batch)
                            self.labels.append(label)
                            if i//2 == i/2:
                                label = pyglet.text.Label(str(int(360*i/self.step_number - 180)),# pi = '\u03C0'
                                                          font_name='Times New Roman',
                                                          font_size=16,
                                                          x=self.x0 + self.dx * i,
                                                          color=(0, 0, 0, 255),
                                                          y=self.y0 - self.dy * self.step_number - 3 * self.dy // 2,
                                                          anchor_x='center', anchor_y='top', batch=self.batch)
                                self.labels.append(label)

                    obj, enemy = self.objects_copy[0], self.objects_copy[1]
                    diff_vector = np.array([enemy[ObjectProp.Xcoord] - obj[ObjectProp.Xcoord], enemy[ObjectProp.Ycoord] - obj[ObjectProp.Ycoord]])
                    dir2 = enemy[ObjectProp.Dir]
                    vec2 = np.array([np.cos(np.radians(dir2)), np.sin(np.radians(dir2))])
                    distance = np.linalg.norm(diff_vector)
                    arr_dir = np.array([enemy[ObjectProp.Xcoord] - obj[ObjectProp.Xcoord], enemy[ObjectProp.Ycoord] - obj[ObjectProp.Ycoord]])
                    arr_dir = arr_dir / np.linalg.norm(arr_dir)
                    obj_dir = np.array([np.cos(np.radians(obj[ObjectProp.Dir])), np.sin(np.radians(obj[ObjectProp.Dir]))])
                    arr_turned = np.array([arr_dir[0]*obj_dir[0] + arr_dir[1]*obj_dir[1], arr_dir[0]*obj_dir[1] - arr_dir[1]*obj_dir[0]])
                    #angle_between_radius = 180 - np.degrees(np.arccos((diff_vector[0] * vec2[0] + diff_vector[1] * vec2[1]) / ((np.sqrt(pow(diff_vector[0], 2) + pow(diff_vector[1], 2))) * (np.sqrt(pow(vec2[0], 2) + pow(vec2[1], 2)))))) if (diff_vector[0] != 0 and vec2[0] != 0) else 0
                    angle_between_radius = np.degrees(np.arccos(arr_turned[0]))
                    if arr_turned[1] < 0:
                        angle_between_radius = 360- angle_between_radius
                    #if (diff_vector[0] * vec2[1] - diff_vector[1] * vec2[0]) > 0:
                    #    angle_between_radius = 360 - angle_between_radius
                    #angle_between_objects = np.fabs((obj[ObjectProp.Dir] - enemy[ObjectProp.Dir]) % 360)
                    #loss_num = self.loss_function.loss_result(obj, distance, angle_between_radius, angle_between_objects, 1, 1)
                    #self.fl_label.text = 'Оценка функции полезности: {}'.format(loss_num)
                    #self.fl_label.visible = True

                    raw_image = img.tobytes()
                    self.pil_img = pyglet.image.ImageData(self.dx*(self.step_number),
                                                          self.dy*(self.step_number+1),
                                                          'RGB', raw_image)
                    self.pil_img_sprite = pyglet.sprite.Sprite(self.pil_img, batch=self.batch)
                    self.pil_img_sprite.update(x=self.x0, y=self.y0 - 430)
                    self.pil_img_sprite.visible = True

                self.recalc += 1
                self.draw = False
            if self._polar_grid == False:
                for index in range(0, len(self.labels)):
                    self.labels[index].delete()
                    #self.fl_label.visible = False
                    self.draw = True
                    if self.pil_img_sprite:
                        self.pil_img_sprite.visible = False

class Sprite(pyglet.sprite.Sprite):
    def __init__(self, object, batch):
        self.layer = 2
        if object is None:
            self.img = pyglet.resource.image('images/collision.png')
            self.layer = 0
        elif object == ObjectType.Player1:
            self.img = pyglet.resource.image('images/player1.png')
        elif object == ObjectType.Player2:
            self.img = pyglet.resource.image('images/player2.png')
        elif object == ObjectType.Bot1:
            self.img = pyglet.resource.image('images/red_plane.png')
        elif object == ObjectType.Bot2:
            self.img = pyglet.resource.image('images/blue_plane.png')
        elif object == ObjectType.Cone_sprite:
            self.img = pyglet.resource.image('images/coneRot.png')
            self.layer = 1
        self.img.anchor_x = self.img.width // 2 if object != ObjectType.Cone_sprite else self.img.width
        self.img.anchor_y = self.img.height // 2
        self.layer_group = pyglet.graphics.OrderedGroup(self.layer)
        super(Sprite, self).__init__(img=self.img, batch=batch, group=self.layer_group)
        if object == ObjectType.Cone_sprite:
            self.update(scale_x=0.45, scale_y=0.45)
        else:
            self.update(scale_x=0.15, scale_y=0.11)

