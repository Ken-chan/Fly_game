import numpy as np

class ObjectType:
    Absent = np.int32(0)
    Team1 = np.int32(1)
    Team2 = np.int32(2)
    Bot1 = np.int32(3)
    Bot2 = np.int32(4)
    Player1 = np.int32(5)
    Player2 = np.int32(6)
    ObjArrayTotal = np.int32(43)
    offsets = {
        Team1: (np.int32(0), np.int32(1)),
        Bot1: (np.int32(1), np.int32(20)),
        Player1: (np.int32(21), np.int32(22)),
        Team2: (np.int32(22), np.int32(23)),
        Bot2: (np.int32(23), np.int32(42)),
        Player2: (np.int32(42), np.int32(43))}

    @classmethod
    def offset(cls, obj_type):
        return cls.offsets[obj_type]

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
    K_up = np.int32(6)
    K_down = np.int32(7)
    K_right = np.int32(8)
    K_left = np.int32(9)
    State = np.int32(10)
    Total = np.int32(11)
