import  math
import pyglet

class Bot:
    MAX_FORWARD_SPEED = 10
    MAX_REVERSE_SPEED = 0
    ACCELERATION = 1
    TURN_SPEED = 2
    k_left = k_right = k_down = k_up = 0

    def __init__(self, x, y):
        self.Bot_image = pyglet.image.load("images/Bot.png")
        self.Bot_sprite = pyglet.sprite.Sprite(self.Bot_image)
        self.Bot_sprite.position = (x,y)
        self.direction = 180.0
        self.k_left = self.k_right = self.k_down = self.k_up = 0

    ### Here you can use multiprocessing to play
    def update(self):
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


#window = pyglet.window.Window()


bot = Bot(100,100)


def update(dt):
    bot.update()

if __name__ == "__main__":
    pyglet.clock.schedule_interval(update, 1.0/60)
    pyglet.app.run()


