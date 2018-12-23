import numpy as np
import sys


class Teams:
    Team1 = np.int32(0)
    Team2 = np.int32(1)
    Team1_ids = None
    Team2_ids = None

    @classmethod
    def team_by_id(cls, obj_id):
        if ObjectType.type_by_id(obj_id) == ObjectType.Bot1 or ObjectType.type_by_id(obj_id) == ObjectType.Player1:
            return cls.Team1
        elif ObjectType.type_by_id(obj_id) == ObjectType.Bot2 or ObjectType.type_by_id(obj_id) == ObjectType.Player2:
            return cls.Team2
        else:
            return None

    @classmethod
    def get_team_obj_ids(cls, team):
        if team == cls.Team1:
            if cls.Team1_ids is None:
                cls.Team1_ids = [ObjectType.offset(ObjectType.Player1)[0]] + [x for x in range(ObjectType.offset(ObjectType.Bot1)[0], ObjectType.offset(ObjectType.Bot1)[1] + 1)]
            return cls.Team1_ids
        elif team == cls.Team2:
            if cls.Team2_ids is None:
                cls.Team2_ids = [ObjectType.offset(ObjectType.Player2)[0]] + [x for x in range(ObjectType.offset(ObjectType.Bot2)[0], ObjectType.offset(ObjectType.Bot2)[1] + 1)]
            return cls.Team2_ids

    @classmethod
    def get_opposite_team(cls, team):
        if team == cls.Team1:
            return cls.Team2
        elif team == cls.Team2:
            return cls.Team1


class ObjectType:
    Absent = np.int32(0)
    FieldSize = np.int32(1)
    Bot1 = np.int32(2)
    Bot2 = np.int32(3)
    Player1 = np.int32(4)
    Player2 = np.int32(5)

    ObjArrayTotal = np.int32(24)
    offsets = {
        Player1: (np.int32(0), np.int32(0)),
        Player2: (np.int32(1), np.int32(1)),
        Bot1: (np.int32(2), np.int32(12)),
        Bot2: (np.int32(13), np.int32(23)),
    }

    @classmethod
    def offset(cls, obj_type):
        return cls.offsets[obj_type]

    @classmethod
    def type_by_id(cls, obj_id):
        value = cls.Absent
        if obj_id == np.int32(0):
            value = cls.Player1
        elif obj_id == np.int32(1):
            value = cls.Player2
        elif 2 <= obj_id <= 12:
            value = cls.Bot1
        elif 13 <= obj_id <= 23:
            value = cls.Bot2
        return value

    @classmethod
    def name_of_type_by_id(cls, obj_id):
        value = "Absent"
        if obj_id == np.int32(0):
            value = "Player1"
        elif obj_id == np.int32(1):
            value = "Player2"
        elif 2 <= obj_id <= 12:
            value = "Bot1"
        elif 13 <= obj_id <= 23:
            value = "Bot2"
        return value


class ObjectSubtype:
    Plane = np.int32(0)
    Helicopter = np.int32(1)
    Drone = np.int32(2)
    Rocket = np.int32(3)


class ObjectProp:
    ObjId = np.int32(0)
    ObjType = np.int32(1)
    Xcoord = np.int32(2)
    Ycoord = np.int32(3)
    Dir = np.int32(4)
    AngleVel = np.int32(5)
    PrevAngleVel = np.int32(6)
    Velocity = np.int32(7)
    PrevVelocity = np.int32(8)
    VelControl = np.int32(9)
    TurnControl = np.int32(10)
    State = np.int32(11)
    R_size = np.int32(12)
    VehicleType = np.int32(13)
    Total = np.int32(14)


class Constants:
    epsilon = sys.float_info.epsilon
    DefaultObjectRadius = np.int32(15)
    AttackRange = np.int32(200)
    MinPlaneVel = np.int32(150)
    AttackConeWide = np.int32(20)
    MinVelAccCoef = np.int32(2)
    VelAccCoef = np.int32(120)
    TurnDissipationCoef = np.float(0.01)
    AirResistanceCoef = np.float(0.05)
    TurnAccCoef = np.int32(110)