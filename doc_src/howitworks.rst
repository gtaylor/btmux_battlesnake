.. _how_it_works:

.. include:: global.txt

How it works
============

Battlesnake is powered by Python_ and Twisted_. The bot connects to your
game over telnet, just like a user would. It sets some semi-random tokens
on its player object that allows your softcode to communicate with it
via ``@pemit``.

Your softcoded commands end up being mostly for gathering up the relevant
data to ``@pemit`` to Battlesnake. If the commands need to send a reply
back out to a player, the bot does so with ``@pemit`` as well.

What is Battlesnake ideally suited for?
---------------------------------------

Battlesnake is best used for larger, more complicated systems that would be
easier maintained in Python_ than softcode. Battlesnake may be paired with
your choice of database or data store, with softcode commands used to
feed game state data to Battlesnake. The bot can also pull things from the
game on its own if you show it how to.

Example usage cases
-------------------

A few ideas for neat things Battlesnake can be used for:

* Web-based character creation
* Adding an HTTP API for your website's use
* Tweeting/SMS'ing/emailing certain events to your playerbase
* Very detailed player stat tracking (perhaps shown on your website)
* Stuffing arbitrary bits of data into a full-fledged database
* External AI
* Web-integrated bulletin board systems
* Economic simulations
* Research/industrial/assembly systems
