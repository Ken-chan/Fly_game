from obj_def import *


class Dummy:
    def __init__(self, index):
        self.index = index
        self.current_controller = None

    def calc_behaviour(self, objects_state, enemy_index=None):
        return None

class DumbAI(Dummy):
    def __init__(self, index, battle_field_size, configuration):
        super(DumbAI, self).__init__(index)
        self.battle_field_size = battle_field_size
        self.centre_coord = self.battle_field_size / 2
        self.r_attack = np.int32(100)
        self.crit_approx = np.int32(50)
        self.r_crit = np.int32(100)
        self.collision_crit = np.int32(100)
        self.front_crit_collision = np.int32(350)
        self.enemy_index = np.int32(0)
        self.obj = np.zeros(ObjectProp.Total)
        self.obj_coord = np.array([0.0,0.0])
        self.obj_dir = np.float(0.0)
        self.obj_dir_vec = np.array([0.0, 0.0])
        self.obj_vel = np.float(0.0)
        self.centre_dir = np.array([0.0, 0.0])
        self.enemy_id = np.int32(0)
        self.enemy = np.zeros(ObjectProp.Total)
        self.enemy_coord = np.array([0.0,0.0])
        self.enemy_dir = np.float(0.0)
        self.enemy_dir_vec = np.array([0.0,0.0])
        self.enemy_vel = np.float(0.0)
        self.aim_coord = np.array([0.0, 0.0])
        self.diff_coord = np.array([0.0, 0.0])
        self.angle, self.rotation_side = np.float(0.0), np.float(0.0)
        self.turn_mod = np.float(0.0)
        self.turn_ctrl = np.float(0.0)
        self.rotation_matrix = np.array([[0.0, 0.0], [0.0, 0.0]])
        self.vec1, self.vec2 = np.array([0.0, 0.0]), np.array([0.0, 0.0])
        self.vec2_rel = np.array([0.0, 0.0])
        self.angle_min = np.float(0.0)
        self.vel_ctrl = np.float(0.0)
        self.rot_side = np.float(0.0)
        self.own_team = Teams.team_by_id(self.index)
        self.enemy_team = Teams.get_opposite_team(self.own_team)
        self.friendly_ids = Teams.get_team_obj_ids(self.own_team)
        self.enemy_ids = Teams.get_team_obj_ids(self.enemy_team)
        self.nearest_enemy_id = None
        self.nearest_object_id = None
        self.nearest_object = np.zeros(ObjectProp.Total)
        self.nearest_coord = np.array([0.0, 0.0])
        self.nearest_dir_vec = np.array([0.0, 0.0])
        self.nearest_dir = np.float(0.0)
        self.obj_diff_coord = np.array([0.0, 0.0])
        self.angle_objs = np.float(0.0)
        self.rotation_side_objs = np.float(0.0)

    def calc_nearest_dir(self, vec1, vec2):
        self.vec1, self.vec2 = vec1 / np.linalg.norm(vec1), vec2 / np.linalg.norm(vec2)
        self.rotation_matrix[0][0], self.rotation_matrix[0][1], self.rotation_matrix[1][0], self.rotation_matrix[1][1]= vec1[0], vec1[1], -vec1[1], vec1[0]
        self.vec2_rel = np.matmul(self.rotation_matrix, self.vec2)
        if self.vec2_rel[0] > 1:
            self.vec2_rel[0] = 1
        elif self.vec2_rel[0] < -1:
            self.vec2_rel[0] = -1
        self.angle_min = np.degrees(np.abs(np.arccos(self.vec2_rel[0]))) ## THERE CATCH WARNING ARCOS -1 1
        #self.rotation_side = np.float(1.0) if np.sign(self.vec2_rel[1]) >= 0 else np.float(-1.0)
        self.rotation_side = np.float(np.sign(self.vec2_rel[1]))
        if self.rotation_side == .0:
            self.rotation_side = 1.0
        return self.angle_min, self.rotation_side

    def calc_nearest_obj_and_enemy(self, objects_state):
        self.nearest_enemy_id = None
        enemy_distance = None
        for ind in self.enemy_ids:
            if ind == self.index:
                continue
            if objects_state[ind][ObjectProp.ObjType] != ObjectType.Absent:
                curr_dist = np.linalg.norm(np.array([objects_state[ind][ObjectProp.Xcoord] - self.obj_coord[0],
                                                     objects_state[ind][ObjectProp.Ycoord] - self.obj_coord[1]]))
                if enemy_distance is None or enemy_distance > curr_dist:
                    enemy_distance = curr_dist
                    self.nearest_enemy_id = ind
        self.nearest_object_id = self.nearest_enemy_id
        nearest_distance = enemy_distance
        for ind in self.friendly_ids:
            if ind == self.index:
                continue
            if objects_state[ind][ObjectProp.ObjType] != ObjectType.Absent:
                curr_dist = np.linalg.norm(np.array([objects_state[ind][ObjectProp.Xcoord] - self.obj_coord[0],
                                                     objects_state[ind][ObjectProp.Ycoord] - self.obj_coord[1]]))
                if nearest_distance is None or nearest_distance > curr_dist:
                    nearest_distance = curr_dist
                    self.nearest_object_id = ind
        return self.nearest_enemy_id, self.nearest_object_id

    def calc_behaviour(self, objects_state, enemy_index=None):
        self.obj = objects_state[self.index]
        self.obj_coord[0], self.obj_coord[1] = self.obj[ObjectProp.Xcoord], self.obj[ObjectProp.Ycoord]
        self.obj_dir = self.obj[ObjectProp.Dir]
        self.obj_dir_vec[0], self.obj_dir_vec[1] = np.cos(np.radians(self.obj_dir)), np.sin(np.radians(self.obj_dir))
        self.obj_vel = self.obj[ObjectProp.Velocity]
        self.nearest_enemy_id, self.nearest_object_id = self.calc_nearest_obj_and_enemy(objects_state)

        self.enemy = objects_state[self.nearest_enemy_id] if self.nearest_enemy_id is not None else None
        self.nearest_object = objects_state[self.nearest_object_id] if self.nearest_object_id is not None else None
        if self.battle_field_size[0] - self.crit_approx < self.obj_coord[0] or self.obj_coord[0] < self.crit_approx \
                or self.battle_field_size[1] - self.crit_approx < self.obj_coord[1] or self.obj_coord[1] < self.crit_approx:
            self.centre_dir = self.centre_coord - self.obj_coord
            self.angle, self.rotation_side = self.calc_nearest_dir(self.obj_dir_vec, self.centre_dir)
            self.rot_side = (1 / 180 * self.angle) * self.rotation_side
            self.vel_ctrl = np.float(1) if self.angle <= np.float(90) else np.float(-1)
            return self.rot_side, self.vel_ctrl

        if self.nearest_object is not None:
            self.nearest_coord[0] = self.nearest_object[ObjectProp.Xcoord]
            self.nearest_coord[1] = self.nearest_object[ObjectProp.Ycoord]
            self.nearest_dir = self.nearest_object[ObjectProp.Dir]
            self.nearest_dir_vec[0], self.nearest_dir_vec[1] = np.cos(np.radians(self.nearest_dir)), np.sin(np.radians(self.nearest_dir))
            self.angle, self.rotation_side = self.calc_nearest_dir(self.nearest_dir_vec, self.obj_dir_vec)
            self.obj_diff_coord = self.obj_coord - self.enemy_coord
            self.angle_objs, self.rotation_side_objs = self.calc_nearest_dir(self.obj_dir_vec, self.obj_diff_coord)
            if self.angle > 175 and self.angle_objs > 175 and self.obj[ObjectProp.Velocity] > 130 and np.linalg.norm(self.nearest_coord - self.obj_coord) < self.front_crit_collision:
                self.turn_ctrl = 1
                self.vel_ctrl = -1
                return self.turn_ctrl, self.vel_ctrl

            if np.linalg.norm(self.nearest_coord - self.obj_coord) < self.collision_crit:
                self.angle, self.rotation_side = self.calc_nearest_dir(self.obj_dir_vec, self.nearest_coord - self.obj_coord)
                if self.angle < 90:
                    self.turn_ctrl = -self.rotation_side
                    self.vel_ctrl = -1
                return self.turn_ctrl, self.vel_ctrl

        if self.enemy is not None:
            self.enemy_coord[0], self.enemy_coord[1] = self.enemy[ObjectProp.Xcoord], self.enemy[ObjectProp.Ycoord]
            self.enemy_dir = self.enemy[ObjectProp.Dir]
            self.enemy_dir_vec[0], self.enemy_dir_vec[1] = np.cos(np.radians(self.enemy_dir)), np.sin(np.radians(self.enemy_dir))
            self.enemy_vel = self.enemy[ObjectProp.Velocity]
            self.angle, self.rotation_side = self.calc_nearest_dir(self.enemy_dir_vec, self.obj_dir_vec)
            self.obj_diff_coord = self.obj_coord - self.enemy_coord
            self.angle_objs, self.rotation_side_objs = self.calc_nearest_dir(self.obj_dir_vec, self.enemy_dir_vec)
            if self.angle > 175 and self.angle_objs > 175 and self.obj[ObjectProp.Velocity] > 130 and np.linalg.norm(self.enemy_coord - self.obj_coord) < self.front_crit_collision:
                self.turn_ctrl = 1
                self.vel_ctrl = -1
                return self.turn_ctrl, self.vel_ctrl

            self.aim_coord[0] = self.enemy_coord[0] - self.r_attack * np.cos(np.radians(self.enemy_dir))
            self.aim_coord[1] = self.enemy_coord[1] - self.r_attack * np.sin(np.radians(self.enemy_dir))
            self.diff_coord = self.aim_coord - self.obj_coord
            self.angle, self.rotation_side = self.calc_nearest_dir(self.obj_dir_vec, self.diff_coord)
            self.turn_mod = np.float(1) if self.angle > np.float(30) else np.float(1/30) * self.angle
            self.turn_ctrl = self.rotation_side * self.turn_mod

            self.vel_ctrl = np.float(1) if np.linalg.norm(self.diff_coord) > self.r_crit else np.float(0)
        return self.turn_ctrl, self.vel_ctrl