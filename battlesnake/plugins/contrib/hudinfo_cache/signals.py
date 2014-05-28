import blinker

# Fired when a stale unit has been removed from the store.
on_stale_unit_removed = blinker.signal('hudinfo_cache:on_stale_unit_removed')
# Fired when we detect a unit that isn't in the cache yet.
on_new_unit_detected = blinker.signal('hudinfo_cache:on_new_unit_detected')
on_unit_destroyed = blinker.signal('hudinfo_cache:on_unit_destroyed')

# TODO: Rename to on_shot_landed?
on_hit_landed = blinker.signal('hudinfo_cache:on_hit_landed')
on_shot_missed = blinker.signal('hudinfo_cache:on_shot_missed')

on_unit_state_changed = blinker.signal('hudinfo_cache:on_unit_state_changed')