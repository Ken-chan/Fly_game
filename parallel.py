import game
import numpy as np
from tools import QState
from multiprocessing import Queue, Pool

class ParallelOptions():
    def __init__(self, cube=None, alies_cube=None):
        self.cube = cube
        self.alies_cube = alies_cube
        self.cur_cubes = self.cube, self.alies_cube

    def randomize_cube(self, cube, n_cuts=20, delta=0.05, small_distance=None, max_distance=1500):
        shuffled = np.zeros((n_cuts,n_cuts,n_cuts))
        k = max_distance//small_distance - 1 if small_distance is not None else 1
        for r in range(0, n_cuts//k):
            for phi in range(0, n_cuts):
                for psi in range(0, n_cuts):
                    shuffled[r,phi,psi] = cube[r,phi,psi]+ np.random.normal(0, delta)
        return shuffled

    def randomize_params(self,count,  param, delta=0.02):
        list_params = []
        for i in range(count):
            list_params.append(param + np.random.normal(0, delta))
        return list_params

    def run_gen(self, cur_params, tries=100):
        q = Queue()
        game_obj = game.Game(1000, 1000, train_mode=True, tries=tries, cube=cur_params[0], alies_cube=cur_params[1], queue_res=q, params=cur_params[2:4])
        score = q.get()
        return score, cur_params

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

    def make_list_of_params(self, count, params, delta_cubes=0.05, delta_params=0.02):
        mutations = count
        list_of_enemies_cubes = self.make_list_of_cubes(count=mutations, cube=params[0], delta=delta_cubes)
        list_of_alies_cubes = self.make_list_of_cubes(count=mutations, cube=params[1], delta=delta_cubes)
        list_of_params_crit = self.randomize_params(count=mutations, param=params[2], delta=delta_params)
        list_of_params_walls = self.randomize_params(count=mutations, param=params[3], delta=delta_params)

        main_list = []
        for j in range(mutations):
            list_params = list_of_enemies_cubes[j], list_of_alies_cubes[j], list_of_params_crit[j], \
                          list_of_params_walls[j]
            main_list.append(list_params)
        return main_list

    def make_string_score(self, dict_score):
        str = ''
        for j in dict_score:
            if dict_score[j] != 0:
                str += "{}: {}, ".format(j, dict_score[j])
        return str[:-2]

if __name__ == '__main__':
    n_cuts = 20
    qs = QState(n_cuts)
    enemies_cube, alies_cube = np.zeros((n_cuts, n_cuts, n_cuts)), np.zeros((n_cuts, n_cuts, n_cuts))
    enemy_file_path = "./cubes/enemy_best.txt"
    alies_file_path = "./cubes/alies_0.3067.txt"
    qs.load_cube_file(enemy_file_path, enemies_cube)
    qs.load_cube_file(alies_file_path, alies_cube)

    opt = ParallelOptions()

    best_params = enemies_cube, alies_cube, -0.5, 0.3

    #count_cubes = int(alies_file_path[-5]) if alies_file_path[-6] == '_' else 0
    count_cubes=0
    eras, mutations = 10000, 30
    max_q = 0.3
    delta_cubes = 0.07
    delta_params = 0.03

    pool = Pool(processes=mutations)
    for i in range(eras):
        cur_params = best_params
        find_better = False

        main_list = opt.make_list_of_params(mutations, cur_params, delta_cubes, delta_params)

        q_and_cubes = pool.map(opt.run_gen, main_list)

        local_max, index_local_max, index_max = -1, 0, 0
        for k in range(mutations):
            if q_and_cubes[k][0][0] > max_q:
                max_q = q_and_cubes[k][0][0]
                index_max = k
                find_better = True
            if q_and_cubes[k][0][0] > local_max:
                local_max = q_and_cubes[k][0][0]
                index_local_max = k

        if find_better:
            count_cubes += 1
            best_params = q_and_cubes[index_max][1]
            str_score = opt.make_string_score(q_and_cubes[index_max][0][1])
            print('-> Add parallel best cube: {},  with best score: {:.4f}'.format(count_cubes, max_q))
            print(str_score)

            qs.save_history_file('enemies_first_ver', best_params[0], num_shuffle=count_cubes, score=max_q)
            qs.save_history_file('alies_first_ver', best_params[1], num_shuffle=count_cubes, score=max_q)
            qs.save_params_in_file('crit_and_walls', best_params[2:4], num_shuffle=count_cubes)
        else:
            str_score = opt.make_string_score(q_and_cubes[index_local_max][0][1])
            print('<- Do not found better : ( Local max:{:.4f}'.format(local_max))
            print(str_score)