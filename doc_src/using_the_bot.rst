.. _using_the_bot:

.. include:: global.txt

Getting started using the Bot
=============================

At this point, we assume that your bot is connected to your game. The first
thing you'll want to do is ``examine`` your bot's player object. We'll also
assume that its name is ``Battlesnake``. You should see three attributes
like these::

    BATTLESNAKE_PREFIX.D: @G$>
    BATTLESNAKE_KWARG_DELIMITER.D: &R^
    BATTLESNAKE_LIST_DELIMITER.D: #E$

.. tip:: Note these values, as we'll be using them in the examples below.

You'll also want to note your bot's dbref.
We'll use the dbref ``#123`` as a placeholder.

A crude botinfo example
-----------------------

Now choose an object to put a command on. This could be in your master room
or in your current location. Here's the attribute we'll set::

    BOTINFO.C: $botinfo:think [u(#47/SET_BOT_REGISTERS.F)][u(#47/SENDPACKET.F,botinfo)]

Breaking this down, ``SET_BOT_REGISTERS.F`` sets some %q registers that
``SENDPACKET.F`` uses to form a ``pemit()`` call to a connected bot.
The ``botinfo`` command is being sent to the bot.

You'll probably want to set your bot ``WIZARD`` first, then try running your
new ``botinfo`` command within your MUX. If everything is set up correctly,
you should see a response with some info about the bot.

Moving on from here
-------------------

The next step is to read over the :doc:`protocol` and start thinking big!
