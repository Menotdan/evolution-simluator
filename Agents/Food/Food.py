from random import randint

class Food:
    # state
    x = 0
    y = 0
    energy = 10
    alive = True

    # constants
    energy_min = 25
    energy_max = 40

    def __init__(self):
        self.energy = float(randint(self.energy_min, self.energy_max))