import game
import numpy as np
from tools import QState
from multiprocessing import Queue

eras = 300
tries = 100
mutations = 10
n_cuts = 20

#cube2 = np.random.rand(n_cuts, n_cuts, n_cuts) #random cube
qs = QState(n_cuts)
cube = np.zeros((n_cuts, n_cuts, n_cuts))
file_path = "firstly.txt"
qs.load_cube_file(file_path, cube)

#sucess = obj.success
best_cube = cube
best_score = 0.1
cur_score = -1.0

def randomize_cube(cube):
    shuffled = np.zeros((n_cuts,n_cuts,n_cuts))
    for r in range(0, n_cuts):
        for phi in range(0, n_cuts):
            for psi in range(0, n_cuts):
                shuffled[r,phi,psi] = cube[r,phi,psi]+ np.random.normal(0, 0.05)
                #print(cube[r, phi, psi],shuffled[r, phi, psi], r, phi, psi)
    return shuffled

count_cubes = 0
count_goods = 0
q = Queue()
#Start genetic algorythm
for i in range(0, eras):
    print('<-----Era number:', i)
    cube = best_cube
    is_mutated_good_that_base = False
    for j in range(0, mutations):
        cur_cube = randomize_cube(cube)
        print('<----Shuffled cube number:', j)
        game_obj = game.Game(1000,1000,train_mode=True, tries=tries, cube=cur_cube, queue_res=q)
        cur_score = q.get()
        print(">succesfully from genetic:{}".format(cur_score))
        if cur_score >= best_score:
            best_score = cur_score
            best_cube = cur_cube
            is_mutated_good_that_base = True
        if cur_score > 0.99:
            count_goods += 1
            qs.save_history_file('good_shufled_cube', cube, num_shuffle=count_goods)
        print('<__{}__> Cur but best <__{}__>'.format(cur_score, best_score))
    if is_mutated_good_that_base:
        count_cubes += 1
        qs.save_history_file('best_shuffled_cube', best_cube, num_shuffle=count_cubes)
        print('->>>>Add new shuffled cube file: {},  with best score: {}'.format(count_cubes, best_score))
    else:
        i -= 1 #restart epoch
        print('D; Restart epoch, sad random D; <--------------->')
#game.run_game()