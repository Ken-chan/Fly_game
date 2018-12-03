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
        self.battle_field_width = 0
        self.battle_field_height = 0
        self.scaling_factor = 0

        self.objects_sprites = None
        self.cone_sprites = None
        self.rev_cone_sprites = None

        self.batch = pyglet.graphics.Batch()

        self.init_sprites()
        self.renderer_state = RendererState.Game

    def init_sprites(self):
        self.objects_sprites = []
        self.cone_sprites = []
        self.rev_cone_sprites = []
        new_obj_sprite = None
        self.scaling_factor = self.screen_width / 800

        for index in range(0, ObjectType.ObjArrayTotal):
            object_type = ObjectType.type_by_id(index)

            if object_type == ObjectType.Player1:
                new_obj_sprite = Player_sprite1(batch=self.batch, scaling_factor=self.scaling_factor)
            elif object_type == ObjectType.Player2:
                new_obj_sprite = Player_sprite2(batch=self.batch, scaling_factor=self.scaling_factor)
            elif object_type == ObjectType.Bot1:
                new_obj_sprite = Bot_sprite1(batch=self.batch, scaling_factor=self.scaling_factor)
            elif object_type == ObjectType.Bot2:
                new_obj_sprite = Bot_sprite2(batch=self.batch, scaling_factor=self.scaling_factor)
            cone = Cone_sprite(batch=self.batch, scaling_factor=self.scaling_factor)
            rev_cone = Cone_sprite(batch=self.batch, scaling_factor=self.scaling_factor)

            self.objects_sprites.append(new_obj_sprite)
            self.rev_cone_sprites.append(rev_cone)
            self.cone_sprites.append(cone)

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
                    current_object = self.objects_copy[index]
                    size_proportion_width = self.screen_width / self.battle_field_width
                    size_proportion_height = self.screen_height / self.battle_field_height
                    #size_proportion_dir = self.screen_width / self.screen_height

                    self.objects_sprites[index].update(x=size_proportion_width * (current_object[ObjectProp.Xcoord]),
                                                       y=size_proportion_height * (current_object[ObjectProp.Ycoord]),
                                                       rotation= -current_object[ObjectProp.Dir])

                    self.cone_sprites[index].update(x=size_proportion_width * (current_object[ObjectProp.Xcoord]), # -
                                                        #100 * np.cos(-np.radians(current_object[ObjectProp.Dir]))),
                                                        # This, to move center of cone on the bottom of objects
                                                    y=size_proportion_height * (current_object[ObjectProp.Ycoord]), # -
                                                        #100 * np.sin(-np.radians(current_object[ObjectProp.Dir]))),
                                                        # Do not need this, cause of make anchors
                                                    rotation= -current_object[ObjectProp.Dir])

                    self.rev_cone_sprites[index].update(x=size_proportion_width  * (current_object[ObjectProp.Xcoord]),
                                                        y=size_proportion_height * (current_object[ObjectProp.Ycoord]),
                                                        rotation=-current_object[ObjectProp.Dir] + 180)

class Sprite(pyglet.sprite.Sprite):

    def __init__(self, batch, img, scaling_factor, layer):
        self.img = img
        self.layer = pyglet.graphics.OrderedGroup(layer)
        self.img.anchor_x = self.img.width // 2
        self.img.anchor_y = self.img.height // 2
        self.scaling_factor = scaling_factor
        super(Sprite, self).__init__(img=self.img, x=self.img.anchor_x, y=self.img.anchor_y, batch=batch, group=self.layer)

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
        self.img.blit(0,0) #Blit just add image on the screen with these anchors. Without this anchors don't work
        super(Cone_sprite, self).__init__(batch=batch, img=self.img, scaling_factor=scaling_factor, layer=1)
        self.update(scale_x = 0.45*self.scaling_factor, scale_y = 0.45*self.scaling_factor) #PERFECTLY CALCULATED ON FIELD(800, 600)



