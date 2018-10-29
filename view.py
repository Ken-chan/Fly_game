import pyglet
from multiprocessing import Process
from obj_def import *

class RendererState:
    Start, Pause, Game, Menu, Exit = range(5)

class Renderer:
    def __init__(self, screen_width, screen_height):
        self.renderer_state = RendererState.Start
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.objects_copy = None

        self.batch = pyglet.graphics.Batch()

        self.init_sprites()
        self.renderer_state = RendererState.Game

    def init_sprites(self):
        self.player = Player_sprite(500, 100, self.batch)

    def update_objects(self, objects):
        self.objects_copy = objects


    def update_graphics(self):
        if self.renderer_state == RendererState.Game:
            if self.objects_copy is not None:
                if self.objects_copy[ObjectType.Player1][ObjectProp.ObjType] != ObjectType.Absent:
                    x = self.objects_copy[ObjectType.Player1][ObjectProp.Xcoord]
                    y = self.objects_copy[ObjectType.Player1][ObjectProp.Ycoord]
                    dir = self.objects_copy[ObjectType.Player1][ObjectProp.Dir]
                    self.player.update(x=x, y=y, rotation=dir)


class Bot_sprite(pyglet.sprite.Sprite):

    def __init__(self, x, y, batch):
        self.Bot_image = pyglet.image.load("images/Bot2.png")
        super(Bot_sprite, self).__init__(img=self.Bot_image)
        self.Bot_sprite = pyglet.sprite.Sprite(self.Bot_image, batch=batch)
        self.Bot_sprite.position = (x,y)
        self.Bot_sprite.scale = 0.5  ###update
        self.Bot_sprite.rotation = 180

    def _update(self, dt):
        pass
        #self.Bot_sprite.x, self.Bot_sprite.y = (x, y)
        #self.Bot_sprite.rotation =  #(self.k_right + self.k_left)/5

class Player_sprite(pyglet.sprite.Sprite):

    def __init__(self, x, y, batch):
        self.Player_image = pyglet.image.load("images/Player2.png")
        self.Player_image.anchor_x = self.Player_image.width // 2
        self.Player_image.anchor_y = self.Player_image.height // 2

        super(Player_sprite, self).__init__(img=self.Player_image, x=self.Player_image.anchor_x, y=self.Player_image.anchor_y)
        self.Player_sprite = pyglet.sprite.Sprite(self.Player_image, x=self.Player_image.anchor_x, y=self.Player_image.anchor_y, batch=batch)
        self.Player_sprite.position = (x,y)
        self.Player_sprite.update(scale=0.5)  ###update


    def _update(self, dt):
        #self.Player_sprite.x, self.Player_sprite.y = (x, y)
        self.Player_sprite.rotation = self.direction






