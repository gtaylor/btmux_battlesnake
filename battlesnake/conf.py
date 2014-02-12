import os
import sys
import inspect

from configobj import ConfigObj, flatten_errors
# noinspection PyPackageRequirements
from validate import Validator

# This is populated with a ConfigObj by read_config(). All settings values
# should be accessed through here.
settings = None


def read_config(config_file):
    """
    Reads in the default config values, followed by the user's
    config file.

    :param basestring config_file: The user's config file to read in.
    """

    global settings

    check_for_config_file(config_file)

    project_root = os.path.dirname(os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))))
    configspec = os.path.join(project_root, 'config', 'configspec.cfg')
    settings = ConfigObj(config_file, configspec=configspec)
    results = settings.validate(Validator())
    if results is True:
        # Everything went fine. We're done here.
        return
    # Config file validation failed. Provide as much help as we can.
    print "There were configuration error(s) in %s" % config_file
    for (section_list, key, _) in flatten_errors(settings, results):
        if key is not None:
            print '  Error: The "%s" key in the config section "%s" failed validation' % (
                key, ', '.join(section_list),
            )
        else:
            print '  Error: The "%s" config section was missing' % (
                ', '.join(section_list),
            )
    print "If in doubt, see: http://battlesnake.readthedocs.org/settings.html"
    sys.exit(1)


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
