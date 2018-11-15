import numpy as np

class ObjectType:
    Absent = np.int32(0)
    FieldSize = np.int32(1)
    Bot1 = np.int32(2)
    Bot2 = np.int32(3)
    Player1 = np.int32(4)
    Player2 = np.int32(5)

    ObjArrayTotal = np.int32(23)
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

class ObjectSubtype:
    Plane = np.int32(0)
    Helicopter = np.int32(1)
    Drone = np.int32(2)
    Rocket = np.int32(3)


class ObjectProp:
    ObjId = np.int32(0)
    ObjType = np.int32(1)
    #ObjSubtype = np.int16(2)
    Xcoord = np.int32(2)
    Ycoord = np.int32(3)
    Dir = np.int32(4)
    Velocity = np.int32(5)
    Velocity_prev = np.int32(6)
    K_up = np.int32(7)
    K_down = np.int32(8)
    K_right = np.int32(9)
    K_left = np.int32(10)
    State = np.int32(11)
    R_size = np.int32(12)
    Total = np.int32(13)

