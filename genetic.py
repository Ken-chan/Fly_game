import game
import numpy as np
from tools import QState

n_cuts = 20
#qs = QState(n_cuts)
#cube = np.zeros((n_cuts, n_cuts, n_cuts))
#file_path = "cubev2(-1).txt"
#qs.load_cube_file(file_path, cube)
#print(cube[1,1,1])

cube = np.random.rand(n_cuts, n_cuts, n_cuts)


game = game.Game(1000,1000,train_mode=True, tries=5, cube=cube)
#game.run_game()