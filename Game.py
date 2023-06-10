import math
import time
import pygame
from pygame.locals import *
import numpy as np
from random import random, randint

from Agents.Food.Food import Food
from math_utils import normalize_vector, clamp, get_distance
from Agents.Creatures.Creature import Creature

class Game:
    # state
    foods: list[Food] = []
    creatures: list[Creature] = []
    time_steps = 0
    render_display = None

    # constants
    kill_energy_factor = 0.5
    food_energy_min = 25
    food_energy_max = 40

    reproduction_factor = 3

    sim_delay = 0.05
    time_steps_day = 100
    map_width = 500
    map_height = 350

    render_scale = 2

    GREEN = (0, 200, 0)
    RED =  (200, 0, 0)

    energy_max_by_weight_scale = 5

    def time_step(self):
        for c in self.creatures:
            c.run_ai(self.creatures, self.foods)
            clamped_distance = self.clamp_movement(c, self.map_width, self.map_height)
            c.apply_move_energy_cost(-clamped_distance) # Restore energy we don't actually use

        for c in self.creatures:
            if not c.alive:
                continue

            for f in self.foods:
                if c.collides(f) and f.alive:
                    f.alive = False
                    c.energy += f.energy
            
            for sub_c in self.creatures:
                if not sub_c.alive:
                    continue
                if c == sub_c:
                    continue
                
                if c.collides(sub_c):
                    if c.would_win(sub_c):
                        sub_c.alive = False
                        c.energy += sub_c.energy * self.kill_energy_factor
                        continue
                    else:
                        c.alive = False
                        sub_c.energy += c.energy * self.kill_energy_factor
                        break

        # Cleanup dead creatures
        copy_creatures = self.creatures[:]
        deleted_count = 0
        for creature_index in range(len(copy_creatures)):
            if not copy_creatures[creature_index].alive:
                del self.creatures[creature_index - deleted_count]
                deleted_count += 1
        del copy_creatures

        copy_food = self.foods[:]
        deleted_count = 0
        for food_index in range(len(copy_food)):
            if not copy_food[food_index].alive:
                del self.foods[food_index - deleted_count]
                deleted_count += 1
        del copy_food


    def generate_x(self):
        return float(randint(0, self.map_width - 1))
    
    def generate_y(self):
        return float(randint(0, self.map_height - 1))

    def day_end(self, food_count):
        for c in self.creatures[:]:
            if c.energy >= c.weight:
                for i in range(min(2, math.floor(c.energy / (c.weight * self.reproduction_factor)))):
                    self.create_child(c)
        self.init_food(food_count)
    
    def init_food(self, food_count):
        self.foods.clear()
        for i in range(food_count):
            new_food: Food = Food()
            new_food.x = self.generate_x()
            new_food.y = self.generate_y()
            new_food.energy = float(randint(self.food_energy_min, self.food_energy_max))
            self.foods.append(new_food)

    def draw_objects(self):
        self.render_display.fill((255, 255, 255))
        for c in self.creatures:
            pygame.draw.circle(self.render_display, self.RED, (c.x * self.render_scale, c.y * self.render_scale), c.object_collision_box_edge * 4 * self.render_scale)
        for f in self.foods:
            pygame.draw.circle(self.render_display, self.GREEN, (f.x * self.render_scale, f.y * self.render_scale), Creature.object_collision_box_edge * 4 * self.render_scale)
        pygame.display.update()

    def create_child(self, creature: Creature):
        new_creature = Creature()
        new_creature.x = self.generate_x()
        new_creature.y = self.generate_y()
        
        # scale evolution values
        new_creature.evolve()
        new_creature.energy = new_creature.weight * self.energy_max_by_weight_scale

        self.creatures.append(new_creature)
    
    def clamp_movement(self, c: Creature, limit_x, limit_y):
        c_old_pos = Creature()
        c_old_pos.x, c_old_pos.y = (c.x, c.y)

        if c.x >= limit_x:
            c.x = limit_x - 1

        if c.y >= limit_y:
            c.y = limit_y - 1
        
        if c.x < 0:
            c.x = 0

        if c.y < 0:
            c.y = 0
        distance_clamped = get_distance(c, c_old_pos)
        del c_old_pos
        return distance_clamped

    def init_renderer(self):
        pygame.init()
        self.render_display = pygame.display.set_mode((self.map_width * self.render_scale, self.map_height * self.render_scale))

    def run_sim(self, foods_count):
        last_run = 0

        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    quit()

            time.sleep(max(0, self.sim_delay - last_run))

            start_run = time.time()
            self.time_step()
            self.time_steps += 1

            self.draw_objects()

            if self.time_steps == self.time_steps_day:
                self.time_steps = 0
                self.day_end(foods_count)
                if len(self.creatures) > 0:
                    index = randint(0, len(self.creatures) - 1)
                    print(f"Creatures: {len(self.creatures)}, {round(self.creatures[index].move_escape_weight, 3)}, {round(self.creatures[index].move_attack_weight, 3)}, {round(self.creatures[index].move_food_weight, 3)}")
                self.draw_objects()
            last_run = time.time() - start_run

    def __init__(self, foods_count, creatures_start):
        self.init_renderer()

        for i in range(creatures_start):
            creature_init = Creature()
            creature_init.x = self.generate_x()
            creature_init.y = self.generate_y()
            creature_init.energy = creature_init.weight * self.energy_max_by_weight_scale
            self.creatures.append(creature_init)

        self.init_food(foods_count)

        self.run_sim(foods_count)