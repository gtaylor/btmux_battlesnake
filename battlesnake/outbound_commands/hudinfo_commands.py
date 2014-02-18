
def hudinfo_set_key(protocol, key_str):
    key_len = len(key_str)
    assert key_len <= 21 or key_len < 0, \
        "HUDINFO keys must be between 1 and 21 characters."
    assert ':' not in key_str, "Colons may not appear in HUDINFO keys."

    command_str = 'hudinfo key=%s' % key_str
    regex_str = r'^#HUD:(?P<hudinfo_key>.*):KEY:R# Key set\r$'
    deferred = protocol.expect(regex_str, return_regex_group='hudinfo_key')
    protocol.write(command_str)
    return deferred