import pygame, math, sys, time, game
from pygame.locals import *
from Player import PlaneSprite



class Bot(pygame.sprite.Sprite):
    MAX_FORWARD_SPEED = 10
    MAX_REVERSE_SPEED = 0
    ACCELERATION = 1
    TURN_SPEED = 2
    position = (0, 0)
    direction = 0
    speed = 0
    k_left = k_right = k_down = k_up = 0

    image = pygame.image.load('images/Bot.png')

    def __init__(self, position):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('images/Bot.png')
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = position
        self.position = position
        self.speed = 0
        self.direction = 0
        self.k_left = self.k_right = self.k_down = self.k_up = 0

    ### Here you can use multiprocessing to play
    def update(self):
        self.speed = 1
        if self.speed > self.MAX_FORWARD_SPEED:
            self.speed = self.MAX_FORWARD_SPEED
        if self.speed < -self.MAX_REVERSE_SPEED:
            self.speed = -self.MAX_REVERSE_SPEED
        self.direction += (self.k_right + self.k_left)/5
        if(self.direction >= 360):
            self.direction -= 360
        elif(self.direction < 0):
            self.direction += 360
        x, y = (self.position)
        rad = self.direction * math.pi / 180
        x += self.speed * math.sin(rad)
        y += self.speed * math.cos(rad)
        self.position = (x, y)
        self.image = pygame.transform.rotate(self.image, self.direction)
        self.rect = self.image.get_rect()
        self.rect.center = self.position