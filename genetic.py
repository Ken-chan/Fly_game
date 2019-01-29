import game
import numpy as np

n_cuts = 20
cube = np.random.rand(n_cuts, n_cuts, n_cuts)

print("outer: {}".format(cube[0:2, 0:2, 0:2]))
game = game.Game(1000,1000,train_mode=True, tries=5, cube=cube)
#game.run_game()