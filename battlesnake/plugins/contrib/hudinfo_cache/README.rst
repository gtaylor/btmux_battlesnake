HUDINFO Cache
=============

This module contains everything needed in order to make a bot that sits in
an Observation Lounge, pulling map/unit state and caching it in memory.

The original purpose of this contrib module was to pull in map/unit data,
store it in memory, then broadcast it out over Websockets. However, this
could be useful for all sorts of other cases, as well.