import  math
import pyglet

class Player:
    MAX_FORWARD_SPEED = 10
    MAX_REVERSE_SPEED = 0
    ACCELERATION = 1
    TURN_SPEED = 10

    def __init__(self, x, y):
        self.Player_image = pyglet.image.load("images/Plane.png")
        self.Player_sprite = pyglet.sprite.Sprite(self.Player_image)
        self.Player_sprite.position = (x,y)
        self.direction = 0.0
        self.speed = 0
        self.k_left = self.k_right = self.k_down = self.k_up = 0

    ### Here you can use multiprocessing to play
    def update(self):
        self.speed += (self.k_up - self.k_down) * self.ACCELERATION
        if self.speed > self.MAX_FORWARD_SPEED:
            self.speed = self.MAX_FORWARD_SPEED
        if self.speed < self.MAX_REVERSE_SPEED:
            self.speed = self.MAX_REVERSE_SPEED
        self.direction += (self.k_right - self.k_left) * self.TURN_SPEED
        if(self.direction >= 360):
            self.direction -= 360
        elif(self.direction < 0):
            self.direction += 360

        x, y = (self.Player_sprite.position)
        rad = self.direction * math.pi / 180
        x += self.speed * math.sin(rad)
        y += self.speed * math.cos(rad)
        self.Player_sprite.x, self.Player_sprite.y = (x, y)
        self.Player_sprite.rotation = self.direction
        self.k_left = self.k_right = self.k_down = self.k_up = 0




