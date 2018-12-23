import pyglet
from obj_def import *
from tools import calc_polar_grid
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

        self.step_number = 16
        self.polar_grid = np.zeros((self.step_number, self.step_number + 1))
        self._polar_grid = False                    ### changeable
        self.recalc = 1
        self.draw = True
        self.pil_img = None
        self.pil_img_sprite = None

        self.batch = pyglet.graphics.Batch()

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

            if self.objects_type == ObjectType.Player1:
                self.new_obj_sprite = Player_sprite1(batch=self.batch, scaling_factor=self.scaling_factor)
            elif self.objects_type == ObjectType.Player2:
                self.new_obj_sprite = Player_sprite2(batch=self.batch, scaling_factor=self.scaling_factor)
            elif self.objects_type == ObjectType.Bot1:
                self.new_obj_sprite = Bot_sprite1(batch=self.batch, scaling_factor=self.scaling_factor)
            elif self.objects_type == ObjectType.Bot2:
                self.new_obj_sprite = Bot_sprite2(batch=self.batch, scaling_factor=self.scaling_factor)
            self.cone = Cone_sprite(batch=self.batch, scaling_factor=self.scaling_factor)
            self.rev_cone = Cone_sprite(batch=self.batch, scaling_factor=self.scaling_factor)

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
                    self.cone_sprites[index].visible = False
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
                    self.x0 = 980
                    self.y0 = 1000
                    self.dx = 31
                    self.dy = 25
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
                                                      x=self.x0 - self.dx,
                                                      y=self.y0 - self.dy * i - self.dy // 3,
                                                      anchor_x='left', anchor_y='top', batch=self.batch)
                            self.labels.append(label)
                            if i//2 == i/2:
                                label = pyglet.text.Label(str(int(360*i/self.step_number - 180)),# pi = '\u03C0'
                                                          font_name='Times New Roman',
                                                          font_size=16,
                                                          x=self.x0 + self.dx * i,
                                                          y=self.y0 - self.dy * self.step_number - 3 * self.dy // 2,
                                                          anchor_x='center', anchor_y='top', batch=self.batch)
                                self.labels.append(label)

                    raw_image = img.tobytes()
                    self.pil_img = pyglet.image.ImageData(self.dx*(self.step_number),
                                                          self.dy*(self.step_number+1),
                                                          'RGB', raw_image)
                    self.pil_img_sprite = pyglet.sprite.Sprite(self.pil_img, batch=self.batch)
                    self.pil_img_sprite.update(x=self.x0, y=self.y0 - 430)
                    self.pil_img_sprite.visible = True

                self.recalc += 1
                if self.draw:
                    label = pyglet.text.Label("оценка функции полезности: " + str("сюда писать число"),
                                              font_name='Times New Roman',
                                              font_size=16,
                                              color=((0, 0, 0, 255)),
                                              x=self.x0,
                                              y=self.y0 - self.dy * 19,
                                              anchor_x='left', anchor_y='top', batch=self.batch)
                    self.labels.append(label)
                self.draw = False
            if self._polar_grid == False:
                for index in range(0, len(self.labels)):
                    self.labels[index].delete()
                    self.draw = True
                    if self.pil_img_sprite:
                        self.pil_img_sprite.visible = False


class Sprite(pyglet.sprite.Sprite):
    def __init__(self, batch, img, scaling_factor, layer):
        self.img = img
        self.layer = pyglet.graphics.OrderedGroup(layer)
        self.scaling_factor = scaling_factor
        super(Sprite, self).__init__(img=self.img, batch=batch, group=self.layer)


class Bot_sprite1(Sprite):
    def __init__(self, batch, scaling_factor):
        self.img = pyglet.image.load("images/bot1.png")
        self.img.anchor_x = self.img.width // 2
        self.img.anchor_y = self.img.height // 2
        super(Bot_sprite1, self).__init__(batch=batch, img=self.img, scaling_factor=scaling_factor, layer=2)
        self.update(scale_x=0.15*self.scaling_factor, scale_y = 0.11*self.scaling_factor)


class Bot_sprite2(Sprite):
    def __init__(self, batch, scaling_factor):
        self.img = pyglet.image.load("images/bot2.png")
        self.img.anchor_x = self.img.width // 2
        self.img.anchor_y = self.img.height // 2
        super(Bot_sprite2, self).__init__(batch=batch, img=self.img, scaling_factor=scaling_factor, layer=2)
        self.update(scale_x=0.15*self.scaling_factor, scale_y = 0.1*self.scaling_factor)


class Player_sprite1(Sprite):
    def __init__(self, batch, scaling_factor):
        self.img = pyglet.image.load("images/player1.png")
        self.img.anchor_x = self.img.width // 2
        self.img.anchor_y = self.img.height // 2
        super(Player_sprite1, self).__init__(batch=batch, img=self.img, scaling_factor=scaling_factor, layer=2)
        self.update(scale_x=0.15*self.scaling_factor, scale_y = 0.1*self.scaling_factor)


class Player_sprite2(Sprite):
    def __init__(self, batch, scaling_factor):
        self.img = pyglet.image.load("images/player2.png")
        self.img.anchor_x = self.img.width // 2
        self.img.anchor_y = self.img.height // 2
        super(Player_sprite2, self).__init__(batch=batch, img=self.img, scaling_factor=scaling_factor, layer=2)
        self.update(scale_x=0.15*self.scaling_factor, scale_y = 0.1*self.scaling_factor)


class Cone_sprite(Sprite):
    def __init__(self, batch, scaling_factor):
        self.img = pyglet.image.load("images/coneRot.png")
        self.img.anchor_x = self.img.width - 15
        self.img.anchor_y = self.img.height // 2
        super(Cone_sprite, self).__init__(batch=batch, img=self.img, scaling_factor=scaling_factor, layer=1)
        self.update(scale_x = 0.45*self.scaling_factor, scale_y = 0.45*self.scaling_factor) #PERFECTLY CALCULATED ON FIELD(800, 600)


