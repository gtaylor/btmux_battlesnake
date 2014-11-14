from twisted.internet.defer import inlineCallbacks, returnValue
from txpostgres import reconnection

from battlesnake.conf import settings
from battlesnake.plugins.contrib.pg_db.dict_conn import DictConnection

__DBCONN = DictConnection(detector=reconnection.DeadConnectionDetector())
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
        pg_hostname = settings['pg_db']['pg_hostname']
        pg_port = settings['pg_db']['pg_port']
        pg_dbname = settings['pg_db']['pg_dbname']
        pg_username = settings['pg_db']['pg_username']
        pg_password = settings['pg_db']['pg_password']

        connection_pairs = [
            'dbname=%s' % pg_dbname,
            'user=%s' % pg_username,
            'password=%s' % pg_password,
            'port=%s' % pg_port
        ]

        if pg_hostname:
            connection_pairs.append('host=%s' % pg_hostname)

        connect_str = ' '.join(connection_pairs)
        print "CONN STR", connect_str
        __DB = yield __DBCONN.connect(connect_str)
    returnValue(__DB)
