from battlesnake.conf import settings


__raw_channel_pairs = settings['imc2']['channel_map_pairs']
__channel_map_pairs = [pair.split(' ', 1) for pair in __raw_channel_pairs]

IMC2_TO_MUX_CHANNEL_MAP = \
    {ichan: muxchan for ichan, muxchan in __channel_map_pairs}
MUX_TO_IMC2_CHANNEL_MAP = \
    {muxchan: ichan for ichan, muxchan in __channel_map_pairs}
