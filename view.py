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
        self.cone_sprites = []
        cone = None
        new_obj_sprite = None

        for index in range(0, ObjectType.ObjArrayTotal):
            object_type = ObjectType.type_by_id(index)

            if object_type == ObjectType.Player1:
                new_obj_sprite = Player_sprite1(batch=self.batch)
                cone = Cone_sprite(batch=self.batch)
            elif object_type == ObjectType.Player2:
                new_obj_sprite = Player_sprite2(batch=self.batch)
                cone = Cone_sprite(batch=self.batch)
            elif object_type == ObjectType.Bot1:
                new_obj_sprite = Bot_sprite1(batch=self.batch)
                cone = Cone_sprite(batch=self.batch)
            elif object_type == ObjectType.Bot2:
                new_obj_sprite = Bot_sprite2(batch=self.batch)
                cone = Cone_sprite(batch=self.batch)

            self.objects_sprites.append(new_obj_sprite)
            self.cone_sprites.append(cone)

    def set_battle_field_size(self, x, y):
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
                    self.cone_sprites[index].visible = False
                else:
                    self.objects_sprites[index].visible = True
                    self.cone_sprites[index].visible = True
                    current_object = self.objects_copy[index]
                    size_proportion_width = self.screen_width / self.battle_field_width
                    size_proportion_height = self.screen_height / self.battle_field_height
                    size_proportion_dir = self.screen_width / self.screen_height
                    #self.draw_zone_of_defense(current_object[ObjectProp.Xcoord]*size_proportion_width,
                    #                          current_object[ObjectProp.Ycoord]*size_proportion_height,
                    #                          current_object[ObjectProp.Dir]) # THATS MAKING THESE UGLY PICTURES sorry :c
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


    # need to refactor
    def make_part_of_circle(self, numpoints, rel_x, rel_y, phi, unit_angle):
        global circle
        vertices = []
        for i in range(numpoints):
            angle = np.radians(float(i) / numpoints * 2 * phi + 90 - phi)
            x = 150 * np.cos(angle - unit_angle) + rel_x
            y = 150 * np.sin(angle - unit_angle) + rel_y
            vertices += [x, y]
        vertices += [rel_x, rel_y]
        circle = pyglet.graphics.vertex_list(numpoints + 1, ('v2f', vertices))

    def draw_zone_of_defense(self, x, y, dir):
        self.make_part_of_circle(50, x, y, 30, np.radians(dir))
        circle.draw(pyglet.gl.GL_LINE_LOOP)

    # need to refactor

class Sprite(pyglet.sprite.Sprite):

    def __init__(self, batch, img):
        self.img = img
        self.img.anchor_x = self.img.width // 2
        self.img.anchor_y = self.img.height // 2
        super(Sprite, self).__init__(img=self.img, x=self.img.anchor_x, y=self.img.anchor_y, batch=batch)

class Bot_sprite1(Sprite):
    def __init__(self, batch):
        self.img = pyglet.image.load("images/bot1.png")
        self.img.anchor_x = self.img.width // 2
        self.img.anchor_y = self.img.height // 2
        super(Bot_sprite1, self).__init__(batch=batch, img=self.img)
        self.update(scale_x=0.15, scale_y = 0.11)

class Bot_sprite2(Sprite):
    def __init__(self, batch):
        self.img = pyglet.image.load("images/bot2.png")
        self.img.anchor_x = self.img.width // 2
        self.img.anchor_y = self.img.height // 2
        super(Bot_sprite2, self).__init__(batch=batch, img=self.img)
        self.update(scale_x=0.15, scale_y = 0.1)

class Player_sprite1(Sprite):
    def __init__(self, batch):
        self.img = pyglet.image.load("images/player1.png")
        self.img.anchor_x = self.img.width // 2
        self.img.anchor_y = self.img.height // 2
        super(Player_sprite1, self).__init__(batch=batch, img=self.img)
        self.update(scale_x=0.15, scale_y = 0.1)

class Player_sprite2(Sprite):
    def __init__(self, batch):
        self.img = pyglet.image.load("images/player2.png")
        self.img.anchor_x = self.img.width // 2
        self.img.anchor_y = self.img.height // 2
        super(Player_sprite2, self).__init__(batch=batch, img=self.img)
        self.update(scale_x=0.15, scale_y = 0.1)

class Cone_sprite(Sprite):
    def __init__(self, batch):
        self.img = pyglet.image.load("images/coneRot.png")
        self.img.anchor_x = self.img.width - 15
        self.img.anchor_y = self.img.height // 2
        self.img.blit(0,0) #Blit just add image on the screen with these anchors. Without this anchors don't work
        super(Cone_sprite, self).__init__(batch=batch, img=self.img)
        self.update(scale_x = 0.45, scale_y = 0.45) #PERFECTLY CALCULATED ON FIELD(1000, 1000)



