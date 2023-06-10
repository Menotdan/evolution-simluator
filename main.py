import math
import time
import pygame
from pygame.locals import *
import numpy as np
from random import random, randint

from Agents.Food.Food import Food

MOVE_FOOD = 0
MOVE_ESCAPE = 1
MOVE_ATTACK = 2
MOVE_WANDER = 3

clamp = lambda x, l, u: l if x < l else u if x > u else x

class Creature:
    # constants
    move_weights_change_scale = 0.075
    speed_change_scale = 0.08
    weight_change_scale = 1.25
    eyesight_change_scale = 4
    object_collision_box_edge = 1

    movement_energy_tuning = 0.5
    eyesight_energy_tuning = 0.2
    weight_power_factor = 25

    weight_min = 1
    eyesight_min = 0
    speed_min = 0
    action_weight_min = 0

    # state
    x = 0
    y = 0
    energy = 50
    alive = True

    # evolution
    speed = 1 # coordinate movement per time unit
    weight = 15 # lets you store more energy (energy_max_by_weight_scale * weight) but costs more energy per tile movement ((weight / energy_max_by_weight_scale)*tiles)
    eyesight = 75 # distance you can see, but costs more energy per time unit (eyesight / eyesight_energy_cost_scale) per time

    # movement weights (the max of these is the action performed)
    move_food_weight = 2.0   # ((eyesight - food_distance) * move_food_weight) * (food.energy / 10)
    move_escape_weight = 3.0 # ((eyesight - escape_distance) * move_escape_weight) * ((escape.energy / self.energy))
    move_attack_weight = 1.0 # ((eyesight - attack_distance) * move_attack_weight) * (self.energy / attack.energy)

    def run_ai(self, creatures, food):
        if self.alive == False:
            return

        creatures_copy: list[Creature] = creatures[:]
        visible_creatures: list[Creature] = []
        for c in range(len(creatures_copy)):
            if creatures[c] == self:
                continue
            distance = get_distance(self, creatures_copy[c])
            if distance <= self.eyesight:
                visible_creatures.append((creatures[c], distance))
        del creatures_copy

        food_copy: list[Food] = food[:]
        visible_food: list[Food] = []
        for f in range(len(food_copy)):
            distance = get_distance(self, food_copy[f])
            if distance  <= self.eyesight:
                visible_food.append((food[f], distance))
        del food_copy

        closest_food: Food = None
        closest_food_distance = self.eyesight + 100 # arbitrary

        closest_escape: Creature = None
        closest_escape_distance = self.eyesight + 100 # arbitrary

        closest_attack: Creature = None
        closest_attack_distance = self.eyesight + 100 # arbitrary

        for c, d in visible_creatures:
            if c.energy < self.energy:
                if d < closest_attack_distance:
                    closest_attack = c
                    closest_attack_distance = d
            else:
                if d < closest_escape_distance:
                    closest_escape = c
                    closest_escape_distance = d
        
        for f, d in visible_food:
            if d < closest_food_distance:
                closest_food = f
                closest_food_distance = d
        
        food_weight, escape_weight, attack_weight = (-1, -1, -1)

        if closest_food != None:
            food_weight = ((self.eyesight - closest_food_distance) * self.move_food_weight) * (closest_food.energy / 10)
        if closest_escape != None:
            escape_weight = ((self.eyesight - closest_escape_distance) * self.move_escape_weight) * (closest_escape.energy / max(0.1, self.energy)) / 3
        if closest_attack != None:
            attack_weight = ((self.eyesight - closest_attack_distance) * self.move_attack_weight) * (self.energy / max(0.1, closest_attack.energy)) / 3

        chosen_action = MOVE_WANDER
        if food_weight > escape_weight and food_weight > attack_weight:
            chosen_action = MOVE_FOOD
        elif escape_weight > food_weight and escape_weight > attack_weight:
            chosen_action = MOVE_ESCAPE
        elif attack_weight > food_weight and attack_weight > escape_weight:
            chosen_action = MOVE_ATTACK
        
        move_direction = None
        if chosen_action == MOVE_WANDER:
            move_direction = self.wander_behaviour()
        elif chosen_action == MOVE_FOOD:
            move_direction = self.get_move_towards_vector(closest_food)
        elif chosen_action == MOVE_ATTACK:
            move_direction = self.get_move_towards_vector(closest_attack)
        elif chosen_action == MOVE_ESCAPE:
            move_direction = self.get_move_away_vector(closest_escape)
            if move_direction[0] <= 0 and move_direction[1] <= 0:
                move_direction = self.wander_behaviour()

        self.x += move_direction[0]
        self.y += move_direction[1]

        self.apply_move_energy_cost(self.speed)
        self.energy -= ((self.eyesight / 40) * self.eyesight_energy_tuning)
        if self.energy <= 0:
            self.alive = False

    def normalize_vector(self, vec):
        if np.linalg.norm(vec, ord=1) == 0:
            return [0.0, 0.0]
        norm_vec = (vec / np.linalg.norm(vec, ord=1))
        return list(norm_vec * self.speed)
    
    def wander_behaviour(self):
        move_direction = np.asarray([(random() - 0.5) * 2, (random() - 0.5) * 2])
        move_direction = self.normalize_vector(move_direction)

        return move_direction

    def get_move_towards_vector(self, object):
        move_direction = np.asarray([object.x - self.x, object.y - self.y])
        move_direction = self.normalize_vector(move_direction)

        return move_direction

    def get_move_away_vector(self, object):
        move_direction = np.asarray([self.x - object.x, self.y - object.y])
        move_direction = self.normalize_vector(move_direction)

        return move_direction
    
    def would_win(self, fighter):
        if fighter.energy > self.energy:
            return False
        return True

    def collides(self, object):
        if get_distance(self, object) <= self.object_collision_box_edge:
            return True
        return False
    
    def evolve(self):
        self.weight = max(get_new_value(self.weight, self.weight_change_scale), self.weight_min)
        self.speed = max(get_new_value(self.speed, self.speed_change_scale), self.speed_min)
        self.eyesight = max(get_new_value(self.eyesight, self.eyesight_change_scale), self.eyesight_min)

        self.move_attack_weight = max(get_new_value(self.move_attack_weight, self.move_weights_change_scale), self.action_weight_min)
        self.move_food_weight = max(get_new_value(self.move_food_weight, self.move_weights_change_scale), self.action_weight_min)
        self.move_escape_weight = max(get_new_value(self.move_escape_weight, self.move_weights_change_scale), self.action_weight_min)
    
    def apply_move_energy_cost(self, distance):
        self.energy -= ((self.weight / math.pow(7, self.weight_power_factor/self.weight)) * distance * self.movement_energy_tuning)

def get_new_value(old: float, scale: float):
    return old + ((random() - 0.5) * 2) * scale

def get_distance(object1, object2):
    return math.sqrt(math.pow(object1.x - object2.x, 2) + math.pow(object1.y - object2.y, 2))

def clamp_movement(c: Creature, limit_x, limit_y):
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
            clamped_distance = clamp_movement(c, self.map_width, self.map_height)
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

        

game = Game(100, 50)
print("Game end.")