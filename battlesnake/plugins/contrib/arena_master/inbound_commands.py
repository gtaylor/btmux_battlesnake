from twisted.internet.defer import inlineCallbacks

from battlesnake.core.inbound_command_handling.base import BaseCommand, \
    CommandError
from battlesnake.core.inbound_command_handling.btargparse import \
    BTMuxArgumentParser
from battlesnake.core.inbound_command_handling.command_table import \
    InboundCommandTable
from battlesnake.outbound_commands import mux_commands
from battlesnake.outbound_commands import think_fn_wrappers
from battlesnake.plugins.contrib.arena_master.arena_crud.creation import \
    create_arena
from battlesnake.plugins.contrib.arena_master.arena_crud.destruction import \
    destroy_arena
from battlesnake.plugins.contrib.arena_master.powerups.fixers import \
    spawn_fixer_unit, uniformly_repair_armor, fix_all_internals, reload_all_ammo
from battlesnake.plugins.contrib.arena_master.puppets.kill_tracking import \
    handle_kill
from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    PUPPET_STORE
from battlesnake.plugins.contrib.arena_master.game_modes.wave_survival.wave_spawning import \
    pick_refs_for_wave, spawn_wave
from battlesnake.plugins.contrib.arena_master.staging_room.idesc import \
    pemit_staging_room_idesc


class PickWaveCommand(BaseCommand):
    """
    Picks a wave full of units based on the provided conditions.
    """

    command_name = "am_pickwave"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="pickwave", description='Chooses a wave of units.')

        parser.add_argument(
            'wave_num', type=int,
            help="The wave number.")
        parser.add_argument(
            'opposing_bv2', type=int,
            help="Total BV2 of opposing force.")
        parser.add_argument(
            'difficulty_mod', type=float,
            help="1.0 being the base level difficulty")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        output = str(args)
        mux_commands.pemit(protocol, invoker_dbref, output)
        refs = yield pick_refs_for_wave(
            args.wave_num, args.opposing_bv2, args.difficulty_mod)
        mux_commands.pemit(protocol, invoker_dbref, str(refs))


class SpawnWaveCommand(BaseCommand):
    """
    Picks and spawns a wave full of units based on the provided conditions.
    """

    command_name = "am_spawnwave"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="spawnwave", description='Spawns a wave of units.')

        parser.add_argument(
            'wave_num', type=int,
            help="The wave number.")
        parser.add_argument(
            'opposing_bv2', type=int,
            help="Total BV2 of opposing force.")
        parser.add_argument(
            'difficulty_mod', type=float,
            help="1.0 being the base level difficulty.")
        parser.add_argument(
            'arena_master_dbref', type=str,
            help="Arena master dbref to spawn through.")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        output = str(args)
        mux_commands.pemit(protocol, invoker_dbref, output)

        arena_master_dbref = args.arena_master_dbref
        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError("Invalid arena dbref.")

        yield spawn_wave(
            protocol, args.wave_num, args.opposing_bv2, args.difficulty_mod,
            puppet)
        mux_commands.pemit(protocol, invoker_dbref,
            "Spawning wave.")


class FixUnitCommand(BaseCommand):
    """
    Fixes a unit.
    """

    command_name = "am_fixunit"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()
        fixmodes = ['armor', 'ints', 'ammo']

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="fixunit", description='Fixes a unit.')

        parser.add_argument(
            'mech_dbref', type=str,
            help="The dbref of the mech to fix.")
        parser.add_argument(
            'fix_percent', type=float,
            help="Percentage of damage to fix (0...1)")
        parser.add_argument(
            "--fixmode", type=str, choices=fixmodes, dest='fix_mode',
            default='armor',
            help="Determines what to fix on the unit. Defaults to armor.")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        output = str(args)
        p = protocol
        mux_commands.pemit(protocol, invoker_dbref, output)

        if args.fix_mode == 'armor':
            yield uniformly_repair_armor(p, args.mech_dbref, args.fix_percent)
        elif args.fix_mode == 'ints':
            yield fix_all_internals(p, args.mech_dbref)
        elif args.fix_mode == 'ammo':
            yield reload_all_ammo(p, args.mech_dbref)


class SpawnFixerCommand(BaseCommand):
    """
    Spawns a fixer unit.
    """

    command_name = "am_spawnfixer"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()
        fixmodes = ['armor', 'ints', 'ammo']

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="spawnfixer", description='Spawns a fixer unit.')

        parser.add_argument(
            'map_dbref', type=str,
            help="The dbref of the map to spawn the fixer on.")
        parser.add_argument(
            'fix_percent', type=float,
            help="Percentage of damage to fix (0...1)")
        parser.add_argument(
            "--fixertype", type=str, choices=fixmodes, dest='fixer_type',
            default='armor',
            help="Determines what to fix on the unit. Defaults to armor.")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    @inlineCallbacks
    def handle(self, protocol, invoker_dbref, args):
        output = str(args)
        p = protocol
        mux_commands.pemit(p, invoker_dbref, output)

        yield spawn_fixer_unit(
            p, args.map_dbref, args.fixer_type, args.fix_percent)


class CreateArenaCommand(BaseCommand):
    """
    Basic arena creation.
    """

    command_name = "am_createarena"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        invoker_name = parsed_line.kwargs['invoker_name']
        self._check_for_dupe_arenas(invoker_dbref)
        arena_name = "%s's arena" % invoker_name
        mux_commands.pemit(p, invoker_dbref, "Creating an arena...")
        arena_master_dbref, staging_dbref = yield create_arena(
            p, arena_name, invoker_dbref)
        mux_commands.pemit(p, invoker_dbref, "Arena ready: %s" % arena_master_dbref)

        think_fn_wrappers.tel(p, invoker_dbref, staging_dbref)

        message = (
            "[name({leader_dbref})] has created a new arena"
            " %(ID: %ch{arena_id}%cn%)."
        ).format(
            leader_dbref=invoker_dbref,
            arena_id=arena_master_dbref[1:]
        )
        think_fn_wrappers.cemit(p, 'Public', message)

    def _check_for_dupe_arenas(self, invoker_dbref):
        puppets = PUPPET_STORE.list_arena_master_puppets()
        for puppet in puppets:
            if puppet.leader_dbref == invoker_dbref:
                raise CommandError("You already have an active arena.")


class DestroyArenaCommand(BaseCommand):
    """
    Completely wipes out an arena.
    """

    command_name = "am_destroyarena"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']
        try:
            PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError("Invalid arena dbref.")

        mux_commands.pemit(p, invoker_dbref, "Destroying arena: %s" % arena_master_dbref)
        yield destroy_arena(p, arena_master_dbref)
        mux_commands.pemit(p, invoker_dbref, "Arena destroyed!")


class ArenaListCommand(BaseCommand):
    """
    Lists all active arenas.
    """

    command_name = "am_arenalist"

    #@inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol

        puppets = PUPPET_STORE.list_arena_master_puppets()

        retval = self._get_header_str('Active Arena Listing')
        retval += self._get_footer_str('-')
        retval += (
            '%r%ch [rjust(ID,4)]%b [ljust(Arena Name, 40)] '
            '[ljust(Players,10)] '
            'State%cn'
        )
        retval += self._get_footer_str('-')
        for puppet in puppets:
            retval += (
                "%r [rjust({dbref}, 4)]%b [ljust({name},43)] "
                "[ljust(words(zwho(#{dbref})),7)] "
                "{state} (Public)".format(
                dbref=puppet.dbref[1:], name=puppet.arena_name,
                state=puppet.game_state))
        if not puppets:
            retval += "[center(There are no active arenas. Create one!,78)]"
        retval += self._get_footer_str()
        retval += '%r[center(To get more details on an arena%, type %ch%cgarena <id>%cn,78)]'
        retval += self._get_footer_str()

        mux_commands.pemit(p, invoker_dbref, retval)


class ArenaDetailsCommand(BaseCommand):
    """
    Command to show the details of an arena.
    """

    command_name = "am_arenadetails"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        cmd_line = parsed_line.kwargs['cmd'].split()

        parser = BTMuxArgumentParser(protocol, invoker_dbref,
            prog="arena", description='Shows info on an arena.')

        parser.add_argument(
            'arena_id', type=int, nargs='?', default=None,
            help="The ID of the arena to see the details for..")

        args = parser.parse_args(args=cmd_line)
        try:
            yield self.handle(protocol, invoker_dbref, parsed_line, args)
        except AssertionError as exc:
            raise CommandError(exc.message)

    #@inlineCallbacks
    def handle(self, protocol, invoker_dbref, parsed_line, args):
        p = protocol
        invoker_zone = parsed_line.kwargs['invoker_zone']

        if args.arena_id:
            zone_dbref = '#%s' % args.arena_id
        else:
            zone_dbref = invoker_zone

        is_in_arena = invoker_zone == zone_dbref

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(zone_dbref)
        except KeyError:
            raise CommandError(
                "Invalid arena ID. See the %ch%cgarenas%cn command for a full list.")

        self.render_arena_detail(p, invoker_dbref, puppet, is_in_arena)

    def render_arena_detail(self, protocol, invoker_dbref, puppet, is_in_arena):
        render_lower_tip = is_in_arena
        pemit_staging_room_idesc(
            protocol, puppet, invoker_dbref, render_contents=False,
            render_header=True, render_lower_tip=render_lower_tip)


class ArenaJoinCommand(BaseCommand):
    """
    Joins an arena.
    """

    command_name = "am_arenajoin"

    #@inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol

        arena_master_dbref = parsed_line.kwargs['arena_dbref']
        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError(
                "Invalid arena ID. See the %ch%cgarenas%cn command for a full list.")

        think_fn_wrappers.tel(p, invoker_dbref, puppet.staging_dbref)


class ContinueMatchCommand(BaseCommand):
    """
    Moves the match from in-between to the next wave.
    """

    command_name = "am_continuematch"

    @inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)

        leader_dbref = puppet.leader_dbref
        if leader_dbref != invoker_dbref:
            raise CommandError("Only the arena leader can do that.")

        if puppet.game_state.lower() != 'in-between':
            raise CommandError("You may only %ch%cgcontinue%cn when between waves.")

        yield puppet.change_state_to_active(p)


class ReportDestructionCommand(BaseCommand):
    """
    Called when a unit is destroyed.
    """

    command_name = "am_reportdestruction"

    #@inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)

        victim_unit_dbref = parsed_line.kwargs['victim_unit_dbref']
        killer_unit_dbref = parsed_line.kwargs['killer_unit_dbref']
        cause_of_death = parsed_line.kwargs['cause_of_death']
        handle_kill(p, puppet, victim_unit_dbref, killer_unit_dbref, cause_of_death)


class TScanCommand(BaseCommand):
    """
    Team scan, shows other units.
    """

    command_name = "am_tscan"

    #@inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']
        invoker_unit_dbref = parsed_line.kwargs['invoker_unit_dbref']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)
        map_dbref = puppet.map_dbref
        try:
            invoker_unit = puppet.unit_store.get_unit_by_dbref(invoker_unit_dbref)
        except ValueError:
            raise CommandError('Unable to find your unit in the unit store.')

        retval = self._get_header_str("Team Scan")
        retval += "%r"
        retval += (
            " %[ID%] [ljust(Unit Type,15)] [ljust(Pilot Name,20)] [ljust(X%,Y,7)] "
            "[ljust(Speed,7)][ljust(Head,6)][ljust(Rng,7)]Cond"
        )

        teammates = puppet.list_defending_units()
        teammates.sort(
            key=lambda t_unit: t_unit.distance_to_unit(invoker_unit), reverse=True)
        retval += self._get_footer_str("-")
        for unit in teammates:
            unit_has_target = unit.target_dbref != '#-1'
            target_marker = '%ch%cr*%cn' if unit_has_target else '%b'
            armor_condition = int(unit.calc_armor_condition() * 100)
            retval += "%r"
            retval += (
                "{target_marker}%[{contact_id}%] [ljust({mech_name},15)] "
                "[ljust(name({pilot_dbref}),18)] "
                "[rjust({unit_x},3)],[ljust({unit_y},5)] "
                "[ljust({speed},6)] "
                "[ljust({heading},5)] "
                "[ljust(round(btgetrange({map_dbref},{invoker_unit_dbref},{unit_dbref}),1),6)] "
                "{armor_condition}%%".format(
                    target_marker=target_marker,
                    contact_id=unit.contact_id, mech_name=unit.mech_name[:14],
                    unit_x=unit.x_coord, unit_y=unit.y_coord,
                    pilot_dbref=unit.pilot_dbref, speed=unit.speed,
                    heading=unit.heading, invoker_unit_dbref=invoker_unit_dbref,
                    unit_dbref=unit.dbref, map_dbref=map_dbref,
                    armor_condition=armor_condition,
                )
            )
        retval += self._get_footer_str()

        mux_commands.pemit(p, invoker_dbref, retval)


class EScanCommand(BaseCommand):
    """
    Enemy scan, shows other units.
    """

    command_name = "am_escan"

    #@inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']
        invoker_unit_dbref = parsed_line.kwargs['invoker_unit_dbref']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)
        map_dbref = puppet.map_dbref
        try:
            invoker_unit = puppet.unit_store.get_unit_by_dbref(invoker_unit_dbref)
        except ValueError:
            raise CommandError('Unable to find your unit in the unit store.')

        retval = self._get_header_str("Enemy Scan", width=57)
        retval += "%r"
        retval += (
            " %[ID%] [ljust(Unit Type,15)] [ljust(X%,Y,7)] "
            "[ljust(Speed,7)][ljust(Head,6)][ljust(Rng,7)]Cond"
        )

        teammates = puppet.list_attacking_units()
        teammates.sort(
            key=lambda t_unit: t_unit.distance_to_unit(invoker_unit), reverse=True)
        retval += self._get_footer_str("-", width=57)
        for unit in teammates:
            armor_condition = int(unit.calc_armor_condition() * 100)
            retval += "%r"
            retval += (
                " %[{contact_id}%] [ljust({mech_name},13)] "
                "[rjust({unit_x},3)],[ljust({unit_y},5)] "
                "[ljust({speed},6)] "
                "[ljust({heading},5)] "
                "[ljust(round(btgetrange({map_dbref},{invoker_unit_dbref},{unit_dbref}),1),6)] "
                "{armor_condition}%%".format(
                    contact_id=unit.contact_id, mech_name=unit.mech_name[:14],
                    unit_x=unit.x_coord, unit_y=unit.y_coord,
                    pilot_dbref=unit.pilot_dbref, speed=unit.speed,
                    heading=unit.heading, invoker_unit_dbref=invoker_unit_dbref,
                    unit_dbref=unit.dbref, map_dbref=map_dbref,
                    armor_condition=armor_condition,
                )
            )
        retval += self._get_footer_str(width=57)

        mux_commands.pemit(p, invoker_dbref, retval)


class PScanCommand(BaseCommand):
    """
    Scans for powerups.
    """

    command_name = "am_pscan"

    #@inlineCallbacks
    def run(self, protocol, parsed_line, invoker_dbref):
        p = protocol
        arena_master_dbref = parsed_line.kwargs['arena_master_dbref']
        invoker_unit_dbref = parsed_line.kwargs['invoker_unit_dbref']

        try:
            puppet = PUPPET_STORE.get_puppet_by_dbref(arena_master_dbref)
        except KeyError:
            raise CommandError('Invalid puppet dbref: %s' % arena_master_dbref)
        map_dbref = puppet.map_dbref
        try:
            invoker_unit = puppet.unit_store.get_unit_by_dbref(invoker_unit_dbref)
        except ValueError:
            raise CommandError('Unable to find your unit in the unit store.')

        retval = self._get_header_str("Powerup Scan", width=57)
        retval += "%r"
        retval += (
            " %[ID%] [ljust(Powerup Type,15)] [ljust(X%,Y,7)] "
            "[ljust(Speed,7)][ljust(Head,6)][ljust(Rng,7)]"
        )

        teammates = puppet.unit_store.list_powerup_units()
        teammates.sort(
            key=lambda t_unit: t_unit.distance_to_unit(invoker_unit), reverse=True)
        retval += self._get_footer_str("-", width=57)
        for unit in teammates:
            retval += "%r"
            retval += (
                " %[{contact_id}%] [ljust({mech_name},13)] "
                "[rjust({unit_x},3)],[ljust({unit_y},5)] "
                "[ljust({speed},6)] "
                "[ljust({heading},5)] "
                "[round(btgetrange({map_dbref},{invoker_unit_dbref},{unit_dbref}),1)]".format(
                    contact_id=unit.contact_id, mech_name=unit.mech_name[:14],
                    unit_x=unit.x_coord, unit_y=unit.y_coord,
                    pilot_dbref=unit.pilot_dbref, speed=unit.speed,
                    heading=unit.heading, invoker_unit_dbref=invoker_unit_dbref,
                    unit_dbref=unit.dbref, map_dbref=map_dbref,
                )
            )
        retval += self._get_footer_str(width=57)

        mux_commands.pemit(p, invoker_dbref, retval)


class ArenaMasterCommandTable(InboundCommandTable):

    commands = [
        ArenaListCommand,
        ArenaJoinCommand,
        ArenaDetailsCommand,

        ContinueMatchCommand,

        PickWaveCommand,
        SpawnWaveCommand,
        FixUnitCommand,
        SpawnFixerCommand,

        CreateArenaCommand,
        DestroyArenaCommand,

        TScanCommand,
        EScanCommand,
        PScanCommand,

        ReportDestructionCommand,
    ]
