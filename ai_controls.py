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
        self.battle_field_size_x = battle_field_size[0]
        self.battle_field_size_y = battle_field_size[1]
        self.objects_copy = None
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
                if self.objects_copy[index][ObjectProp.ObjType] == ObjectType.Bot2:
                    r_attack = 100
                    obj = self.objects_copy[index]
                    obj_x, obj_y = obj[ObjectProp.Xcoord], obj[ObjectProp.Ycoord]

                    obj_dir = obj[ObjectProp.Dir]
                    obj_dir_x, obj_dir_y = np.cos(obj_dir * np.pi / 180), np.sin(obj_dir * np.pi / 180)
                    obj_vel = obj[ObjectProp.Velocity]
                    crit_approx = 200
                    crit_state = False
                    if obj_x < crit_approx:
                        vel_ctrl = -1
                        turn_ctrl = -1 if obj_dir_y > 0 else 1
                        crit_state = True
                    if obj_x > self.battle_field_size_x - crit_approx:
                        vel_ctrl = -1
                        turn_ctrl = 1 if obj_dir_y > 0 else -1
                        crit_state = True
                    if obj_y < crit_approx:
                        vel_ctrl = -1
                        turn_ctrl = 1 if obj_dir_x > 0 else -1
                        crit_state = True
                    if obj_y > self.battle_field_size_y - crit_approx:
                        vel_ctrl = -1
                        turn_ctrl = -1 if obj_dir_x > 0 else 1
                        crit_state = True
                    if crit_state:
                        self.messenger.objects_set_control_signal(index, ObjectProp.VelControl, vel_ctrl)
                        self.messenger.objects_set_control_signal(index, ObjectProp.TurnControl, turn_ctrl)
                        continue

                    enemy = self.objects_copy[ObjectType.offset(ObjectType.Player1)[0]]
                    enemy_x, enemy_y = enemy[ObjectProp.Xcoord], enemy[ObjectProp.Ycoord]
                    enemy_dir = enemy[ObjectProp.Dir]
                    enemy_vel = enemy[ObjectProp.Velocity]
                    x_aim, y_aim = enemy_x - r_attack * np.cos(enemy_dir * np.pi / 180),  enemy_y - r_attack * np.sin(enemy_dir * np.pi / 180)
                    print("enemy: {} {} {} {}".format(enemy_x, enemy_y, x_aim, y_aim))
                    diff_x, diff_y = x_aim - obj_x, y_aim - obj_y
                    print("diff_x, diff_y: {} {}".format(diff_x, diff_y))
                    diff_norm = np.linalg.norm([diff_x, diff_y])
                    diff_x_norm, diff_y_norm = diff_x / diff_norm, diff_y / diff_norm
                    dir_abs = diff_x_norm * obj_dir_x + diff_y_norm * obj_dir_y
                    turn_ctrl = -np.abs(dir_abs) + 1
                    r_crit = 100
                    vel_ctrl = 1 if np.linalg.norm([diff_x, diff_y]) > r_crit else 0
                    #print(vel_ctrl, turn_ctrl)
                    self.messenger.objects_set_control_signal(index, ObjectProp.VelControl, vel_ctrl)
                    self.messenger.objects_set_control_signal(index, ObjectProp.TurnControl, turn_ctrl)
