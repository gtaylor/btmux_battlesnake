from twisted.internet.defer import inlineCallbacks

from battlesnake.conf import settings
from battlesnake.core.inbound_command_handling.base import CommandError
from battlesnake.outbound_commands.think_fn_wrappers import btloadmech, \
    btgetxcodevalue_ref, set_attrs, btdesignex


@inlineCallbacks
def load_ref_in_templater(protocol, unit_ref):
    """
    Loads a ref in the templater for scanning/manipulation.

    :param BattlesnakeTelnetProtocol protocol:
    :param str unit_ref: The unit reference to load.
    """

    p = protocol
    is_valid_ref = yield btdesignex(p, unit_ref)
    if not is_valid_ref:
        raise CommandError("Invalid unit reference.")

    templater_dbref = settings['unit_library']['templater_dbref']
    yield btloadmech(p, templater_dbref, unit_ref)
    # btloadmech() doesn't set the Mechname attrib, so we have to pull that
    # from the template file and set it on the object ourselves.
    mechname = yield btgetxcodevalue_ref(p, unit_ref, 'Mechname')
    yield set_attrs(p, templater_dbref, {'Mechname': mechname})
