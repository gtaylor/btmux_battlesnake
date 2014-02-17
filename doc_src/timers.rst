.. _timers:

.. include:: global.txt

Timers
======

Battlesnake's timers work much like a traditional MU* client's in that
they are used to perform an action every so often. There are two kinds of
timers:

* :py:mod:`battlesnake.core.timers.IntervalTimer`
* :py:mod:`battlesnake.core.timers.CronTimer`

Timers of the :py:mod:`IntervalTimer <battlesnake.core.timers.IntervalTimer>`
type are executed on intervals measured in seconds. For example, "Do
something every 30 seconds".

Timers of the :py:mod:`CronTimer <battlesnake.core.timers.CronTimer>` type
execute tasks at pre-set times during the day. For example, "Do something
on the 30th minute of every hour of the day". Use these when you want
to get very specific with execution times.

Common usage cases
------------------

We'll outline a few common usage cases for Timers, for the sake of providing
some ideas. These aren't the only uses, though.

Retrieving data
^^^^^^^^^^^^^^^

Battlesnake has to either retrieve or be fed data from your game in order
to stay in sync with what is going on. Timers are a great way to achieve
that.

Some example ways to do this:

* Run the :py:func:`battlesnake.outbound_commands.mux_commands.think` command
  to retrieve specific values of interest.
* Run various softcode commands in your game whose output is picked up
  by :doc:`triggers` within Battlesnake. This is good for when you have a
  very large volume of data to retrieve (which may be a lot more involved
  to pick up via
  :py:func:`think <battlesnake.outbound_commands.mux_commands.think>`.


Economy/weather ticks
^^^^^^^^^^^^^^^^^^^^^

Economy and weather simulations are some of the more bulky, nasty bits of
softcode in your typical BTMUX. These are excellent candidates to move into
Battlesnake. Timers are important pieces of both Economy and weather-related
things.

Stat collection
^^^^^^^^^^^^^^^

If you are tracking certain time-series data points (like # of users connected),
timers are a great way to make sure you are getting points the correct
interval.
