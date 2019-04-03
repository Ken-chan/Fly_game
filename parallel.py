import game
import numpy as np
from tools import QState
from multiprocessing import Queue, Pool

class ParallelOptions():
    def __init__(self, cube=None, alies_cube=None):
        self.cube = cube
        self.alies_cube = alies_cube

    def randomize_cube(self, cube, n_cuts=20, delta=0.05, small_distance=None, max_distance=1500):
        shuffled = np.zeros((n_cuts,n_cuts,n_cuts))
        k = max_distance//small_distance - 1 if small_distance is not None else 1
        for r in range(0, n_cuts//k):
            for phi in range(0, n_cuts):
                for psi in range(0, n_cuts):
                    shuffled[r,phi,psi] = cube[r,phi,psi]+ np.random.normal(0, delta)
        return shuffled

    def run_gen(self, cur_cube, tries=100):
        q = Queue()
        game_obj = game.Game(1000, 1000, train_mode=True, tries=tries, cube=self.cube, alies_cube=cur_cube, queue_res=q)
        score = q.get()
        return score, cur_cube

    def download_best_cubes(self, count):
        list_of_cubes = []
        for i in range(count):
            file_path = "best_shuffled_cube_with_time_{}.txt".format(i)
            cube = np.zeros((n_cuts, n_cuts, n_cuts))
            qs.load_cube_file(file_path, cube)
            list_of_cubes.append(cube)
        return list_of_cubes

    def make_list_of_cubes(self, count, cube=None, download=False, delta=0.05):
        list_of_cubes = []
        if download:
            list_of_cubes = self.download_best_cubes(count=count)
        else:
            for j in range(count):
                rand_cube = self.randomize_cube(cube, delta=delta)  # 0.05
                list_of_cubes.append(rand_cube)
        return list_of_cubes

if __name__ == '__main__':
    n_cuts = 20
    qs = QState(n_cuts)
    enemies_cube, alies_cube = np.zeros((n_cuts, n_cuts, n_cuts)), np.zeros((n_cuts, n_cuts, n_cuts))
    enemy_file_path = "./cubes/best_enemy_cube.txt"
    alies_file_path = "./cubes/alies_after_generation.txt"
    qs.load_cube_file(enemy_file_path, enemies_cube)
    qs.load_cube_file(alies_file_path, alies_cube)

    opt = ParallelOptions(cube=enemies_cube)

    best_cube = alies_cube ##alies_cube

    eras = 10000
    mutations = 30
    count_cubes = int(alies_file_path[-5]) if alies_file_path[-6] == '_' else 0
    max_q = 0.1
    delta = 0.2

    pool = Pool(processes=mutations)
    for i in range(eras):
        cur_cube = best_cube
        find_better = False

        list_of_cubes = opt.make_list_of_cubes(count=mutations, cube=cur_cube, delta=delta)
        q_and_cubes = pool.map(opt.run_gen, list_of_cubes)

        local_max, index_max = -1, 0
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
            print('-> Add parallel best cube: {},  with best score: {:.4f}'.format(count_cubes, max_q))
            qs.save_history_file('alies_gen_ford_ver', best_cube, num_shuffle=count_cubes, score=max_q)
        else:
            print('<- Do not found better : ( Local max:{}'.format(local_max))