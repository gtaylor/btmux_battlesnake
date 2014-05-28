import blinker

# Fired when a stale unit has been removed from the store.
on_stale_unit_removed = blinker.signal('arena_master:on_stale_unit_removed')
# Fired when we detect a unit that isn't in the cache yet.
on_new_unit_detected = blinker.signal('arena_master:on_new_unit_detected')
on_unit_destroyed = blinker.signal('arena_master:on_unit_destroyed')

on_shot_landed = blinker.signal('arena_master:on_hit_landed')
on_shot_missed = blinker.signal('arena_master:on_shot_missed')

on_unit_state_changed = blinker.signal('arena_master:on_unit_state_changed')
