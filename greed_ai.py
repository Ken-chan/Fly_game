from obj_def import *
from tools import calc_polar_grid, Loss
import time


class GreedAi:
    def __init__(self, index, battle_field_size, cube=None):
        # print("hello its me")
        self.current_controller = None
        self.index = index
        self.nearest_enemy_id = 13
        self.num_actions = 4
        self.cube = cube
        self.battle_field_size = battle_field_size
        self.centre_coord = self.battle_field_size / 2
        self.obj = np.zeros(ObjectProp.Total)

        #reward options#
        self.loss = Loss(cube=self.cube)
        #reward options#


        self.acts = []
        for step_v in range(0, 5):
            for step_d in range(0, 5):
                self.acts.append((-1 + 0.5 * step_v, -1 + 0.5 * step_d))

    def get_nearest_enemy_id(self):
        pass

    def collect_reward(self, objects_state):
        obj = objects_state[self.index]
        #self.nearest_enemy_id = self.get_nearest_enemy_id()
        enemy = objects_state[self.nearest_enemy_id]
        diff_vector = np.array(
            [enemy[ObjectProp.Xcoord] - obj[ObjectProp.Xcoord], enemy[ObjectProp.Ycoord] - obj[ObjectProp.Ycoord]])
        dir2 = enemy[ObjectProp.Dir]
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

    def set_control_signal(self, objects_copy, obj_index, sig_type, sig_val):
        if  -1 <= sig_val <= 1 and sig_type in (ObjectProp.TurnControl, ObjectProp.VelControl):
            objects = objects_copy
            objects[obj_index][sig_type] = sig_val
            return objects

    def calc_v_diff(self, object_state):
        self.min_v_add = 0
        if object_state[ObjectProp.VehicleType] == ObjectSubtype.Plane:
            self.min_v_add = Constants.MinVelAccCoef * np.abs(object_state[ObjectProp.Velocity] - Constants.MinPlaneVel) if object_state[ObjectProp.Velocity] < Constants.MinPlaneVel else 0
        self.dv_calc = Constants.VelAccCoef * (object_state[ObjectProp.VelControl]) - Constants.TurnDissipationCoef * np.abs(object_state[ObjectProp.AngleVel]) * \
             object_state[ObjectProp.Velocity] - Constants.AirResistanceCoef * object_state[ObjectProp.Velocity] + self.min_v_add
        self.w_calc = Constants.TurnAccCoef * object_state[ObjectProp.TurnControl]
        return self.dv_calc, self.w_calc

    def test_update_units(self, obj, act):
        dt = 1.0 / 30
        self.tmp_objects = np.copy(obj)
        self.set_control_signal(self.tmp_objects, self.index, ObjectProp.TurnControl, act[0])
        self.set_control_signal(self.tmp_objects, self.index, ObjectProp.VelControl, act[1])
        for index in range(0, ObjectType.ObjArrayTotal):
            if self.tmp_objects[index][ObjectProp.ObjType] != ObjectType.Absent:
                self.tmp_objects[index][ObjectProp.PrevVelocity] = self.tmp_objects[index][ObjectProp.Velocity]
                self.tmp_objects[index][ObjectProp.PrevAngleVel] = self.tmp_objects[index][ObjectProp.AngleVel]
                self.dv, self.w = self.calc_v_diff(self.tmp_objects[index])
                self.tmp_objects[index][ObjectProp.Velocity] = self.dv * dt + self.tmp_objects[index][ObjectProp.PrevVelocity]
                self.tmp_objects[index][ObjectProp.AngleVel] = self.w
                self.tmp_objects[index][ObjectProp.Dir] += self.tmp_objects[index][ObjectProp.AngleVel] * dt
                self.tmp_objects[index][ObjectProp.Dir] = self.tmp_objects[index][ObjectProp.Dir] % 360
                self.cur_rad = np.radians(self.tmp_objects[index][ObjectProp.Dir])
                self.tmp_objects[index][ObjectProp.Xcoord] += \
                    self.tmp_objects[index][ObjectProp.Velocity] * np.cos(self.cur_rad) * dt
                self.tmp_objects[index][ObjectProp.Ycoord] += \
                    self.tmp_objects[index][ObjectProp.Velocity] * np.sin(self.cur_rad) * dt
        return self.tmp_objects

    def get_gready_action(self, objects_copy):
        self.max_revard = -2
        self.max_revard_action = (0, 0)
        #print(objects_copy[self.index])
        for act in self.acts:
            self.tmp_obj = self.test_update_units(objects_copy, act)
            self.tmp_revard = self.collect_reward(self.tmp_obj)
            #print("action = ", act, "revard = ", self.tmp_revard)
            #print(self.tmp_obj[self.index])
            if self.tmp_revard > self.max_revard:
                self.max_revard = self.tmp_revard
                self.max_revard_action = act
        #print("max_revard: {}".format(self.max_revard_action))
        return self.max_revard_action

    def calc_behaviour(self, objects_copy):
        self.rot_side, self.vel_ctrl = (0, 0)
        self.obj = objects_copy[self.index]
        #new_action = (0, -1)
        new_action = self.get_gready_action(objects_copy)
        #print(new_action)

        self.rot_side, self.vel_ctrl = new_action

        return self.rot_side, self.vel_ctrl

