# Food

## Description
`Food` is the class of objects that are used to supply energy to [Creatures](../Creatures/Creature.md).

## Functions
* `draw_object(display_surface: pygame.Surface, render_scale: float)`
  - This function is used to draw the object to the screen. This must be overloaded in your custom `Food` classes in order for them to be drawn. You can also leave it unimplemented to not draw your objects.
* `eaten(eaten_by: Creature)`
  - This function gets called when the food is eaten. Using this you can apply effects to the `Creature` that ate the `Food`. You don't need to overload this if you just want the energy the `Food` has to be given to the `Creature`. If you want to, for example, prevent certain creatures from eating certain food, you can subtract the `Food`'s energy from the `Creature`'s if it matches the type you are concerned about.
* `__init__()`
  - This is where you might want to set up the `Food`'s energy value, maybe you want it to be random, then you could initilalize it here. If your `Food` implements any other important functionality you can also set that up here. Not important by default, assuming you give your `Food` an energy value.