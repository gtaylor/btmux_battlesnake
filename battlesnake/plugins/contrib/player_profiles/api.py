import datetime

from twisted.internet.defer import inlineCallbacks

from battlesnake.plugins.contrib.pg_db.api import get_db_connection


@inlineCallbacks
def create_new_player(username, email):
    """
    This is a really crappy, basic user creation call that we'll use until
    the website has a means of doing this.

    :param str username:
    :param str email:
    """

    alias = ''
    password = ''
    now = datetime.datetime.now()

    conn = yield get_db_connection()
    query_str = (
        'INSERT INTO accounts_sosuser'
        '  (username, alias, email, password, last_login, is_superuser, is_staff,'
        '   date_joined, is_active)'
        '  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
    )
    value_tuple = (
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
