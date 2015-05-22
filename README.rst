A settings Python project
=======================

A lib to easly define settings for your app.

support for:
 - default settings (python class format)
 - config file (can be edit by the user)
 - user file (to save edited settings to)
 - auto type discovery (can be overriden)
 - support for string formatting (the python format way {hello})
 - resolver for type to string convertion
 - support for settingshelp in app and in the file by comments
 - help messages are save to comments 
 - help messages are loaded from files
 
usage

-- settings.py --

import sys

from settingslib import BaseSettings, Section, Option, Resolver

class Settings(BaseSettings):
    
    # alle settings must be upper case
    # some different types
    INT_SETTINGS = 1
    SOME_SETTINGS = "hello"
    OTHER_SETTINGS = "world"
    FORMAT_SETTINGS = "{OTHER_SETTINGS} {OTHER_SETTINGS}"
    ROOT_DIR = "vars/user"
    SETTINGS_DIR = "{ROOT_DIR}/settings" # results to "vars/user/settings"
    SETTINGS_FILE = "{SETTINGS_DIR}/userconfig.conf"
    LOG_DIR = "{ROOT_DIR}/log"
    PORT = 1257
    BOOL_SET = True
    FLOAT_SET = 1.152
    LIST_OF_INTS = [2] # all values that are append are automatic int type
    TUPLE_COMBINATION = ('dds', 121 , '11') # tuple is always (str, int, str)
    
    # override user resolver, using a tuple
    
    # settings = Option( default, resolver, **extraOptions)
    # default : the default value for this setting
    # resolver : a tuple (type , kwargs) to construct the resolver
        # type : a classtype (like int or str) or a string repressing a class like "str" or "int" used to find the resolver 
        # kwargs : kwargs for the resolver (dict duhh :P)
    # extraOptions : a dict with extra options, like help message or if we should save the value
    
    RESOLVER_SETTING = Option("some default class like", Resolver("str", choices = ['str','int', 'bool']), save=False, help="a string represention a python class")
    
    # you can also use a class like notation to create settings, this is the same as RESOLVER_SETTINGS
    class SOMESETTING(Option):  #subclassing Option
        " Doc string is used for help message. "
        default = 'str'
        class resolver(Resolver):
            type='str'
            choices = ['str','int', 'bool']
        
        # other attrs are asumed to be extraOptions
        save = False
    
    #create sections
    class SECTION(Section): #subclassing Section
        SECTION_SETTING = 8080
        
        # you can go as deep as you like
        class SECONDSETTINGS(Section):
            SETTINGS = 'hello'

settings = Settings('my_app_', [os.path.join(os.path.dirname(__file__), 'data', 'config.conf')]) # add prefix and "in package settings"
# now we can just import is like a module
sys.modules[__name__] = settings

-- __main__.py --

import argparse

from . import settings

def main():
    
    #create options
    parser = argparse.ArgumentParser(
                        usage='%(prog)s [options]',
                        description='Launch app'
                    )
    
    parser.add_argument('-p', '--port', 
                        type=int,
                        dest = 'port')
    
    args = parser.parse_args(args)
    
    settings.set_options(args)
    settings.set_userfile(settings.SETTINGS_FILE)
    
    for file in ['dev.conf', 'dev0.conf', 'somefile.conf']:
        settings.add_cfgfile(os.path.join(settings.SETTINGS_DIR, file))
    
    # settings are setup up
    
    # set up logging or something
    logger.setup() # logger.py can just import settings and use settings.LOG_DIR or something





