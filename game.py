#initialize the screen
import pygame, math, sys, time
from pygame.locals import *
from Bot import Bot
from Player import PlaneSprite


class HorizontalWallSprite(pygame.sprite.Sprite):
    normal = pygame.image.load('images/walls.png')

    def __init__(self, position):
        super(HorizontalWallSprite, self).__init__()
        self.rect = pygame.Rect(self.normal.get_rect())
        self.rect.center = position
        self.image = self.normal


class VertWallSprite(pygame.sprite.Sprite):
    normal = pygame.image.load('images/vertical_walls.png')

    def __init__(self, position):
        super(VertWallSprite, self).__init__()
        self.rect = pygame.Rect(self.normal.get_rect())
        self.rect.center = position
        self.image = self.normal


def Game():
    alpha = math.pi/4
    betta = math.pi/4
    range_of_atack = 300
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    #GAME CLOCK
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 75)
    win_font = pygame.font.Font(None, 50)
    win_condition = None
    win_text = font.render('', True, (0, 255, 0))
    loss_text = font.render('', True, (255, 0, 0))
    pygame.mixer.music.load('My_Life_Be_Like.mp3')
    #pygame.mixer.music.play(loops=0, start=0.0)
    t0 = time.time()

    bot = Bot((500,0))
    bot_group = pygame.sprite.RenderPlain(bot)

    walls = [
        HorizontalWallSprite((0, -30)),
        HorizontalWallSprite((500, -30)),
        HorizontalWallSprite((1000, -30)),
        HorizontalWallSprite((0, 800)),
        HorizontalWallSprite((500, 800)),
        HorizontalWallSprite((1000, 800)),
        VertWallSprite((-30, 100)),
        VertWallSprite((-30, 600)),
        VertWallSprite((1050, 100)),
        VertWallSprite((1050, 600)),
    ]
    wall_group = pygame.sprite.RenderPlain(*walls)

    # CREATE A PLANE AND RUN
    rect = screen.get_rect()
    plane = PlaneSprite('images/plane.png', (500, 730))
    plane_group = pygame.sprite.RenderPlain(plane)

    #THE GAME LOOP
    while True:
        bot.update()
        #USER INPUT
        t1 = time.time()
        dt = t1-t0

        deltat = clock.tick(30)
        for event in pygame.event.get():
            if not hasattr(event, 'key'): continue
            down = event.type == KEYDOWN
            if win_condition == None:
                if event.key == K_RIGHT: plane.k_right = down * -10
                elif event.key == K_LEFT: plane.k_left = down * 10
                elif event.key == K_UP: plane.k_up = down * 2
                elif event.key == K_DOWN: plane.k_down = down * -2
                elif event.key == K_ESCAPE: sys.exit(0) # quit the game
            elif win_condition == True or win_condition == False :
                Game()
                t0 = t1
            elif event.key == K_ESCAPE:
                sys.exit(0)

        #COUNT TIMER
        seconds = round((0 + dt),2)
        if win_condition == None:
            timer_text = font.render(str(seconds), True, (255,255,0))
            if seconds >= 300:
                win_condition = False
                timer_text = font.render("Time!", True, (255,0,0))
                loss_text = win_font.render('Press Space to Retry', True, (255,0,0))


        #RENDERING
        screen.fill((135,206,250))
        plane_group.update(deltat)
        collisions = pygame.sprite.groupcollide(plane_group, wall_group, False, False, collided = None)
        if collisions != {}:
            win_condition = False
            timer_text = font.render("Crash!", True, (255,0,0))
            plane.image = pygame.image.load('images/collision.png')
            loss_text = win_font.render('Press Space to Retry', True, (255,0,0))
            seconds = 0
            plane.MAX_FORWARD_SPEED = 0
            plane.MAX_REVERSE_SPEED = 0
            plane.k_right = 0
            plane.k_left = 0

        """bot_collision = pygame.sprite.groupcollide(plane_group, bot_group, False, True)
        if bot_collision != {}:
            seconds = seconds
            timer_text = font.render("Caught him!", True, (0,255,0))
            win_condition = True
            plane.MAX_FORWARD_SPEED = 0
            plane.MAX_REVERSE_SPEED = 0
            #pygame.mixer.music.play(loops=0, start=0.0)
            win_text = win_font.render('Press Space to Replay', True, (0,255,0))
            if win_condition == True:
                plane.k_right = -5"""

        yb, xb = bot.position
        yp, xp = plane.position
        xp2 = (xb - xp) * math.cos(bot.direction / 180 * math.pi - betta) + (yb - yp) * math.sin(
            bot.direction / 180 * math.pi - betta)
        yp2 = (xp - xb) * math.sin(bot.direction / 180 * math.pi - betta) + (yb - yp) * math.cos(
            bot.direction / 180 * math.pi - betta)
        print(plane.direction - bot.direction, math.acos(xp2 / math.sqrt(xp2 * xp2 + yp2 * yp2)) <= 2 * alpha , math.sqrt(xp2 * xp2 + yp2 * yp2) < range_of_atack)
        if (abs(plane.direction - bot.direction) > (180 - alpha*180/math.pi) and abs(plane.direction - bot.direction) < (180 + alpha*180/math.pi)
                and yp2 > 0 and math.acos(xp2 / math.sqrt(xp2 * xp2 + yp2 * yp2)) <= 2 * betta
                and math.sqrt(xp2 * xp2 + yp2 * yp2) < range_of_atack):
            seconds = seconds
            timer_text = font.render("Caught him!", True, (0, 255, 0))
            win_condition = True
            plane.MAX_FORWARD_SPEED = 0
            plane.MAX_REVERSE_SPEED = 0
            # pygame.mixer.music.play(loops=0, start=0.0)
            win_text = win_font.render('Press Space to Replay', True, (0, 255, 0))
            if win_condition == True:
                plane.k_right = -5



        wall_group.update(collisions)
        wall_group.draw(screen)
        plane_group.draw(screen)
        bot_group.draw(screen)
        #Counter Render
        screen.blit(timer_text, (20,60))
        screen.blit(win_text, (250, 700))
        screen.blit(loss_text, (250, 700))
        pygame.display.flip()

