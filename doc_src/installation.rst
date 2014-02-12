.. _installation:

.. include:: global.txt

Installation
============

Battlesnake is developed on GitHub_ in a git_ repository. We don't do any
point releases at this time, as things are still evolving, and the expected
audience for this software is pretty niche.

The first thing to do is retrieve a clone of the repository::

    git clone https://github.com/gtaylor/btmux_battlesnake.git

This will leave you with a ``btmux_battlensake`` directory. ``cd`` into it::

    cd btmux_battlesnake

Now install the requirements via ``pip``, preferrably within a virtualenv_
(you are using virtualenv, right?)::

    pip install -r requirements.txt

If you want to be able to generate documentation locally or run the test
suite, install the developer dependencies::

    pip install -r requirements_dev.txt

Now copy the starter config file and adjust the ``hostname``, ``port``,
``username``, and ``password`` values::

    cp config/battlesnake.cfg.dist battlesnake.cfg
    vim battlesnake.cfg (Or whatever your preferred editor is)

You are now ready to run the bot (from within ``btmux_battlesnake``)::

    twistd -n battlesnake

This defaults to using the ``battlesnake.cfg`` file in your current directory,
but you can run multiple bots or use an alternative location with the ``-c`` flag::

    twistd -n battlesnake -c battlesnake.cfg

When in doubt, check out the help listing::

    twistd -n battlesnake -h

.. tip:: You will not be able to run battlesnake unless your current
    directory is ``btmux_battlesnake`` (or whatever you have renamed it to).
    This is a limitation of Twisted's plugin system.

For more details on settings, check out :doc:`settings`.