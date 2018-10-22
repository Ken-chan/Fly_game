import  math
import pyglet

class RendererState:
    Start, Pause, Game, Menu, Exit = range(5)


class Renderer:
    def __init__(self, screen_width, screen_height):
        self.renderer_state = RendererState.Start
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.batch = pyglet.graphics.Batch()

        self.init_sprites()
        self.renderer_state = RendererState.Game

    def init_sprites(self):
        self.player = Player(100, 100, self.batch)
        self.bot = Bot(500, 800, self.batch)


    def update(self, dt):
        self.bot._update(dt)
        self.player._update(dt)

    def update_player(self, delta_speed, delta_angle):
        self.player.speed += delta_speed
        self.player.direction += delta_angle

class Bot(pyglet.sprite.Sprite):
    MAX_FORWARD_SPEED = 10
    MAX_REVERSE_SPEED = 0
    ACCELERATION = 100
    TURN_SPEED = 2

    def __init__(self, x, y, batch):
        self.Bot_image = pyglet.image.load("images/Bot.png")
        super(Bot, self).__init__(img=self.Bot_image)
        self.Bot_sprite = pyglet.sprite.Sprite(self.Bot_image, batch=batch)
        self.Bot_sprite.position = (x,y)
        self.direction = 180.0
        self.k_left = self.k_right = self.k_down = self.k_up = False

    def _update(self, dt):
        self.speed = 1
        if self.speed > self.MAX_FORWARD_SPEED:
            self.speed = self.MAX_FORWARD_SPEED
        if self.speed < self.MAX_REVERSE_SPEED:
            self.speed = self.MAX_REVERSE_SPEED
        self.direction += (self.k_right + self.k_left)/5
        if(self.direction >= 360):
            self.direction -= 360
        elif(self.direction < 0):
            self.direction += 360

        x, y = (self.Bot_sprite.position)
        rad = self.direction * math.pi / 180
        x += self.speed * math.sin(rad)
        y += self.speed * math.cos(rad)
        self.Bot_sprite.x, self.Bot_sprite.y = (x, y)
        self.Bot_sprite.rotation = (self.k_right + self.k_left)/5

class Player(pyglet.sprite.Sprite):
    MAX_FORWARD_SPEED = 100
    MAX_REVERSE_SPEED = 0
    ACCELERATION = 50
    TURN_SPEED = 20

    def __init__(self, x, y, batch):
        self.Player_image = pyglet.image.load("images/Plane.png")
        self.Player_image.anchor_x = self.Player_image.width // 2
        self.Player_image.anchor_y = self.Player_image.height // 2

        super(Player, self).__init__(img=self.Player_image, x=self.Player_image.anchor_x, y=self.Player_image.anchor_y)

        self.Player_sprite = pyglet.sprite.Sprite(self.Player_image, x=self.Player_image.anchor_x, y=self.Player_image.anchor_y, batch=batch)
        self.Player_sprite.position = (x,y)
        self.direction = 0.0
        self.speed = 0
        self.k_left = self.k_right = self.k_down = self.k_up = 0

    def _update(self, dt):
        #self.speed += (self.k_up - self.k_down) * self.ACCELERATION * dt
        if self.speed > self.MAX_FORWARD_SPEED:
            self.speed = self.MAX_FORWARD_SPEED
        if self.speed < self.MAX_REVERSE_SPEED:
            self.speed = self.MAX_REVERSE_SPEED
        #self.direction += (self.k_right - self.k_left) * self.TURN_SPEED * dt
        if(self.direction >= 360):
            self.direction -= 360
        elif(self.direction < 0):
            self.direction += 360

        x, y = (self.Player_sprite.position)
        rad = self.direction * math.pi / 180
        x += self.speed * math.sin(rad) * dt
        y += self.speed * math.cos(rad) * dt
        self.Player_sprite.x, self.Player_sprite.y = (x, y)
        self.Player_sprite.rotation = self.direction






