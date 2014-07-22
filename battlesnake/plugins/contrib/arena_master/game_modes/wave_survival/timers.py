from battlesnake.conf import settings
from battlesnake.core.timers import TimerTable, IntervalTimer

from battlesnake.plugins.contrib.arena_master.puppets.defines import \
    GAME_STATE_ACTIVE
from battlesnake.plugins.contrib.arena_master.puppets.puppet_store import \
    PUPPET_STORE


class ActiveArenaChecksTimer(IntervalTimer):
    """
    Periodically checks all arena master puppets with game mode 'wave' to
    see if the game state is Active, but all defenders/attackers have died.
    """

    interval = settings['arena_master']['match_end_check_interval']
    pause_when_bot_is_disconnected = True

    @classmethod
    def on_register(cls, protocol):
        print "* arena_master match end check interval: %ss" % cls.interval

    def run(self, protocol):
        wave_puppets = PUPPET_STORE.list_arena_master_puppets(game_mode='wave')
        for puppet in wave_puppets:
            if puppet.wave_check_cooldown_counter >= 0:
                # Wave check is on cooldown. Decrement and ignore.
                puppet.wave_check_cooldown_counter -= 1
                continue
            if puppet.game_state != GAME_STATE_ACTIVE:
                # They're not fighting, we're not interested.
                continue
            defenders_remaining = len(puppet.list_defending_units())
            if defenders_remaining == 0:
                # They're all dead, game over!
                puppet.change_state_to_finished(protocol)
            attackers_remaining = len(puppet.list_attacking_units())
            if attackers_remaining == 0:
                # Wave wiped!
                puppet.change_state_to_in_between(protocol)


class WaveSurvivalTimerTable(TimerTable):

    timers = [
        ActiveArenaChecksTimer,
    ]
