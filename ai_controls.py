import pyglet
import messages
from dumb_ai import DumbAI, Dummy
#from q_ai import QAi
from greed_ai import GreedAi
from obj_def import *

class AIcontrolsState:
    Start, Run, Exit = range(3)

class TargetMatch:
    def __init__(self):

        self.mapping = []
        self.mapping_index = 0
        self.enemy_index = None

        self.own_team = Teams.Team1
        self.enemy_team = Teams.get_opposite_team(self.own_team)
        self.friendly_ids = Teams.get_team_obj_ids(self.own_team)
        self.enemy_ids = Teams.get_team_obj_ids(self.enemy_team)

    def get_mapping(self, objects):
        self.mapping = []
        self.mapping_index = 0
        for ind in self.enemy_ids:
            if objects[ind][ObjectProp.ObjType] != ObjectType.Absent:
                self.mapping.append(self.mapping_index)
                #print(self.mapping_index)
                self.mapping_index += 1
        return self.mapping #индекс бота и его цели

class AItype:
    Dummy, DumbAi, QAi, GreedAi = range(4)

    @classmethod
    def contruct_ai(cls, aitype, index, battle_field_size, configuration, controller=None, cube=None, alies_cube=None, params=None):

        if aitype == cls.DumbAi:
            return DumbAI(index, battle_field_size, configuration)
        elif aitype == cls.Dummy:
            return Dummy(index)
        #elif aitype == cls.QAi:
        #    q_ai = QAi(index, battle_field_size, controller)
        #    return q_ai
        elif aitype == cls.GreedAi:
            return GreedAi(index, battle_field_size, cube, alies_cube, params)


class AIcontrols:
    def __init__(self, configuration, messenger=None, train_mode=False, cube=None, alies_cube=None, params=None, team_strategy=None):
        self.ai_state = AIcontrolsState.Start
        self.train_mode = train_mode
        self.messenger = messenger
        self.battle_field_size = np.array([0.0, 0.0])
        self.objects_copy = None
        self.configuration = None
        self.result = None
        self.controller = None
        self.ai_objs = []
        self.cube = cube
        self.alies_cube = alies_cube
        self.params = params

        self.team_strategy = team_strategy

        self.teamiter = TargetMatch()
        self.list_maps = []
        self.mapping_iter = np.int32(0)

        for index in range(0, ObjectType.ObjArrayTotal):
            self.ai_objs.append(Dummy(index))
        self.update_ai_settings(configuration)
        self.framerate = 30
        self.functions = {messages.AIcontrols.Quit: self.stop_ai,
                          messages.AIcontrols.UpdateObjects: self.update_objects,
                          messages.AIcontrols.Run: self.start_ai_controls,
                          messages.AIcontrols.UpdateAiSettings: self.update_ai_settings}
        if not self.train_mode:
            pyglet.clock.schedule_interval(self.read_mes, 1.0 / self.framerate)
            pyglet.clock.schedule_interval(self.recalc, 1.0 / self.framerate)

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

    def update_ai_settings(self, configuration):
        self.configuration = configuration
        if configuration:
            offset_counter = {}
            for key in configuration:
                for item in configuration[key]:
                    if key not in offset_counter:
                        offset_counter[key] = 0
                    else:
                        offset_counter[key] += 1

                    if key == ObjectType.FieldSize:
                        self.battle_field_size[0], self.battle_field_size[1] = item[0], item[1]
                    if key in (ObjectType.Player1, ObjectType.Player2, ObjectType.Bot1, ObjectType.Bot2):
                        if len(item) == 6:
                            _, _, _, _, _, aitype = item
                            off_counter = offset_counter[key]
                            obj_offset, _ = ObjectType.offset(key)
                            obj_ind = obj_offset + off_counter
                            self.ai_objs[obj_ind] = AItype.contruct_ai(aitype, obj_ind, self.battle_field_size, configuration,
                                                                       controller=self.controller, cube=self.cube, alies_cube=self.alies_cube, params=self.params)

    def recalc(self, dt, objects_for_train=None):
        self.result = []
        if objects_for_train is not None:
            self.train_mode = True
            self.objects_copy = objects_for_train
        if self.ai_state == AIcontrolsState.Run and (self.objects_copy is not None or self.train_mode):

            self.list_maps = []
            self.list_maps = self.teamiter.get_mapping(self.objects_copy) #словарик
            self.mapping_iter = -1

            for index in range(0, ObjectType.ObjArrayTotal):
                if self.objects_copy[index][ObjectProp.ObjType] == ObjectType.Absent:
                    continue
                #print("ai obj: {}".format(self.ai_objs))
                #if self.ai_objs[index].current_controller is not None:
                #    self.controller = self.ai_objs[index].current_controller
                #    #print(self.controller.actions_executed_so_far)



                if len(self.list_maps) != 0:
                    self.mapping_iter += 1
                    self.mapping_iter = self.mapping_iter % len(self.list_maps)
                    if self.team_strategy == TeamInteractions.All_for_one:
                        self.teamiter.enemy_index = self.list_maps[0]
                    elif self.team_strategy == TeamInteractions.OneGoal_oneTarget:
                        self.teamiter.enemy_index = self.list_maps[self.mapping_iter] if Teams.team_by_id(index) == self.teamiter.own_team else None
                    elif self.team_strategy == TeamInteractions.Dynamical_choose:
                        self.teamiter.enemy_index = None
                else:
                    self.teamiter.enemy_index = None

                result = self.ai_objs[index].calc_behaviour(self.objects_copy, self.teamiter.enemy_index) ###ВОТ ТУТ НАДО ЕЩЕ ЦЕЛЬ ПРОБРАСЫВАТЬ

                if result is None:
                    continue
                turn_ctrl, vel_ctrl = result
                if self.train_mode:
                    self.result.append([index, vel_ctrl, turn_ctrl])
                    continue
                self.messenger.objects_set_control_signal(index, ObjectProp.VelControl, vel_ctrl)
                self.messenger.objects_set_control_signal(index, ObjectProp.TurnControl, turn_ctrl)
            if self.train_mode:
                return self.result

