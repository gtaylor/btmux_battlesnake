import psycopg2
import psycopg2.extras
from txpostgres import txpostgres


def dict_connect(*args, **kwargs):
    kwargs['connection_factory'] = psycopg2.extras.DictConnection
    return psycopg2.connect(*args, **kwargs)


class DictConnection(txpostgres.Connection):
    connectionFactory = staticmethod(dict_connect)
