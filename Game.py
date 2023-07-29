import math
import time
import pygame
from pygame.locals import *
import numpy as np
from random import random, randint

from math_utils import normalize_vector, clamp, get_distance

from Agents.Food.Food import Food
from Agents.Food.Food_Default import Food_Default

from Agents.Creatures.Creature import Creature
from Agents.Creatures.Creature_Default import Creature_Default

class Game:
    # init state (type, factor)
    creatures_spawn = [(Creature_Default, 1)]
    food_spawn = [(Food_Default, 1)]

    # state
    foods: list[Food] = []
    creatures: list[Creature] = []
    time_steps = 0
    render_display = None

    # constants
    food_energy_min = 25
    food_energy_max = 40

    reproduction_factor = 3

    sim_delay = 0.05
    time_steps_day = 100
    map_width = 500
    map_height = 350

    render_scale = 2

    def encounter_handle(self, c1: Creature, c2: Creature):
        c1_would_win = c1.would_win(c2)
        c2_would_win = c2.would_win(c1)
        real_c1_wins = True

        if c1_would_win != c2_would_win:
            if c1.energy > c2.energy:
                real_c1_wins = c1_would_win
            else:
                real_c1_wins = c2_would_win
        else:
            real_c1_wins = c1_would_win # both are correct, just pick one

        if real_c1_wins:
            c1.won_fight(c2)
            c2.lost_fight(c1)
        else:
            c1.lost_fight(c2)
            c2.won_fight(c1)

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
                    f.eaten(c)
                    f.alive = False
                    c.energy += f.energy

            for sub_c in self.creatures:
                if not sub_c.alive:
                    continue
                if c == sub_c:
                    continue
                if c.collides(sub_c):
                    self.encounter_handle(c, sub_c)

        # Cleanup dead creatures
        copy_creatures = self.creatures[:]
        deleted_count = 0
        for creature_index in range(len(copy_creatures)):
            if not copy_creatures[creature_index].alive:
                del self.creatures[creature_index - deleted_count]
                deleted_count += 1
        del copy_creatures

        # Cleanup eaten food
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
            for i in range(int(c.child_count())):
                self.create_child(c)

        self.init_food(food_count)

    def init_food(self, food_count):
        self.foods.clear()
        for food_type, percent in self.food_spawn:
            for i in range(int(math.floor(food_count * percent))):
                new_food = food_type()
                new_food.x = self.generate_x()
                new_food.y = self.generate_y()
                self.foods.append(new_food)

    def draw_objects(self):
        self.render_display.fill((255, 255, 255))
        for c in self.creatures:
            c.draw_object(self.render_display, self.render_scale)
        for f in self.foods:
            f.draw_object(self.render_display, self.render_scale)
        pygame.display.update()

    def create_child(self, creature: Creature):
        new_creature = creature.copy()
        new_creature.x = self.generate_x()
        new_creature.y = self.generate_y()

        # scale evolution values
        new_creature.evolve()

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

    def init_window(self):
        pygame.init()
        self.render_display = pygame.display.set_mode((self.map_width * self.render_scale, self.map_height * self.render_scale))
        pygame.display.set_caption("Evolution Simulator")
        

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
                    index = -1
                    highest_energy = 0
                    for c in range(len(self.creatures)):
                        if self.creatures[c].energy > highest_energy:
                            index = c
                            highest_energy = self.creatures[c].energy

                    print(f"Creatures: {len(self.creatures)} | Best Creature; Move Weights (E, A, F): {round(self.creatures[index].move_escape_weight, 3)}, {round(self.creatures[index].move_attack_weight, 3)}, {round(self.creatures[index].move_food_weight, 3)}, Weight: {round(self.creatures[index].weight, 3)}, Speed: {round(self.creatures[index].speed, 3)}, Eyesight: {round(self.creatures[index].eyesight, 3)}")
                self.draw_objects()
            last_run = time.time() - start_run

    def __init__(self, foods_count, creatures_start):
        self.init_window()

        for creature_type, percent in self.creatures_spawn:
            for i in range(int(math.floor(creatures_start * percent))):
                creature_init = creature_type()
                creature_init.x = self.generate_x()
                creature_init.y = self.generate_y()
                self.creatures.append(creature_init)

        self.init_food(foods_count)

        self.run_sim(foods_count)