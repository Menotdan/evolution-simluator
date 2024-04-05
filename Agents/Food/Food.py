from random import randint
import pygame

GREEN = (0, 200, 0)

class Food:
    # state
    x = 0
    y = 0
    energy = 10
    alive = True
    object_collision_box_edge = 1

    def draw_object(self, display_surface, render_scale):
        pass

    def eaten(self, eaten_by):
        pass

    def __init__(self):
        pass