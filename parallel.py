import game
import numpy as np
from tools import QState
from multiprocessing import Queue, Pool

class ParallelOptions():
    def __init__(self, cube=None, alies_cube=None):
        self.cube = cube
        self.alies_cube = alies_cube

    def randomize_cube(self, cube, n_cuts=20, delta=0.05):
        shuffled = np.zeros((n_cuts,n_cuts,n_cuts))
        for r in range(0, n_cuts):
            for phi in range(0, n_cuts):
                for psi in range(0, n_cuts):
                    shuffled[r,phi,psi] = cube[r,phi,psi]+ np.random.normal(0, delta)
        return shuffled

    def run_gen(self, cur_cube, tries=100):
        q = Queue()
        game_obj = game.Game(1000, 1000, train_mode=True, tries=tries, cube=self.cube, alies_cube=cur_cube, queue_res=q)
        score = q.get()
        return score, cur_cube

    def download_best_cubes(self, count=20):
        list = []
        for i in range(count):
            file_path = "best_shuffled_cube_with_time_{}.txt".format(i)
            cube = np.zeros((n_cuts, n_cuts, n_cuts))
            qs.load_cube_file(file_path, cube)
            list.append(cube)
        return list

if __name__ == '__main__':
    n_cuts = 20
    qs = QState(n_cuts)
    load_cube = np.zeros((n_cuts, n_cuts, n_cuts))
    alies_cube = np.zeros((n_cuts, n_cuts, n_cuts))
    file_path = "best_2.txt"
    alies_file_path = "alies_zero_cube.txt"
    qs.load_cube_file(file_path, load_cube)
    qs.load_cube_file(alies_file_path, alies_cube)
    opt = ParallelOptions(cube=load_cube)

    best_cube = alies_cube ##alies_cube

    count_download_cubes = 15

    eras = 10000
    mutations = 30
    count_cubes = 0
    max_q = 0.1


    for i in range(eras):
        cur_cube = best_cube
        find_better = False
        #list_of_best_cubes = download_best_cubes(count=count_download_cubes)

        randomized_cubes = []
        for j in range(mutations):
            rand_cube = opt.randomize_cube(cur_cube, delta=0.1) #0.05
            randomized_cubes.append(rand_cube)

        #print("Makes {} list of randomized cubes!, Era number:{}".format(mutations, i))
        pool = Pool(processes=mutations)
        q_and_cubes = pool.map(opt.run_gen, randomized_cubes)
        local_max = 0

        index_max = 0
        for k in range(mutations):
            if q_and_cubes[k][0] > max_q:
                max_q = q_and_cubes[k][0]
                index_max = k
                find_better = True
            if q_and_cubes[k][0] > local_max:
                local_max = q_and_cubes[k][0]

        if find_better:
            count_cubes += 1
            best_cube = q_and_cubes[index_max][1]
            print('-> Add parallel best cube: {},  with best score: {}'.format(count_cubes, max_q))
            qs.save_history_file('alies_cube_ver', best_cube, num_shuffle=count_cubes)
        else:
            print('<- Do not found better : ( Local max:{}'.format(local_max))


