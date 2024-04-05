from random import randint
import pygame
from Agents.Food.Food import Food

GREEN = (0, 200, 0)

class Food_Default(Food):
    # constants
    energy_min = 25
    energy_max = 40

    def draw_object(self, display_surface, render_scale):
        pygame.draw.circle(display_surface, GREEN, (self.x * render_scale, self.y * render_scale), self.object_collision_box_edge * 4 * render_scale)

    def __init__(self):
        super().__init__()
        self.energy = float(randint(self.energy_min, self.energy_max))