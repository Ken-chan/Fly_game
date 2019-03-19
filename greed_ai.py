from obj_def import *
from tools import calc_polar_grid, Loss, Helper
import time


class GreedAi:
    def __init__(self, index, battle_field_size, cube=None, alies_cube=None):
        # print("hello its me")
        self.current_controller = None
        self.index = index
        self.nearest_enemy_id = None
        self.cube = cube
        self.alies_cube = alies_cube
        self.battle_field_size = battle_field_size
        self.centre_coord = self.battle_field_size / 2
        self.obj = np.zeros(ObjectProp.Total)
        self.obj_coord = np.array([0.0, 0.0])
        self.nearest_distance = None
        self.enemy_distance = None
        self.obj = None
        self.enemy = None
        self.total_reward = np.float(0.0)
        self.alies_reward = np.float(0.0)

        self.diff_vector = np.array([0.0,0.0])
        self.distance = np.float(0.0)
        self.arr_dir = np.array([0.0,0.0])
        self.obj_dir = np.array([0.0,0.0])
        self.angle_between_radius = np.float(0.0)
        self.angle_between_objects = np.float(0.0)
        self.arr_turned = np.array([0.0,0.0])
        self.alone = False


        self.own_team = Teams.team_by_id(self.index)
        self.enemy_team = Teams.get_opposite_team(self.own_team)
        self.friendly_ids = Teams.get_team_obj_ids(self.own_team)
        self.enemy_ids = Teams.get_team_obj_ids(self.enemy_team)

        #reward options#
        self.loss = Loss(cube=self.cube, alies_cube=self.alies_cube)
        self.h = Helper()
        #reward options#


        self.acts = []
        self.num_actions = 3
        for step_v in range(0, self.num_actions+1):
            for step_d in range(0, self.num_actions+1):
                self.acts.append((-1 + (2/self.num_actions * step_v), -1 + (2/self.num_actions * step_d)))

    def calc_nearest_obj_and_enemy(self, objects_state):
        self.nearest_enemy_id = None ## AHTING HARDCODE
        self.enemy_distance = None
        for ind in self.enemy_ids:
            if ind == self.index:
                continue
            if objects_state[ind][ObjectProp.ObjType] != ObjectType.Absent:
                curr_dist = np.linalg.norm(np.array([objects_state[ind][ObjectProp.Xcoord] - self.obj_coord[0],
                                                     objects_state[ind][ObjectProp.Ycoord] - self.obj_coord[1]]))
                if self.enemy_distance is None or self.enemy_distance > curr_dist:
                    self.enemy_distance = curr_dist
                    self.nearest_enemy_id = ind
        self.alone = True
        for ind in self.friendly_ids:
            if ind == self.index:
                continue
            if objects_state[ind][ObjectProp.ObjType] != ObjectType.Absent:
                self.alone = False
                self.nearest_distance = np.linalg.norm(np.array([objects_state[ind][ObjectProp.Xcoord] - self.obj_coord[0],
                                                     objects_state[ind][ObjectProp.Ycoord] - self.obj_coord[1]]))
        if self.alone:
            self.nearest_distance = None
        return self.nearest_enemy_id

    def collect_reward(self, objects_state):
        self.obj = objects_state[self.index]
        self.enemy = objects_state[self.nearest_enemy_id] if self.nearest_enemy_id is not None else None
        if self.enemy is not None:
            self.distance, self.angle_between_radius, self.angle_between_objects = self.h.get_r_phi_psi(self.obj, self.enemy)
        self.total_reward = self.loss.loss_result(self.obj, self.distance, self.angle_between_radius, self.angle_between_objects, 1, 1)
        self.alies_reward = self.loss.calc_qstate_friends(objects_state, self.friendly_ids, self.index)

        return self.total_reward + self.alies_reward

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
        #print(new_action)
        self.obj_coord[0], self.obj_coord[1] = self.obj[ObjectProp.Xcoord], self.obj[ObjectProp.Ycoord]
        self.nearest_enemy_id = self.calc_nearest_obj_and_enemy(objects_copy)

        new_action = self.get_gready_action(objects_copy)
        self.rot_side, self.vel_ctrl = new_action

        return self.rot_side, self.vel_ctrl

