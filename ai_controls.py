from multiprocessing import Process, Queue
import pyglet
import messages
from obj_def import *
from random import *


class AIcontrolsState:
    Start, Run, Exit = range(3)


class AIcontrols(Process):
    def __init__(self, messenger, battle_field_size):
        super(AIcontrols, self).__init__()
        self.ai_state = AIcontrolsState.Start
        self.messenger = messenger
        self.battle_field_size = np.array(battle_field_size)
        self.objects_copy = None
        self.ai_objs = []
        for index in range(0, ObjectType.ObjArrayTotal):
            self.ai_objs.append(Dummy(index))
        dumb_ai_index = ObjectType.offset(ObjectType.Bot2)[0]
        self.ai_objs[dumb_ai_index] = DumbAI(dumb_ai_index, self.battle_field_size)
        self.functions = {messages.AIcontrols.Quit: self.stop_ai,
                          messages.AIcontrols.UpdateObjects: self.update_objects,
                          messages.AIcontrols.Run: self.start_ai_controls}

        pyglet.clock.schedule_interval(self.read_mes, 1.0 / 30.0)
        pyglet.clock.schedule_interval(self.recalc, 1.0 / 30.0)

    def read_mes(self, dt):
        if self.ai_state != AIcontrolsState.Exit:
            while True:
                data = self.messenger.get_message(messages.AIcontrols)
                if not data:
                    break
                self.functions[data['func']](**data['args']) if 'args' in data else self.functions[data['func']]()

    def start_ai_controls(self):
        self.ai_state = AIcontrolsState.Run

    def stop_ai(self):
        self.ai_state = AIcontrolsState.Exit

    def update_objects(self, objects_copy):
        self.objects_copy = objects_copy

    def recalc(self, dt):
        if self.ai_state == AIcontrolsState.Run and self.objects_copy is not None:
            for index in range(0, ObjectType.ObjArrayTotal):
                if self.objects_copy[index][ObjectProp.ObjType] == ObjectType.Absent:
                    continue
                result = self.ai_objs[index].calc_behaviour(self.objects_copy)
                if result is None:
                    continue
                turn_ctrl, vel_ctrl = result
                self.messenger.objects_set_control_signal(index, ObjectProp.VelControl, vel_ctrl)
                self.messenger.objects_set_control_signal(index, ObjectProp.TurnControl, turn_ctrl)

class Dummy:
    def __init__(self, index):
        self.index = index

    def calc_behaviour(self, objects_state):
        return None


class DumbAI(Dummy):
    def __init__(self, index, battle_field_size):
        super(DumbAI, self).__init__(index)
        self.battle_field_size = battle_field_size
        self.centre_coord = self.battle_field_size / 2
        self.r_attack = 100
        self.crit_approx = 100
        self.r_crit = 100
        self.enemy_index = ObjectType.offset(ObjectType.Player1)[0]
        self.obj = np.zeros(ObjectProp.Total)
        self.obj_coord = np.array([0.0,0.0])
        self.obj_dir = np.float(0.0)
        self.obj_dir_vec = np.array([0.0, 0.0])
        self.obj_vel = np.float(0.0)
        self.centre_dir = np.array([0.0, 0.0])
        self.enemy = np.zeros(ObjectProp.Total)
        self.enemy_coord = np.array([0.0,0.0])
        self.enemy_dir = np.float(0.0)
        self.enemy_dir_vec = np.array([0.0,0.0])
        self.enemy_vel = np.float(0.0)


    def calc_nearest_dir(self, vec1, vec2):
        vec1, vec2 = vec1 / np.linalg.norm(vec1), vec2 / np.linalg.norm(vec2)
        rotation_matrix = np.array([[vec1[0], vec1[1]], [-vec1[1], vec1[0]]])
        vec2_rel = np.matmul(rotation_matrix, vec2)
        angle_min = np.abs(np.arccos(vec2_rel[0])) * 180 / np.pi
        rotation_side = 1 if np.sign(vec2_rel[1]) >= 0 else -1
        return angle_min, rotation_side


    def calc_behaviour(self, objects_state):
        self.obj = objects_state[self.index]
        self.obj_coord[0], self.obj_coord[1] = self.obj[ObjectProp.Xcoord], self.obj[ObjectProp.Ycoord]
        self.obj_dir = self.obj[ObjectProp.Dir]
        self.obj_dir_vec[0], self.obj_dir_vec[1] = np.cos(self.obj_dir * np.pi / 180), np.sin(self.obj_dir * np.pi / 180)
        self.obj_vel = self.obj[ObjectProp.Velocity]
        if self.battle_field_size[0] - self.crit_approx < self.obj_coord[0] or self.obj_coord[0] < self.crit_approx \
                or self.battle_field_size[1] - self.crit_approx < self.obj_coord[1] or self.obj_coord[1] < self.crit_approx:
            self.centre_dir = self.centre_coord - self.obj_coord
            angle, rotation_side = self.calc_nearest_dir(self.obj_dir_vec, self.centre_dir)
            rot_side = (1 / 180 * angle) * rotation_side
            vel_ctrl = 1 if angle <= 90 else -1
            return rot_side, vel_ctrl

        self.enemy = objects_state[self.enemy_index]
        self.enemy_coord = np.array([self.enemy[ObjectProp.Xcoord], self.enemy[ObjectProp.Ycoord]])
        self.enemy_dir = self.enemy[ObjectProp.Dir]
        self.enemy_dir_vec = np.array([np.cos(self.obj_dir * np.pi / 180), np.sin(self.obj_dir * np.pi / 180)])
        self.enemy_vel = self.enemy[ObjectProp.Velocity]

        aim_coord = self.enemy_coord - np.array([self.r_attack * np.cos(self.enemy_dir * np.pi / 180), self.r_attack * np.sin(self.enemy_dir * np.pi / 180)])
        diff_coord = aim_coord - self.obj_coord
        angle, rotation_side = self.calc_nearest_dir(self.obj_dir_vec, diff_coord)
        turn_mod = 1 if angle > 30 else 1/30 * angle
        turn_ctrl = rotation_side * turn_mod

        vel_ctrl = 1 if np.linalg.norm(diff_coord) > self.r_crit else 0
        return turn_ctrl, vel_ctrl