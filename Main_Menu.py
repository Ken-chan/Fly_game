import pygame, math, sys, time, end, game
from pygame.locals import *


pygame.init()
screen = pygame.display.set_mode((1024, 768))
while 1:
    screen.fill((0,0,0))
    for event in pygame.event.get():
                if not hasattr(event, 'key'): continue
                if event.key == K_SPACE: 
                    game.Game()
                elif event.key == K_ESCAPE: sys.exit(0)  
    img = pygame.image.load("images/Plane_start_pic.png")
    screen.blit(img,(0,0))
    pygame.display.flip()
