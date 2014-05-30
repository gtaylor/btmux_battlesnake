from twisted.internet.defer import inlineCallbacks, returnValue
from txpostgres import txpostgres, reconnection

from battlesnake.conf import settings

__DBCONN = txpostgres.Connection(detector=reconnection.DeadConnectionDetector())
__DB = None


@inlineCallbacks
def get_db_connection():
    """
    Lazy load a DB connection that is ready for queries.

    :rtype: txpostgres.txpostgres.Connection
    :returns: A Connection object that has authenticated and is ready for queries.
    """

    global __DB

    if not __DB:
        pg_dbname = settings['pg_db']['pg_dbname']
        pg_username = settings['pg_db']['pg_username']
        pg_password = settings['pg_db']['pg_password']

        connect_str = 'dbname={pg_dbname} user={pg_username} password={pg_password}'.format(
            pg_dbname=pg_dbname, pg_username=pg_username, pg_password=pg_password)
        __DB = yield __DBCONN.connect(connect_str)
    returnValue(__DB)
