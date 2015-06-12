Cookbook
========

Settings as Module
------------------
    File : settings.py
    
    .. code-block:: python
    
        from settingslib.basesettings import BaseSettings
        
        # basic settings
        class Settings(BaseSettings):
            " Doc of the settingsobject."
            SOMESETTING = 'hello'
            INTSETTING = 1
            " This is an help message for INTSETTING"
        
            COMBINED_SETTING = '{INTSETTING} is an int, also {SOMESETTING}'

        # Add environ prefilx and add configfile from dir in package
        settings = Settings('my_app_', [os.path.join(os.path.dirname(__file__) , 'data', 'configfile.conf')])
        
        #hack make is so we can just import the settingsobject
        sys.modules[__name__] = settings
        
    Now you can import the settings module in you app without a problem.
    
    Example (file : some_file.py)
    
    .. code-block:: python
    
        form . import settings
        # or just import settings 
        # but from settings import INTSETTING won't work
        
        def some_func():
            return settings.INTSETTING 
        # if the settings are overridden during runtime the settings object will
        # reflect this.


Using configfile to override default Settings
---------------------------------------------

Some Text


Using environment value to override default Settings
----------------------------------------------------

Some Text


Using commandline options to override default Settings
------------------------------------------------------

Some Text

Complete setup
--------------

File : settings.py
    
    .. code-block:: python
    
        import os
        
        from settingslib.basesettings import BaseSettings
        
        # basic settings
        class Settings(BaseSettings):
            " Doc of the settingsobject."
            SOMESETTING = 'hello'
            " This is an help message for SOMESETTING"
            INTSETTING = 1
            " This is an help message for INTSETTING"
            DATA_DIR = os.path.join(os.path.dirname(__file__), 'data') # or a better place for the data dir
            USER_CONFIG_FILE = os.path.join('{DATA_DIR}', 'settings.conf')
        
            COMBINED_SETTING = '{INTSETTING} is an int, also {SOMESETTING}'

        # Add environ prefilx and add configfile from dir in package
        settings = Settings('my_app_', [os.path.join(os.path.dirname(__file__) , 'data', 'configfile.conf')])
        if len(settings.CONFIG_FILES) > 0:
                for file in settings.CONFIG_FILES:
                    settings.add_cfgfile(file)
        
        #hack make is so we can just import the settingsobject
        sys.modules[__name__] = settings
    
    In the above code we define our settings, allow enviroment values
    ,prefixed with ``"my_app_"``, to override settings and allow a the enviroment
    value with key of ``"my_app_config_files"`` to specify a jsonlist of 
    configfiles to used to override the default values.
    
    The next file is the main file to start the app.
    It uses commandline options to config more options
    on the settingsobject. After the 
    
    File : __main__.py
    
    .. code-block:: python
        
        form . import settings
        
        # Take args so other app can import __main__ and call ``main`` with custom args.
        def main(args = None):
            
            parser = argparse.ArgumentParser(
                        usage='%(prog)s [options]',
                        description='Launch app'
                    )
            parser.add_argument('--somesetting', 
                        #default = 'start', don't set defaults, the settingsobject takes care this for you
                        dest='somesetting',
                        help = setttings.help('somesetting'))
            parser.add_argument('--data_dir', # Allow to override the data_dir and thus the user_config_file
                        dest='data_dir',
                        help = setttings.help('somesetting'))
            parser.add_argument('--cfgfiles', 
                        dest='cfgfiles',
                        nargs='+',
                        help = 'Configfiles to add to overrride default settings.')
            
            options = parser.parse_args(args)
            
            settings.set_options(options)
            if options.cfgfiles:
                for file in options.cfgfiles:
                    settings.add_cfgfile(file)
            
            settings.set_userfile(settings.USER_CONFIG_FILE)
            
            # all setting are loaded
    
    The settings are set up, there are in total 6 placed where the default can be override
    - A config file in de package_dir/data/configfile.conf  (maybe created at install)
    - Environ values prefixed with ``"my_app"``
    - Environ key ``"my_app_config_files"`` to specify more config files in jsonlist
    - Commandline options
    - Config files passed to the cfgfiles arg in de commandline
    - Userconfig files, values save from the last time it app run
            