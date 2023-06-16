import numpy as np
from random import *
import math

clamp = lambda x, l, u: l if x < l else u if x > u else x

def normalize_vector(vec):
        if np.linalg.norm(vec, ord=1) == 0:
            return np.asarray([0.0, 0.0])
        norm_vec = (vec / np.linalg.norm(vec, ord=1))
        return norm_vec

def get_new_value(old: float, scale: float):
    return old + ((random() - 0.5) * 2) * scale

def get_distance(object1, object2):
    return math.sqrt(math.pow(object1.x - object2.x, 2) + math.pow(object1.y - object2.y, 2))

def get_move_towards_vector(self, object):
        move_direction = np.asarray([object.x - self.x, object.y - self.y])
        move_direction = normalize_vector(move_direction)

        return move_direction * self.speed

def get_move_away_vector(self, object):
        move_direction = np.asarray([self.x - object.x, self.y - object.y])
        move_direction = normalize_vector(move_direction)

        return move_direction * self.speed