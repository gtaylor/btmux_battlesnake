.. _settings:

.. include:: global.txt

Settings
========

When Battlesnake is started, the path to your config file is passed in
via the ``-c`` flag. Default values are pulled from
``battlesnake/config/configspec.cfg``. Any of the values detailed below may
be overridden in your config file.

The name in brackets in each section below is the section name in the
config file.

[mux]
-----

``hostname``
    The hostname or IP address of your game. **Must be overridden in your
    config file**.
``port``
    The port to connect to. **Must be overridden in your
    config file**.

[account]
---------

``username`` (default: Battlesnake)
    The player username to connect as.
``password``
    The player's password. **Must be overridden in your
    config file**.

[bot]
-----

``response_watcher_expire_check_interval`` (default: 1.0)
    Sets the interval (seconds) for how often to check for stale response
    watchers to purge.
``enable_hudinfo`` (default: False)
    If True, generate and send a HUDINFO key. This will allow you to start
    using HUDINFO commands.
``extra_services`` (default: [])
    A list of Python paths to loader functions that return a Service.
    If you only have one item to add to the list, make sure there is a
    trailing comma or you'll get a validation error. A comma causes our
    config system to convert the string to a list.
``plugins`` (default: 'battlesnake.plugins.example_plugin.plugin.ExamplePlugin','battlesnake.plugins.nat_idler.plugin.NatIdlerPlugin')
    A comma-separated list of BattlesnakePlugin sub-classes to register.
    Plugins can contain :doc:`triggers`, :doc:`timers`, and commands.

Plugins
-------

[nat_idler]
^^^^^^^^^^^

``keepalive_interval`` (default: 30.0)
    Sets the interval (seconds) at which the bot sends an IDLE command to the MUX.
    This is useful to prevent timeouts over NATs.

[unit_spawning]
^^^^^^^^^^^^^^^

``unit_parent_dbref`` (default: #66)
    Your mech/unit parent's dbref.

[ai]
^^^^

``ai_parent_dbref`` (default: #69)
    Your AI parent's dbref.
