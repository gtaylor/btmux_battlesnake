.. _settings:

.. include:: global.txt

Settings
========

When Battlesnake is started, the path to your config file is passed in
via the ``-c`` flag. Default values are pulled from
``battlesnake/config/defaults.cfg``. Any of the values detailed below may
be overridden in your config file.

MUX settings
------------

``hostname``
    The hostname or IP address of your game. **Must be overridden in your
    config file**.
``port``
    The port to connect to. **Must be overridden in your
    config file**.

Account settings
----------------

``username`` (default: Battlesnake)
    The player username to connect as.
``password``
    The player's password. **Must be overridden in your
    config file**.

Bot settings
------------

``keepalive_interval`` (default: 30.0)
    Sets the interval (seconds) at which the bot sends an IDLE command to the MUX.
    This is useful to prevent timeouts over NATs.
``monitor_expire_check_interval`` (default: 1.0)
    Sets the interval (seconds) for when the response monitor loops through
    all pending monitors and expires past-due entries. This should probably
    not go into double digits.