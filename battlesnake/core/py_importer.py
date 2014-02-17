"""
Python import related convenience functions.
"""


def import_class(full_path):
    """
    We dynamically load a few classes based on configuration values. A few
    examples are Triggers and CommandTables. This function provides a
    cheesy/fast way to do that.

    :param str full_path: The full Python path to the class to import.
    :returns: The dynamically loaded class.
    """

    mod_path, class_name = full_path.rsplit('.', 1)
    mod = __import__(mod_path, fromlist=[class_name])
    return getattr(mod, class_name)
