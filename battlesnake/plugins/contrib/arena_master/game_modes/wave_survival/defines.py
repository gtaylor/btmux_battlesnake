"""
Constants and defines for the wave survival arena type.
"""

WAVE_DIFFICULTY_LEVELS = {
    'easy': {
        'modifier': 0.5,
        'wave_step': 0.1,
        'salvage_loss': 95,
        'base_bp_draw_chance': 18,
    },
    'normal': {
        'modifier': 0.8,
        'wave_step': 0.25,
        'salvage_loss': 93,
        'base_bp_draw_chance': 20,
    },
    'hard': {
        'modifier': 1.15,
        'wave_step': 0.30,
        'salvage_loss': 91,
        'base_bp_draw_chance': 22,
    },
    'overkill': {
        'modifier': 1.3,
        'wave_step': 0.40,
        'salvage_loss': 89,
        'base_bp_draw_chance': 24,
    },
}

# This defines the rock bottom BV2 level for a wave, regardless of difficulty
# level modifiers or what the player(s) are in. We do this to ensure enough
# variety at the easy difficulty and lower waves.
MIN_WAVE_BV2 = 600
