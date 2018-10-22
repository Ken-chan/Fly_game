import pygame, sys, math
from pygame.locals import *


def end_game():
    while 1:
        pygame.init()
        screen = pygame.display.set_mode((1024, 768))
        win_font = pygame.font.Font(None, 70)
        win_text = win_font.render('Congratulations! Thanks for Playing!', True, (0,255,0))
        screen.blit(win_text, (60, 384))
        pygame.display.flip()
        for event in pygame.event.get():
            if not hasattr(event, 'key'): continue
            if event.key == K_ESCAPE: sys.exit(0) # quit the game

#end.end_game()



class Game:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

    def quit(self):
        pyglet.app.exit()

    def run_game(self):
        self.game_window = pyglet.window.Window(self.screen_width, self.screen_height)

        @self.game_window.event
        def on_close():
            self.quit()

        pyglet.app.run()

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


    # CREATE A PLANE AND RUN
    rect = screen.get_rect()
    plane = PlaneSprite('images/plane.png', (500, 730))
    plane_group = pygame.sprite.RenderPlain(plane)

    #THE GAME LOOP
    while True:
        bot.update(,
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

        yb, xb = bot.position
        yp, xp = plane.position
        xp2 = (xb - xp) * math.cos(bot.direction / 180 * math.pi - betta) + (yb - yp) * math.sin(
            bot.direction / 180 * math.pi - betta)
        yp2 = (xp - xb) * math.sin(bot.direction / 180 * math.pi - betta) + (yb - yp) * math.cos(
            bot.direction / 180 * math.pi - betta)

        if (abs(plane.direction - bot.direction) > (180 - alpha*180/math.pi) and abs(plane.direction - bot.direction) < (180 + alpha*180/math.pi)
                and yp2 > 0 and math.acos(xp2 / math.sqrt(xp2 * xp2 + yp2 * yp2)) <= 2 * betta
                and math.sqrt(xp2 * xp2 + yp2 * yp2) < range_of_atack):
            seconds = seconds
            timer_text = font.render("Caught him!", True, (0, 255, 0))
            win_condition = True
            plane.MAX_FORWARD_SPEED = 0
            plane.MAX_REVERSE_SPEED = 0
            win_text = win_font.render('Press Space to Replay', True, (0, 255, 0))
            if win_condition == True:
                plane.k_right = -5

        plane_group.draw(screen)
        bot_group.draw(screen)
        #Counter Render
        screen.blit(timer_text, (20,60))
        screen.blit(win_text, (250, 700))
        screen.blit(loss_text, (250, 700))
        pygame.display.flip()


