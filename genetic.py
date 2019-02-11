import game
import numpy as np
from tools import QState

eras = 1
epoches = 1
n_cuts = 20
#cube = np.random.rand(n_cuts, n_cuts, n_cuts) #random cube
qs = QState(n_cuts)
cube = np.zeros((n_cuts, n_cuts, n_cuts))
file_path = "cubev2(-1).txt"
qs.load_cube_file(file_path, cube)
#print(cube[1,1,1])

for i in range(0, eras):
    print('<-Era:', i+1)
    game = game.Game(1000,1000,train_mode=True, tries=50, cube=cube)
#game.run_game()