from twisted.internet.defer import inlineCallbacks

from battlesnake.core.base_plugin import BattlesnakePlugin

from battlesnake.plugins.contrib.pg_db.api import get_db_connection


class PGDBPlugin(BattlesnakePlugin):
    """
    Plugin for accessing an external Postgres DB. Doesn't do much other
    than establish the connection and provide a common place for all other
    plugins to get a cursor instance from. See the ``api`` submodule
    within ``pg_db``.
    """

    @inlineCallbacks
    def do_after_plugin_is_loaded(self):
        # Causes the lazy loading to happen.
        yield get_db_connection()
