import blinker

# Fired when a unit is taken over by AI.
on_unit_ai_started = blinker.signal('ai:on_unit_ai_started')
