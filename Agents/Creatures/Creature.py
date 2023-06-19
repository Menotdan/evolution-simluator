from Agents.Food.Food import Food
from math_utils import normalize_vector, clamp, get_distance, get_new_value
import numpy as np
from random import *
import math

MOVE_FOOD = 0
MOVE_ESCAPE = 1
MOVE_ATTACK = 2
MOVE_WANDER = 3

class Creature:
    # state
    x = 0
    y = 0
    energy = 50
    alive = True

    def run_ai(self, creatures, food):
        return

    def child_count(self):
        return 0
    
    def would_win(self, fighter):
        return False

    def lost_fight(self, fighter):
        self.alive = False

    def won_fight(self, fighter):
        pass

    def collides(self, object):
        return False
    
    def evolve(self):
        pass

    def apply_move_energy_cost(self, distance):
        pass

    def copy(self):
        return_object = Creature()
        return_object.energy = self.weight * 5

        return return_object
    
    def draw_object(self, display_surface, render_scale):
        pass

    # Serialization
    def save_to_string(self):
        return ""

    def load_from_string(self, string):
        pass

    def average_add(self, input_data):
        return input_data
    
    def average_divide(input_data, count):
        return input_data
    
    def __init__(self):
        self.energy = 0