import os
import inspect
import sys
import ConfigParser

settings = ConfigParser.SafeConfigParser()

REQUIRED_SETTINGS = {
    'mux': [
        'hostname', 'port'
    ],
    'account': [
        'password',
    ],
}


def read_config(config_file):
    """
    Reads in the default config values, followed by the user's
    config file.

    :param basestring config_file: The user's config file to read in.
    """

    project_root = os.path.dirname(os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))))
    check_for_config_file(config_file)
    default_config_file = os.path.join(project_root, 'config', 'defaults.cfg')
    settings.read([default_config_file, config_file])
    validate_config()


def check_for_config_file(config_file):
    """
    Makes sure the specified config file exists. If it doesn't, shit a brick
    and put on the brakes.

    :param basestring config_file: The full, absolute path to the config file.
    """

    if os.path.exists(config_file):
        # Hooray!
        return

    print "Error: No such config file found: %s" % config_file
    sys.exit(1)


def validate_config():
    """
    Really cheesy way to check for a few required values that we can't provide
    defaults for. If we come up short, show an error message and sys.exit.
    """

    global settings, REQUIRED_SETTINGS

    for section, req_settings in REQUIRED_SETTINGS.items():
        for req_setting in req_settings:
            try:
                value = settings.get(section, req_setting)
            except ConfigParser.NoOptionError:
                print "Error: Missing config value for the '%s' setting in the [%s] section." % (
                    req_setting, section)
                sys.exit(1)
            if value == "CHANGE_ME":
                print(
                    "Error: Replace the default CHANGE_ME config value for the '%s' "
                    "setting in the [%s] section.") % (
                        req_setting, section)
                sys.exit(1)
