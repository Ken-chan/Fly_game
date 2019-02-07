from obj_def import *
from discrete_deepq import DiscreteDeepQ
from tools import calc_polar_grid
from tools import Loss, SimpleLoss
import time

class QAi:
    def __init__(self, index, battle_field_size, controller=None):
        #print("hello its me")
        if index == 13:
            self.nearest_enemy_id = 2
            save_path = 'q_first_model'
        else:
            self.nearest_enemy_id = 13
            save_path = 'q_second_model'
        self.num_actions = 9
        self.index = index
        self.battle_field_size = battle_field_size
        self.centre_coord = self.battle_field_size / 2
        self.obj = np.zeros(ObjectProp.Total)

        self.loss = SimpleLoss(battle_field_size)

        self.step_number = 16
        self.polar_grid = np.zeros((self.step_number + 1, self.step_number))
        #self.number_of_dynamic_steps = 1 # it changes not here, default = 1
        self.number_of_object_typs = 1
        self.observation_size = self.number_of_object_typs * \
                                1 * \
                                self.step_number * (self.step_number + 1)
        self.observation = np.zeros(self.observation_size)
        self.last_observation = np.zeros(self.observation_size)
        self.last_last_observation = None
        self.last_last_last_observation = None
        self.last_action = 0
        self.simulation_started_time = time.time()
        self.acts = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 0), (0, 1), (1, -1), (1, 0), (1, 1)]
        if controller == None:
            self.current_controller = DiscreteDeepQ(3*self.observation_size,
                                                    2, self.acts,
                                                    discount_rate=0.9, exploration_period=5000000,
                                                    max_experience=10000,
                                                    store_every_nth=5, train_every_nth=100,
                                                    minibatch_size=32,
                                                    learning_rate=0.01, gamma=0.95,
                                                    target_network_update_rate=10000,
                                                    save_path=save_path)

            #self.current_controller.restore(save_path)
        else:
            self.current_controller = controller


    def observe(self, objects_copy):
        #Return observation vector.
        calc_polar_grid(self, objects_copy, self.battle_field_size[0], self.battle_field_size[1], step_number=16)
        self.tmp_polar_grid = np.array(self.polar_grid.ravel())
        for i in range(0, self.tmp_polar_grid.size):
            if self.tmp_polar_grid[i] == -1:
                self.observation[i] = -1
            elif self.tmp_polar_grid[i] != 0:  ## доделать различение противников от союзников, пока что все враги
                self.observation[i] = 1
                #print("enemy", i + self.tmp_polar_grid.size)
        #print(self.observation)
        return self.observation


    def collect_reward(self, objects_state):
        obj = objects_state[self.index]
        total_reward = self.loss.loss_result(obj, objects_state)
        return total_reward


    def calc_behaviour(self, objects_copy):
        self.rot_side, self.vel_ctrl = (0, 0)
        self.obj = objects_copy[self.index]
        #print(self.obj)

        self.observation = np.zeros(self.observation_size)
        self.new_observation = self.observe(objects_copy)
        if self.last_last_observation is None:
            self.last_observation = self.new_observation
            self.last_last_observation = self.new_observation
            self.last_last_last_observation = self.new_observation
        #print(self.new_observation)
        self.reward = self.collect_reward(objects_copy)
        print("reward = ", self.reward)
        #if self.reward == 1:
        #    print("111111111111111111111111111111111111111111111111111111111111111111111111111111")
        if self.last_observation is not None:
            self.current_controller.store(np.array(np.concatenate((self.last_last_last_observation,
                                                                   self.last_last_observation,
                                                                   self.last_observation), axis=None)),
                                          self.last_action, self.reward,
                                          np.array(np.concatenate((self.last_last_observation,
                                                                   self.last_observation,
                                                                   self.new_observation), axis=None)))
        new_action = self.current_controller.action(np.array(np.concatenate((self.last_last_observation,
                                                                             self.last_observation,
                                                                             self.new_observation), axis=None)))
        self.rot_side, self.vel_ctrl = self.acts[new_action]
        #new_action = self.acts[new_action]

        self.current_controller.training_step()

        self.last_last_last_observation = self.last_last_observation
        self.last_last_observation = self.last_observation
        self.last_action = new_action
        self.last_observation = self.new_observation

        #print(self.rot_side, self.vel_ctrl)
        return self.rot_side, self.vel_ctrl


