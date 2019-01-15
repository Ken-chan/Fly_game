import tensorflow as tf
from obj_def import *
from model import MLP
from discrete_deepq import DiscreteDeepQ
from tools import calc_polar_grid, Loss
import time

class QAi:
    def __init__(self, index, battle_field_size):
        #print("hello its me")
        self.nearest_enemy_id = 0
        self.num_actions = 4
        self.index  = index
        self.battle_field_size = battle_field_size
        self.centre_coord = self.battle_field_size / 2
        self.obj = np.zeros(ObjectProp.Total)

        self.loss = Loss(configuration=None)

        self.step_number = 16
        self.polar_grid = np.zeros((self.step_number + 1, self.step_number))
        #self.number_of_dynamic_steps = 1 # it changes not here, default = 1
        self.number_of_object_typs = 2
        self.observation_size = self.number_of_object_typs * \
                                1 * \
                                self.step_number * (self.step_number + 1)
        self.observation = np.zeros(self.observation_size)
        self.last_observation = np.zeros(self.observation_size)
        self.last_last_observation = np.zeros(self.observation_size)
        self.last_action = None
        self.simulation_started_time = time.time()
        self.acts = [(0, 0, 0, 1), (0, 0, 1, 0), (0, 1, 0, 0), (1, 0, 0, 0)]

        self.current_controller = DiscreteDeepQ(self.observation_size,
                                                self.num_actions, self.acts,
                                                discount_rate=0.99, exploration_period=1000,
                                                max_experience=200000,
                                                store_every_nth=6, train_every_nth=100,
                                                learning_rate=0.01, decay=0.9)

        self.current_controller.restore('q_first_model')

    def observe(self, objects_copy):
        #Return observation vector.
        calc_polar_grid(self, objects_copy, self.battle_field_size[0], self.battle_field_size[1])
        self.tmp_polar_grid = np.array(self.polar_grid.ravel())
        for i in range(0, self.tmp_polar_grid.size):
            if self.tmp_polar_grid[i] == -1:
                self.observation[i] = 1
            elif self.tmp_polar_grid[i] != 0:  ## доделать различение противников от союзников, пока что все враги
                self.observation[i + self.tmp_polar_grid.size] = 1
        #print(self.observation)
        return self.observation


    def collect_reward(self, objects_state):
        obj = objects_state[self.index]
        enemy = objects_state[self.nearest_enemy_id]
        diff_vector = np.array(
            [enemy[ObjectProp.Xcoord] - obj[ObjectProp.Xcoord], enemy[ObjectProp.Ycoord] - obj[ObjectProp.Ycoord]])
        dir2 = enemy[ObjectProp.Dir]
        vec2 = np.array([np.cos(np.radians(dir2)), np.sin(np.radians(dir2))])
        distance = np.linalg.norm(diff_vector)
        arr_dir = np.array(
            [enemy[ObjectProp.Xcoord] - obj[ObjectProp.Xcoord], enemy[ObjectProp.Ycoord] - obj[ObjectProp.Ycoord]])
        arr_dir = arr_dir / np.linalg.norm(arr_dir)
        obj_dir = np.array([np.cos(np.radians(obj[ObjectProp.Dir])), np.sin(np.radians(obj[ObjectProp.Dir]))])
        arr_turned = np.array(
            [arr_dir[0] * obj_dir[0] + arr_dir[1] * obj_dir[1], arr_dir[0] * obj_dir[1] - arr_dir[1] * obj_dir[0]])
        # angle_between_radius = 180 - np.degrees(np.arccos((diff_vector[0] * vec2[0] + diff_vector[1] * vec2[1]) / ((np.sqrt(pow(diff_vector[0], 2) + pow(diff_vector[1], 2))) * (np.sqrt(pow(vec2[0], 2) + pow(vec2[1], 2)))))) if (diff_vector[0] != 0 and vec2[0] != 0) else 0
        angle_between_radius = np.degrees(np.arccos(arr_turned[0]))
        if arr_turned[1] < 0:
            angle_between_radius = 360 - angle_between_radius
        # if (diff_vector[0] * vec2[1] - diff_vector[1] * vec2[0]) > 0:
        #    angle_between_radius = 360 - angle_between_radius
        angle_between_objects = np.fabs((obj[ObjectProp.Dir] - enemy[ObjectProp.Dir]) % 360)
        total_reward = self.loss.loss_result(obj, distance, angle_between_radius, angle_between_objects, 1, 1)
        return total_reward


    def calc_behaviour(self, objects_copy):
        self.rot_side, self.vel_ctrl = (0,0)
        self.obj = objects_copy[self.index]
        self.new_observation = self.observe(objects_copy)
        #print(self.new_observation)
        self.reward = self.collect_reward(objects_copy)
        #print(self.reward)
        if self.last_observation is not None:
            self.current_controller.store(self.last_observation, self.last_action, self.reward,
                                          self.new_observation)
        new_action = self.current_controller.action(self.new_observation)
        if new_action == 0:
            self.rot_side = -1
            self.vel_ctrl = 0
        if new_action == 1:
            self.rot_side = 1
            self.vel_ctrl = 0
        if new_action == 2:
            self.rot_side = 0
            self.vel_ctrl = -1
        if new_action == 3:
            self.rot_side = 0
            self.vel_ctrl = 1
        new_action = self.acts[new_action]
        self.current_controller.training_step()
        self.last_last_observation = self.last_observation
        self.last_action = new_action
        self.last_observation = self.new_observation

        #print(self.rot_side, self.vel_ctrl)
        #print(self.reward)
        return self.rot_side, self.vel_ctrl


