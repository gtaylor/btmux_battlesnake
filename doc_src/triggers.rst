.. _triggers:

.. include:: global.txt

Triggers
========

Battlesnake's triggers work much like a traditional MU* client's in that
a key phrase sets off an action. The primary use for triggers in Battlesnake
is for data collection, though it can be used for a number of other
purposes.

A :py:class:`Trigger <battlesnake.core.triggers.Trigger>` consists of a regular
expression that determines what to look for, and a function to run when
a match is made. The neat thing about Python regular expressions is that
we can use regex groups to break the matches up into useful pieces. For
example, if a trigger has the following regex:

.. code-block:: python

    line_regex = re.compile(r'(?P<talker>.*) says "[Hh]ello"')

Our ``run`` method on the :py:class:`Trigger <battlesnake.core.triggers.Trigger>`
can address each group individually:

.. code-block:: python

    talkers_name = re_match.group("talker")
    response = "Why hello there, {talkers_name}.".format(talkers_name=talkers_name)
    mux_commands.say(protocol, response)

In the case of the previous example, anyone saying "Hello" to the bot would
be greeted back::

    You say "Hello"
    Battlesnake says "Why hello there, Kelvin McCorvin."

Note how the original speaker's name comes back.

Common usage cases
------------------

We'll outline a few common usage cases for Triggers, for the sake of providing
some ideas. These aren't the only uses, though.

Retrieving data
^^^^^^^^^^^^^^^

If you have a large amount of data to feed your bot on a regular basis,
you can use triggers and :doc:`timers` in conjunction with one another to do
so. Perhaps you write a softcode command that your bot executes with a timer,
picking the output up with a trigger. Or maybe your game has a task scheduling
system interally which can be used to ``@pemit`` a string matching one of your
triggers in order to feed data in.

Event monitoring
^^^^^^^^^^^^^^^^

Triggers can be used to watch for certain events. Perhaps you join your bot
to the **MUXConnections** channel and set up a trigger to note when players
log in. Or maybe you park your bot in an Observation Lounge and use triggers
to record shot stats or respond to base capture emits.
