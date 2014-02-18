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

``keepalive_interval`` (default: 30.0)
    Sets the interval (seconds) at which the bot sends an IDLE command to the MUX.
    This is useful to prevent timeouts over NATs.
``response_watcher_expire_check_interval`` (default: 1.0)
    Sets the interval (seconds) for how often to check for stale response
    watchers to purge.
``enable_hudinfo`` (default: False)
    If True, generate and send a HUDINFO key. This will allow you to start
    using HUDINFO commands.

[commands]
----------

``inbound_tables`` (default: battlesnake.inbound_commands.bot_management.tables.BotManagementCommandTable)
    A comma-separated list of InboundCommandTable sub-classes to register.
    These are full Python paths.

[triggers]
----------

``tables`` (default: battlesnake.triggers.examples.tables.ExampleTriggerTable)
    A comma-separated list of TriggerTable sub-classes to register.
    These are full Python paths.

[timers]
--------

``tables`` (default: battlesnake.timers.bot_misc.tables.BotMiscTimerTable)
    A comma-separated list of TimerTable sub-classes to register.
    These are full Python paths.
