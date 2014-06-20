from ConfigParser import ConfigParser


class Bunch:
    def __init__(self, kwds):
        tmp = {}
        for key, value in kwds.iteritems():
            tmp[key] = Bunch(value) if isinstance(value, dict) else value

        self.__dict__.update(tmp)

    def get_attributes(self):
        return self.__dict__.keys()


def _read_section(config, section, working_dict):
    working_dict[section] = [item[0].upper() for item in config.items(section)]


def _get_sections_to_read_completely(config, working_dict):
    if working_dict == {}:
        return config.sections()
    return [key for key, value in working_dict.iteritems() if value == []]


def _prepare_working_dict(config, section_option_dict):
    working_dict = section_option_dict.copy()  # to not alter the input

    for section in _get_sections_to_read_completely(config, working_dict):
        _read_section(config, section, working_dict)

    return working_dict


def load_config(filename=None, section_option_dict={}):
    """
    This function returns a Bunch object from the stated config file.

    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    NOTE:
        The values are not evaluated by default.
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    filename:
        The desired config file to read.
        The config file must be written in a syntax readable to the
        ConfigParser module -> INI syntax

        [sectionA]
        optionA1 = ...
        optionA2 = ...

    section_option_dict:
        A dictionary that contains keys, which are associated to the sections
        in the config file, and values, which are a list of the desired
        options.
        If empty, everything will be loaded.
        If the lists are empty, everything from the sections will be loaded.

    Example:
        dict = {'sectionA': ['optionA1', 'optionA2', ...],
                'sectionB': ['optionB1', 'optionB2', ...]}

        config = get_config('config.cfg', dict)
        config.sectionA.optionA1

    Other:
        Bunch can be found in configparser.py
    """

    config = ConfigParser()
    config.read(filename)

    working_dict = _prepare_working_dict(config, section_option_dict)

    tmp_dict = {}

    for section, options in working_dict.iteritems():
        tmp_dict[section] = {}
        for option in options:
            tmp_dict[section][option] = config.get(section, option)

    return Bunch(tmp_dict)
