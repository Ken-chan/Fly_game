import pyglet
from obj_def import *

class RendererState:
    Start, Pause, Game, Menu, Exit = range(5)

class Renderer:
    def __init__(self, screen_width, screen_height):
        self.renderer_state = RendererState.Start
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.objects_copy = None
        self.battle_field_width = np.int32(0)
        self.battle_field_height = np.int32(0)
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

        self.batch = pyglet.graphics.Batch()

        self.init_sprites()
        self.renderer_state = RendererState.Game

    def init_sprites(self):
        self.objects_sprites = []
        self.cone_sprites = []
        self.rev_cone_sprites = []
        self.scaling_factor = self.screen_width / 800


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

    def set_battle_field_size(self, x, y):
        self.battle_field_width = x
        self.battle_field_height = y

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
                    self.rev_cone_sprites[index].visible = True
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



