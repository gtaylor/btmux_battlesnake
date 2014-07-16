import time

from twisted.internet.defer import inlineCallbacks, returnValue

from battlesnake.conf import settings
from battlesnake.plugins.contrib.ai.signals import on_unit_ai_started
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.outbound_commands import mux_commands


@inlineCallbacks
def start_unit_ai(
        protocol, unit_dbref, piloting_skill=3, gunnery_skill=3):
    """
    Creates and starts an AI on the given unit.

    :param BattlesnakeTelnetProtocol protocol:
    :param str unit_dbref: A MUX object string for the unit to AI'ify.
    :param int piloting_skill: Piloting skill value for the AI pilot.
    :param int gunnery_skill: Gunnery skill value for the AI pilot.
    :rtype: defer.Deferred
    :returns: A Deferred whose callback value will be the dbref of
        the newly created AI.
    """

    p = protocol
    ai_name = "UNIT-AUTOPILOT-{unit_dbref}".format(unit_dbref=unit_dbref)
    ai_dbref = yield think_fn_wrappers.create(protocol, ai_name, otype='t')
    # Dead mech/AI compactor dbref.
    compactor_dbref = settings['unit_spawning']['dead_mech_compactor_dbref']
    mux_commands.link(protocol, ai_dbref, compactor_dbref)
    yield think_fn_wrappers.teleport(protocol, ai_dbref, unit_dbref)
    # AI pilot is in place, set some attribs on him
    yield think_fn_wrappers.set_attrs(protocol, ai_dbref, {
        'Xtype': 'AUTOPILOT',
        'IS_AUTOPILOT': '1',
        'CREATED': time.time(),
    })
    # We can't set this with set(), have to use @set or @startup.
    yield mux_commands.startup(
        p, ai_dbref,
        '@fo me={disengage;delcommand -1;addcommand startup;addcommand autogun on;engage}',)
    # Now set some values on the mech that are needed to make things work.
    yield think_fn_wrappers.set_attrs(protocol, unit_dbref, {
        'MECHSKILLS': '%s %s' % (piloting_skill, gunnery_skill),
        'PILOT': ai_dbref,
        'IS_AI_CONTROLLED': '1',
    })
    flags = [
        'INHERIT', 'STAFF', 'XCODE', 'MONITOR', 'QUIET',
    ]
    # This activates the AI when the XCODE flag is set.
    yield think_fn_wrappers.set_flags(protocol, ai_dbref, flags)
    mux_commands.parent(p, ai_dbref, settings['ai']['ai_parent_dbref'])
    mux_commands.lock(p, ai_dbref, ai_dbref)
    # This sequence will engage the AI and start the unit.
    force_cmd = "{addcommand startup;addcommand autogun on;engage;@wait 1=sendchannel a=Engaged and starting up!}"
    mux_commands.force(p, ai_dbref, force_cmd)

    on_unit_ai_started.send(None, ai_dbref=ai_dbref, unit_dbref=unit_dbref)
    returnValue(ai_dbref)
