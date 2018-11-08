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

        self.batch = pyglet.graphics.Batch()

        self.init_sprites()
        self.renderer_state = RendererState.Game

    def init_sprites(self):
        self.objects_sprites = []
        new_obj_sprite = None

        for index in range(0, ObjectType.ObjArrayTotal):
            object_type = ObjectType.type_by_id(index)

            if object_type == ObjectType.Player1:
                new_obj_sprite = Player_sprite1(batch=self.batch)
            elif object_type == ObjectType.Player2:
                new_obj_sprite = Player_sprite2(batch=self.batch)
            elif object_type == ObjectType.Bot1:
                new_obj_sprite = Bot_sprite1(batch=self.batch)
            elif object_type == ObjectType.Bot2:
                new_obj_sprite = Bot_sprite2(batch=self.batch)

            self.objects_sprites.append(new_obj_sprite)

    def set_battle_fiel_size(self, x, y):
        self.battle_field_width = x
        self.battle_field_height = y

    def update_objects(self, objects):
        self.objects_copy = objects

    def update_graphics(self):
        if self.renderer_state == RendererState.Game and self.objects_copy is not None:
            for index in range(0, len(self.objects_sprites)):
                #print(self.objects_copy[index])
                if self.objects_copy[index][ObjectProp.ObjType] == ObjectType.Absent:
                    self.objects_sprites[index].visible = False
                else:
                    self.objects_sprites[index].visible = True
                    current_object = self.objects_copy[index]
                    size_proportion_width = self.screen_width / self.battle_field_width
                    size_proportion_height = self.screen_height / self.battle_field_height
                    size_proportion_dir = self.screen_width / self.screen_height
                    self.objects_sprites[index].update(x=(current_object[ObjectProp.Xcoord]*size_proportion_width),
                                                       y=(current_object[ObjectProp.Ycoord]*size_proportion_height),
                                                       rotation=current_object[ObjectProp.Dir])


class Sprite(pyglet.sprite.Sprite):

    def __init__(self, batch, img):
        self.img = img
        self.img.anchor_x = self.img.width // 2
        self.img.anchor_y = self.img.height // 2

        super(Sprite, self).__init__(img=self.img, x=self.img.anchor_x, y=self.img.anchor_y, batch=batch)
        self.update(scale=0.5)  ###update

class Bot_sprite1(Sprite):
    def __init__(self, batch):
        self.img = pyglet.image.load("images/bot1.png")
        super(Bot_sprite1, self).__init__(batch=batch, img=self.img)
        self.update(scale=0.25)

class Bot_sprite2(Sprite):
    def __init__(self, batch):
        self.img = pyglet.image.load("images/bot2.png")
        super(Bot_sprite2, self).__init__(batch=batch, img=self.img)
        self.update(scale=0.25)

class Player_sprite1(Sprite):
    def __init__(self, batch):
        self.img = pyglet.image.load("images/player1.png")
        super(Player_sprite1, self).__init__(batch=batch, img=self.img)

class Player_sprite2(Sprite):
    def __init__(self, batch):
        self.img = pyglet.image.load("images/player2.png")
        super(Player_sprite2, self).__init__(batch=batch, img=self.img)




