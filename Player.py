# initialize the screen
import pygame, math, sys, time
from pygame.locals import *


class PlaneSprite(pygame.sprite.Sprite):
    MAX_FORWARD_SPEED = 5
    MAX_REVERSE_SPEED = 0
    ACCELERATION = 0.1
    TURN_SPEED = 0.5
    start = False

    def __init__(self, image, position):
        pygame.sprite.Sprite.__init__(self)
        self.src_image = pygame.image.load(image)
        self.position = position
        self.speed = 0
        self.direction = 0
        self.k_left = self.k_right = self.k_down = self.k_up = 0

    def update(self, deltat):
        # SIMULATION
        self.speed += (self.k_up + self.k_down)
        if self.speed > self.MAX_FORWARD_SPEED:
            self.speed = self.MAX_FORWARD_SPEED
        if self.speed < -self.MAX_REVERSE_SPEED:
            self.speed = -self.MAX_REVERSE_SPEED
        self.direction += (self.k_right + self.k_left)/5
        if (self.direction >= 360):
            self.direction -= 360
        elif (self.direction < 0):
            self.direction += 360
        x, y = (self.position)
        rad = self.direction * math.pi / 180
        x += -self.speed * math.sin(rad)
        y += -self.speed * math.cos(rad)
        self.position = (x, y)
        self.image = pygame.transform.rotate(self.src_image, self.direction)
        self.rect = self.image.get_rect()
        self.rect.center = self.position


