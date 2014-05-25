import blinker

# Fired when a new unit is spawned and placed on a map.
on_unit_spawned = blinker.signal('unit_spawning:on_unit_spawned')
