from Agents.Creatures.Creature import Creature
from Agents.Food.Food import Food
from math_utils import normalize_vector, clamp, get_distance, get_new_value, get_move_towards_vector, get_move_away_vector
import numpy as np
from random import *
import math
import pygame

MOVE_FOOD = 0
MOVE_ESCAPE = 1
MOVE_ATTACK = 2
MOVE_WANDER = 3

RED =  (200, 0, 0)

class Creature_Default(Creature):
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
            move_direction = get_move_towards_vector(self, closest_food)
        elif chosen_action == MOVE_ATTACK:
            move_direction = get_move_towards_vector(self, closest_attack)
        elif chosen_action == MOVE_ESCAPE:
            move_direction = get_move_away_vector(self, closest_escape)
            if move_direction[0] <= 0 and move_direction[1] <= 0:
                move_direction = self.wander_behaviour()

        self.x += move_direction[0]
        self.y += move_direction[1]

        self.apply_move_energy_cost(self.speed)
        self.energy -= ((self.eyesight / 40) * self.eyesight_energy_tuning)
        if self.energy <= 0:
            self.alive = False
    
    def child_count(self):
        return math.floor(max(0, min(randint(1, 2), self.energy / self.weight / 15)))
    
    def wander_behaviour(self):
        move_direction = np.asarray([(random() - 0.5) * 2, (random() - 0.5) * 2])
        move_direction = normalize_vector(move_direction)

        return move_direction * self.speed
    
    def would_win(self, fighter):
        if fighter.energy > self.energy:
            return False
        return True

    def lost_fight(self, fighter):
        self.alive = False

    def won_fight(self, fighter):
        self.energy += fighter.energy / 2

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

    def copy(self):
        return_object = Creature_Default()
        return_object.weight = self.weight
        return_object.speed = self.speed
        return_object.eyesight = self.eyesight

        return_object.move_attack_weight = self.move_attack_weight
        return_object.move_food_weight = self.move_food_weight
        return_object.move_escape_weight = self.move_escape_weight

        return_object.energy = self.weight * 5

        return return_object
    
    def draw_object(self, display_surface, render_scale):
        pygame.draw.circle(display_surface, RED, (self.x * render_scale, self.y * render_scale), self.object_collision_box_edge * 4 * render_scale)

    def __init__(self):
        super().__init__()
        self.energy = self.weight * 5
