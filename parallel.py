import game
import numpy as np
from tools import QState
from multiprocessing import Queue, Pool

def randomize_cube(cube, n_cuts=20, delta=0.005):
    shuffled = np.zeros((n_cuts,n_cuts,n_cuts))
    for r in range(0, n_cuts):
        for phi in range(0, n_cuts):
            for psi in range(0, n_cuts):
                shuffled[r,phi,psi] = cube[r,phi,psi]+ np.random.normal(0, delta)
    return shuffled

def run_gen(cur_cube, tries=150):
    q = Queue()
    game_obj = game.Game(1000, 1000, train_mode=True, tries=tries, cube=cur_cube, queue_res=q)
    score = q.get()
    return score, cur_cube

if __name__ == '__main__':
    n_cuts = 20
    qs = QState(n_cuts)
    load_cube = np.zeros((n_cuts, n_cuts, n_cuts))
    file_path = "cube_with_time_6.txt"
    qs.load_cube_file(file_path, load_cube)
    best_cube = load_cube

    eras = 500
    mutations = 30
    count_cubes = 0
    max_q = 0.9

    for i in range(eras):
        load_cube = best_cube
        randomized_cubes = []
        for j in range(mutations):
            rand_cube = randomize_cube(load_cube, delta=0.006)
            randomized_cubes.append(rand_cube)
        #print("Makes {} list of randomized cubes!, Era number:{}".format(mutations, i))
        pool = Pool(processes=mutations)
        q_and_cubes = pool.map(run_gen, randomized_cubes)

        index_max = 0
        for k in range(mutations):
            if q_and_cubes[k][0] > max_q:
                max_q = q_and_cubes[k][0]
                index_max = k

        count_cubes += 1
        best_cube = q_and_cubes[index_max][1]
        print('->Add parallel best cube: {},  with best score: {}'.format(count_cubes, max_q))
        qs.save_history_file('parallel_best', best_cube, num_shuffle=count_cubes)



