import blinker


# This signal is used by our timers to send unit data to all connected clients.
unit_store_contents_signal = blinker.signal('unit_store_contents_signal')
