"""
Define archetypes here. Right now these are just dicts containing the arch's
skills and physical attributes.
"""

# If your game doesn't have separate archetypes, this guy can do it all.
JACK_OF_ALL_TRADES = {
    'physical_attributes': {
        'build': 5,
        'reflexes': 5,
        'intuition': 6,
        'learn': 5,
        'charisma': 4,
    },
    'skills': {
        'medtech': 3,
        'perception': 3,
        'gunnery-spotting': 3,
        'computer': 3,
        'comm-conventional': 3,
        'gunnery-artillery': 3,
        'gunnery-laser': 3,
        'gunnery-missile': 3,
        'piloting-biped': 4,
        'piloting-quad': 3,
        'gunnery-flamer': 3,
        'piloting-tracked': 3,
        'piloting-spacecraft': 3,
        'piloting-bsuit': 3,
        'piloting-hover': 3,
        'piloting-naval': 3,
        'piloting-aerospace': 3,
        'piloting-wheeled': 3,
        'gunnery-ballistic': 3,
    }
}
