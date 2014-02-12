.. _protocol:

.. include:: global.txt

Battlesnake protocol
====================

Battlesnake communicates over ``@pemit``, using strings broken up with
multi-character delimiters for various purposes. While the protocol is crude
and makes some assumptions, it is reliable enough for heavy usage.

Inbound vs Outbound commands
----------------------------

Battlesnake has a notion of *inbound* and *outboud* commands. Outbound
commands are those performed by the bot, sending text to the game. Inbound
commands are ``@pemit`` strings asking the bot to do something, typically
from your softcode.

This document will mostly focus on inbound commands, as that is where most
of the challenge is.

A high level overview of inbound command syntax
-----------------------------------------------

An simple inbound command ``@pemit`` syntax example::

    <prefix_str><command_name><kwarg_delim><invoker_dbref>

Breaking this down by component:

**<prefix_str>**
    A randomized multi-character string that is set on the bot's player object
    when it connects. If the bot sees this at the beginning of a line of input,
    it knows to look **command_name** up in its command table.

**<command_name>**
    This is the command name that Battlesnake will look up in its internal
    command table. For example, *send_email*.

**<kwarg_delim>**
    This is another randomly generated multi-character string that is used
    to separate bits of input to send to the bot. Almost all data (save
    for the invoker's dbref) is in key=value form, separated by this delimiter.

**<invoker_dbref>**
    This is the object on the MUX that is sending the command. The most common
    use for this is to give the bot a way to reply to the invoker.

Here's an example inbound command with no additional data::

    PREFIXSTRsend_emailKWDELIM#212

``<prefix_str>`` is ``PREFIXSTR``, ``<command_name>`` is ``send_email``,
``<kwarg_delim>`` is ``KWDELIM``, and ``<invoker_dbref>`` is ``#212``.

Sending key/value data with inbound commands
--------------------------------------------

We know how to send inbound commands now, but this isn't too useful unless
we can also send in arbitrary bits of data. Expanding on our previous
example, here's how that works::

    <prefix_str><command_name><kwarg_delim><invoker_dbref><kwarg_delim>key1=value1<kwarg_delim>key2=value2

As you can see, **kwarg_delim** is used to split up key/value pairs. On the
Battlesnake side, we convert these into Python dicts. Here's how the command
parser would split this up:

.. code-block:: python

    {'key1': 'value1', 'key2': 'value2'}

But what if we omit a value for a key?

.. code-block:: python

    <kwarg_delim>key1=<kwarg_delim>
    {'key1': ''}

Sending lists values
--------------------

Sometimes we'll need to send lists instead of individual values::

    <kwarg_delim>key=item1<list_delim>item2

We've introduced a new delimiter, **list_delim**. Much like **prefix_str**
and **kwarg_delim**, this is a randomly generated multi-character delimiter.
The presence of a list delimiter in a kwarg's value causes it to be converted
to a list in Battlesnake. Let's say we do something like this (omitted
invoker/command name/prefix for brevity)::

    <kwarg_delim>key=item1<list_delim>item2<list_delim>item3

Within Battlesnake, this would be interpreted as:

.. code-block:: python

    {'key': ['item1', 'item2', 'item3']}

You can combine regular string values and list values without issue::

    <kwarg_delim>key1=value1<kwarg_delim>key2=item1<list_delim>item2<list_delim>item3

In Python land, this would be interpreted as:

.. code-block:: python

    {
        'key1': 'value1',
        'key2': ['item1', 'item2', 'item3']
    }

Protocol limitations
--------------------

The Battlesnake protocol only knows of two different data types: strings and
lists. Your logic on the Python side will need to know how to treat the data
being passed in. If you need ints, you'll need to cast them and potentially
handle errors.

While the delimiter characters should be random enough to avoid collisions,
if your softcode were to generate values that matched one of the delimiters,
kwarg pairs could be discarded. The likelihood of this happening is incredibly
low, though, unless your data is sufficiently random and large.