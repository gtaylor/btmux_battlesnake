from battlesnake.core.ansi import ANSI_HI_GREEN, ANSI_HI_YELLOW, ANSI_HI_RED, \
    ANSI_HI_MAGENTA

# Maps a lowercase weight class nam to a WHERE filter SQL.
WEIGHT_CLASS_SQL_MAP = {
    'light': 'weight < 40',
    'medium': 'weight >= 40 AND weight < 60',
    'heavy': 'weight >= 60 AND weight < 80',
    'assault': 'weight >= 80'
}

UNIT_TYPE_SQL_MAP = {
    'mech': "unit_type='Mech'",
    'tank': "unit_type='Vehicle'",
    'vtol': "unit_type='VTOL'",
    'battlesuit': "unit_type='Battlesuit'",
}

# We use a consistent set of colors for each weight class.
UNIT_WCLASS_LIGHT_COLOR = ANSI_HI_GREEN
UNIT_WCLASS_MEDIUM_COLOR = ANSI_HI_YELLOW
UNIT_WCLASS_HEAVY_COLOR = ANSI_HI_RED
UNIT_WCLASS_ASSAULT_COLOR = ANSI_HI_MAGENTA
