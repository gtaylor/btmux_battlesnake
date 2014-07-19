import datetime

from twisted.internet.defer import inlineCallbacks

from battlesnake.plugins.contrib.pg_db.api import get_db_connection


@inlineCallbacks
def add_existing_player_to_db(player_dbref, username, email):
    """
    This is a really crappy, basic user creation call that we'll use until
    the website has a means of doing this.

    :param str player_dbref:
    :param str username:
    :param str email:
    """

    alias = ''
    password = ''
    now = datetime.datetime.now()

    conn = yield get_db_connection()
    query_str = (
        'INSERT INTO accounts_sosuser'
        '  (id, username, alias, email, password, last_login, is_superuser, '
        '   is_staff, date_joined, is_active)'
        '  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    )
    value_tuple = (
        int(player_dbref[1:]),
        username,
        alias,
        email,
        password,
        # last_login
        now,
        # is_superuser
        False,
        # is_staff
        False,
        # date_joined
        now,
        # is_active
        True,
    )

    yield conn.runOperation(query_str, value_tuple)
