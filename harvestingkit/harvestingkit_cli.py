#!/usr/bin/env python
from argparse import ArgumentParser

from ConfigParser import ConfigParser

from harvestingkit.elsevier_package import ElsevierPackage
from harvestingkit.oup_package import OxfordPackage
from harvestingkit.springer_package import SpringerPackage

from harvestingkit.config import CFG_CONFIG_PATH


class Bunch:

    def __init__(self, kwds):
        self.__dict__.update(kwds)


def _convert_to_bool(keyboard_input):
    keyboard_input = keyboard_input.lower()
    if (keyboard_input != '' and keyboard_input != 'y'
            and keyboard_input != 'n'):
        raise ValueError
    return True if keyboard_input == '' or keyboard_input == 'y' else False


def _query_keyboard_input(checking_function, message):
    while True:
        try:
            return checking_function(raw_input(message))
        except ValueError:
            print 'Not a valid option, try again...'


def _get_credentials():
    return {'LOGIN': raw_input('Login: '),
            'PASSWORD': raw_input('Password: '),
            'URL': raw_input('URL: ')}


def _get_default_ConfigParser():
    config = ConfigParser()
    config.read(CFG_CONFIG_PATH)
    return config


def _setup_credentials(config, publisher):
    for key, value in _get_credentials().iteritems():
        config.set(publisher, key, value)


def _query_user_for_credentials(publishers):
    config = _get_default_ConfigParser()

    default = ('\033[92m'
               'Do you want to setup your credentials to harvest from {0}?\n'
               '[Y]:n?'
               '\033[0m')
    for publisher in publishers:
        if _query_keyboard_input(_convert_to_bool, default.format(publisher)):
            _setup_credentials(config, publisher)

    with open(CFG_CONFIG_PATH, 'w') as config_file:
        config.write(config_file)


def call_all(settings):
    if settings.update_credentials:
        _query_user_for_credentials(['ELSEVIER', 'OXFORD', 'SPRINGER'])


def call_elsevier(settings):
    if settings.update_credentials:
        _query_user_for_credentials(['ELSEVIER'])
        return

    elsevier_package = ElsevierPackage(package_name=settings.package_name,
                                       path=settings.path,
                                       run_locally=settings.run_locally,
                                       extract_nations=
                                       settings.extract_nations)
    elsevier_package.bibupload_it()


def call_oxford(settings):
    if settings.update_credentials:
        _query_user_for_credentials(['OXFORD'])
        return

    oxford_package = OxfordPackage(package_name=settings.package_name,
                                   path=settings.path,
                                   extract_nations=settings.extract_nations)
    oxford_package.bibupload_it()
    if not settings.dont_empty_ftp:
        oxford_package.empty_ftp()


def call_springer(settings):
    if settings.update_credentials:
        _query_user_for_credentials(['SPRINGER'])
        return

    springer_package = SpringerPackage(package_name=settings.package_name,
                                       path=settings.path,
                                       extract_nations=
                                       settings.extract_nations)
    springer_package.bibupload_it()


def call_package(settings):
    packages = {'all': call_all,
                'elsevier': call_elsevier,
                'oxford': call_oxford,
                'springer': call_springer}

    packages[settings.selected_subparser](settings)


def main():
    argparser = ArgumentParser()

    subparsers = argparser.add_subparsers(dest='selected_subparser')

    all_parser = subparsers.add_parser('all')
    elsevier_parser = subparsers.add_parser('elsevier')
    oxford_parser = subparsers.add_parser('oxford')
    springer_parser = subparsers.add_parser('springer')

    all_parser.add_argument('--update-credentials', action='store_true')

    elsevier_parser.add_argument('--run-locally', action='store_true')
    elsevier_parser.add_argument('--package-name')
    elsevier_parser.add_argument('--path')
    elsevier_parser.add_argument('--CONSYN', action='store_true')
    elsevier_parser.add_argument('--update-credentials', action='store_true')
    elsevier_parser.add_argument('--extract-nations', action='store_true')

    oxford_parser.add_argument('--dont-empty-ftp', action='store_true')
    oxford_parser.add_argument('--package-name')
    oxford_parser.add_argument('--path')
    oxford_parser.add_argument('--update-credentials', action='store_true')
    oxford_parser.add_argument('--extract-nations', action='store_true')

    springer_parser.add_argument('--package-name')
    springer_parser.add_argument('--path')
    springer_parser.add_argument('--update-credentials', action='store_true')
    springer_parser.add_argument('--extract-nations', action='store_true')

    '''
    Transforms the argparse arguments from Namespace to dict and then to Bunch
    Therefore it is not necessary to access the arguments using the dict syntax
    The settings can be called like regular vars on the settings object
    '''

    settings = Bunch(vars(argparser.parse_args()))

    call_package(settings)


if __name__ == '__main__':
    main()
