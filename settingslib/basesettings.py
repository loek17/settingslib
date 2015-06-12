#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright (c) 2014 Loek Wensveen
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

from __future__ import absolute_import

import logging
import os

from . import configfile

logger = logging.getLogger(__name__)

__all__ = ['Option', 'Resolver', 'BaseSettings', 'Section',
            'SettingsException', 'add_resolver_type']

class SettingsException(Exception):
    pass
            
def add_resolver_type(cls):
    Section._resolverTypes.append(cls)
    
class Section(object):
    """ Section class used to create Sections in a Settings object.
    
    Works the same a the BaseSettings class but can be used
    to create subsection in the settingsobject. This is done
    by sub-classing this class in a settingsobject. Attributes
    set on a Section work the same as for BaseSettings.
    
    The name of the class subclassing Section must be upper-case
    else it is not pick up by the BaseSettings.
    
    Sections can be created in Sections, same rules apply.
    
    Example:
    
    .. code-block:: python
    
        class Settings(BaseSettings):
            NORMAL_ATTR = "some str"
            " NORMAL_ATTR is a normal setting in the settingsobject"
        
            class SECTION(Section):
                " This is the help message of this section "
            
                SECTION_ATTR = "some other str"
                " SECTION_ATTR is a attr of the section, it can be acces by settings.SECTION.SECTION_ATTR"
    
    Sections are automatic created by the SectionSettingsResolver. Sections are
    recreated each time they are accessed. 

    :param root: The root BaseSettings instance (settingsobject). they are passed to the resolvers
    :param options: A dict representing options passed by the commandline. if a '.' is in the key
            it is assumed that this is for a section (somesection.some_attr  --> settings.SOMESECTION.SOME_ATTR
    :param userconfig: A `Configfile` object used to save the runtime set settings
    :param nosave: A dict containing all the values, for this section, set at runtime but should not be saved.
    :param envconfig: A dict containing all values, for this section, set by environment values
    :param configs: A list of dict. Each dict represents a file config. they can be used to override the default
            Example uses is dev vs prod env, platfrom based config, enz. you can pass as may file config dict 
            as you want.
    :type root: `BaseSettings`
    :type options: `dict`
    :type userconfig: `ConfigFile`
    :type nosave: `dict`
    :type envconfig: `dict`
    :type configs: `list` containing `dict`
    """
    class __metaclass__(type):
        """ This metaclass handles the creating of the settings class
        it removes all uppercase attrs for the class and add them to
        the default dict. 
        
        it also creates a raw_resolver dict. this contains or the 
        string type, a `Resolver` object or None. this is used to create
        the resolver for this settings attr. If None is set the value in
        the default_dict is used to create the resolver.
        
        it also create a raw_extraOptions dict, the values in this
        dict override the default extraOption dict for each attr.
        This allows things like nosave attrs or solid values (default 
        always returned).
        
        It also creates the help_dict. this dict contains all help 
        messages for the attrs. Attr string literals are supported.
        the help message are also added to the userconfigfile. this
        makes it more clear if the user trys to read the file.
        """
        def __new__(cls, name, bases, attrs):
            if name in ['Section', 'BaseSettings']:
                return type.__new__(cls, name, bases, attrs)

            defaults = {}
            resolvers = {}
            extraOptions = {}
            
            try:
                help_dict = dict((k.lower(), v) for k,v in get_attr_doc_form_class(name, attrs['__module__']))
            except:
                help_dict = {}
            
            for key, value in attrs.items():
                if key.isupper():
                    if isinstance(value, Option):
                        defaults[key.lower()] = value.default
                        resolvers[key.lower()] = value.resolver
                        extraOptions[key.lower()] = value.extraOptions
                        if value.__doc__:
                            help_dict[key.lower()] = value.__doc__
                    else:
                        defaults[key.lower()] = value
                        resolvers[key.lower()] = None
                        extraOptions[key.lower()] = {}
                    del attrs[key]
            
            attrs['defaults'] = defaults
            attrs['raw_resolvers'] = resolvers
            attrs['help_dict'] = help_dict
            attrs['raw_extraOptions'] = extraOptions
            
            return type.__new__(cls, name, bases,attrs)

    _defaultExtraOptions = {
        "save" : True,
        #"commandoption" : False,           # Maybe add support for this later
        #"commandkwargs" : False,           # Maybe add support for this later
        "callback" : lambda k,v : None,    # callback called after a settings is set with setting as arg
        "initialize" : lambda k,v : None,  # called with the default, returning something does not update the value, is this usefull??
        "solid" : False                    # If True this value can't be changed, the default is always returned
    }
    
    _resolverTypes = []
    use_env = True

    def __init__(self, root, options, userconfig, nosave, envconfig ,configs):
        
        self.root = root
        
        self.options = {}
        for key, value in options.items():
            if '.' in key:
                dkey, key = key.split('.', 1)
                if dkey not in self.options:
                    self.options[dkey.lower()] = {}
                self.options[dkey.lower()][key] = value
            else:
                self.options[key.lower()] = value
                
        
        self.userconfig = userconfig
        userconfig.set_help(None, self.__doc__)
        
        self.nosave = nosave
        
        self.envconfig = {}
        for key, value in envconfig.items():
            if '.' in key:
                dkey, key = key.split('.', 1)
                if dkey not in self.envconfig:
                    self.envconfig[dkey] = {}
                self.envconfig[dkey][key] = value
            else:
                self.envconfig[key] = value
        
        self.fileconfigs = configs

        self.extraOptions = {}
        for key in self.raw_extraOptions.keys():
            self.extraOptions[key.lower()] = dict(self._defaultExtraOptions)
            self.extraOptions[key.lower()].update(self.raw_extraOptions[key.lower()])
        
        self.resolvers = {}
        for key, resolver in self.raw_resolvers.items():
            if resolver is not None:
                r = self._get_resolver(resolver.type,key=None, default=None, kwargs=resolver.resolverKwargs)
            else:
                r = self._get_resolver(self.defaults[key.lower()].__class__, key=key.lower(), default=self.defaults[key.lower()])
            self.resolvers[key.lower()] = r
            
            if r.multivalue and not r.has_childs():
                r.set_childs(self.defaults[key.lower()])
            
        for key, default in self.defaults.items():
            self.extraOptions[key.lower()]['initialize'](key, default)
        
        
    
    def __getattr__(self, key):
        """ Returns the value of a settings attr.
        Key must be upper.
        
        We look for the attr thougt the following way
        Command line Options  -  Userconfig - No Save values - environment values - file configs - default
        
        If the value is found it is passed to the get 
        function resolver of this attr. The get function
        will coerce the found value to the finaly value
        for the application. If a settings has solid set 
        to True in the extraOptions the default is 
        returned.
        
        Getattr is only called if the key is not found in __dict__
        """
        if not key.isupper():
            raise AttributeError("Key is not upper and not in __dict__, key : {key}".format(key=key))
        key = key.lower()

        if self.extraOptions[key]['solid'] is True:
            return self.defaults[key]

        for setting in [self.options, self.userconfig, self.nosave, self.envconfig] + self.fileconfigs + [self.defaults]:
            if key in setting.keys():
                return self.resolvers[key].get(setting[key])
        raise AttributeError("Key does not exists in Settings object, key : {key}".format(key=key))
    
    def __setattr__(self, key, value):
        """ Sets attr for a settings.
        Key must be upper.
        
        Before the value is save it is validated using the validate
        kwargs passed to a resolver or using the default. the default
        uses the options passed to a resolver. If the validate function 
        return False an SettingsException is raised.
        
        When the value is save it is first passed to the raw function
        of the resolver of this attr. The resolver returns a string 
        reprsention of the value. This string is saved.
        
        By default the settings is save in the userconfig file. If
        `nosave` is set to True in the extra settings dict the value
        is saved in the nosave dict. This dict is not saved when
        userconfig is saved thus making is not presisten between
        restarts.
        """
        if not key.isupper():
            return object.__setattr__(self, key, value)
        if self.resolvers[key.lower()].validate(value):
            if self.extraOptions[key.lower()]['save'] is not False:
                self.userconfig[key.lower()] = self.resolvers[key.lower()].raw(value)
                self.userconfig.set_help(key.lower(), self.help(key.lower()))
            else:
                self.nosave[key.lower()] = value
        else:
            raise SettingsException("This value is not valid for this key, key : {key}, value : {value}, {resolver}".format(key=key,value=value,resolver=self))
        # call the callback after the setting is set.
        self.extraOptions[key.lower()]['callback'](key, value)
    
    def __delattr__(self, key):
        """ Del a runtime set value from the settingsobject.
        Key must be uppercase.
        
        delattr will only delete value set at runtime. This means
        that value set by commandline options, Enviroment values 
        or configfiles are not deleted. You can use the `del()`
        function for that using the extra kwargs.
        
        Default values can never be deleted.
        """
        if not key.isupper():
            return object.__delattr__(self, key, value)
        key = key.lower()
        
        for setting in [self.userconfig, self.nosave]:
            if key in setting.keys():
                del setting[key]
    
    def get(self, key):
        """ Same as __getattr__ but key doesn't have to be uppercase.
        
        Also you can acces subsections using dots in the string. 
        ``get('section.hello')`` is the same as ``settings.SECTION.HELLO``
        
        :param key: The key to get, dots allowed.
        :type key: `str`
        :return: Returns value of the key, resolved by resolver.
        :rtype: Same as type of default
        """
        settings = self
        for k in key.split('.')[:-1]:
            settings = settings.__getattr__(k.upper())
        return settings.__getattr__(key.split('.')[-1].upper())
    
    def set(self, key, value):
        """ Same as __setattr__ but key doesn't have to be uppercase.
        
        Also you can acces subsections using dots in the string. 
        ``set('section.hello', 'str')`` is the same as 
        ``settings.SECTION.HELLO = 'str'``
        
        :param key: The key to set, dots allowed.
        :type key: ``str``
        """
        settings = self
        for k in key.split('.')[:-1]:
            settings = settings.__getattr__(k)
        settings.__setattr__(key.split('.')[-1].upper(), value)
    
    def has(self, key):
        """ Check if a settingsobject has a key.
        
        Also you can acces subsections using dots in the string. 
        ``has('section.hello', 'str')`` is the same as:
        
        .. code-block:: python
        
            try:
                settings.SECTION.HELLO
            except AttributeError:
                print "not found"
        
        :param key: The key to check, dots allowed.
        :type key: `str`
        :return: Returns True if key in settingsobject else False
        :rtype: `bool`
        """
        try:
            settings = self
            for k in key.split('.')[:-1]:
                settings = settings.defaults[k]
            key = key.split('.')[-1]
            
            return key in settings.defaults
        except AttributeError:
            return False
    
    def delele(self, key, options=False, env=False, fileconfig=False, runtime=True):
        """ Same as ``__delattr__`` but key doesn't have to be uppercase.
        
        Also you can acces subsections using dots in the string. 
        ``delete('section.hello')`` is the same as 
        ``del settings.SECTION.HELLO``
        
        You can pass extra kwargs specify form with configdict
        the key must be deleted. the following kwargs are valid.
        
        :param key: The key to delete, dots allowed.
        :param options: If set to True key will be delete from commandline options
        :param env: If set to True key will be deleted from enviroment set config
        :param fileconfig: If set to True key will be deleted from all file configs
        :param runtime: If set to False this will not delete form userconfig and nosave
        :type key: `str`
        :type options: `bool`
        :type env: `bool`
        :type fileconfig: `bool`
        :type runtime: `bool`
        """
        settings = self
        for k in key.split('.')[:-1]:
            settings = settings.get(k)
        
        settingslist = []
        if runtime:
            settingslist.extend([self.userconfig, self.nosave])
        if options:
            settingslist.append(self.options)
        if env:
            settingslist.append(self.envconfig)
        if fileconfig:
            settingslist.extend(self.fileconfigs)
        
        for setting in [self.userconfig, self.nosave]:
            if key in setting.keys():
                del setting[key]

    def keys(self):
        """ Returns all key of settingsobject.
        
        Same as ``dict.keys()``
        
        Does return sections, does not returns keys of sections.
        
        :return: list of keys of settingsobject
        :rtype: `list`
        """
        return [key.upper() for key in self.defaults.keys()]
    
    def values(self):
        """ Returns all values in settings.
        
        Same as ``dict.values()``
        
        Does return sections, does not returns values of sections.
        All values are resolved by the resolver
        
        :return: list of values of settingsobject
        :rtype: ``list``
        """
        values = []
        for key in self.keys():
            values.append(self.get(key))
        return values
    
    def items(self):
        """ Returns tulpes of (key, value) of all settings in settingsobject.
        
        Same as ``dict.items()``
        
        Does return sections, does not returns key or values of sections.
        All values are resolved by the resolver
        
        :return: list of values of settingsobject
        :rtype: ``list`` of key, value tuples
        """
        return [(key, self.get(key)) for key in self.keys()]
    
    def sections(self):
        """ Returns all keys of sections in settingsobject.
        
        Returns a list of all sections key in a secttions object.
        Keys of subsetions are not returned.
        
        :return: list of key if the key is a section
        :rtype: ``list``
        """
        return [key.upper() for key, value in self.defaults.keys() if issubclass(value, Section)]
    
    def help(self, key=None):
        """ This function will return help messages for an attr of for the settingsobject itself.
        
        Help messages can be passed to a ``Option`` object 
        or an attr docstring after the attr declaration.
        
        :param key: A string specifying the the attr of with the help message must be returned
                if None is provided the doc of the settingsobject or section is returned (``self.__doc__``)
        :return: Help message for key
        :rtype: `str`
        """
        if key is None:
            return self.__doc__ or None
        for k in key.split('.')[:-1]:
            settings = settings.__getattr__(k.upper())
        lkey = key.split('.')[-1].lower()
        if lkey.upper() in settings.sections():
            return settings.get(lkey).help()
        else:
            try:
                return self.help_dict[lkey]
            except KeyError:
                return None

    def get_dict(self):
        """ Function to get a compleet dict of a settingsobject.
        
        all values are resolved by the resolvers
        if a Section is encounterd it will be converted
        to a dict.
        
        :return: Compleet dict of settingsobject
        :rtype: ``dict``
        """
        d = {}
        for key, value in self.items():
            if isinstance(value, Section):
                d[key] = value.get_dict()
            else:
                d[key] = value
        return d
    
    def _get_resolver(self, type_=None, key=None, default=None ,kwargs={}):
        """ Internal function to get a resolver bases on type, key_name and default value."""
        for cls in reversed(self._resolverTypes):
            if cls.supports(type_, key, default):
                return cls(self, **kwargs)
        for subtype in type_.__mro__:
            for cls in reversed(self._resolverTypes):
                if cls.supports(subtype, key, default):
                    return cls(self, **kwargs)
        return self._get_resolver('default', kwargs=kwargs)

class BaseSettings(Section):
    """ The base class for a settingsobject.
    
    It inherts all function from the `Section` class.
    
    To create a settingsobject extend this class and 
    set all settings attribute in uppercase on the 
    class. 
    
    Exampe (file : package/settings.py):
    
    .. code-block:: python
    
        from settingslib.basesettings import BaseSettings
    
        class Settings(BaseSettings):
            " Doc of the settingsobject."
            SOMESETTING = 'hello'
            INTSETTING = 1
            " This is an help message for INTSETTING"
        
            COMBINED_SETTING = '{INTSETTING} is an int, also {SOMESETTING}'
    
    After you defined the settings class you can create
    if using it constructor like normal classes.
    Extra options can be passed. This extra options
    are used to tell the settingsobject where to find 
    the values to override the default settings.
    
    Example:
    
    .. code-block:: python
    
        settings = Settings('my_app_', [os.path.join(os.path.dirname(__file__) , 'data', 'configfile.conf')])
    
        #hack make is so we can just import the settingsobject
        sys.modules[__name__] = settings
    
    After the code above you can use the settings the following way:
    (package/somefile.py)
    
    .. code-block:: python
    
        from . import settings
    
        def somfunc():
            return settings.COMBINED_SETTING
    
        print '1e time :', somfunc()
        settings.SOMESETTING = 'bye'
        print '2e time', somfunc()
    
    the above will print:
    "1e time : 1 is an int, also hello"
    "2e time : 1 is an int, also bye"
    
    :param env_preflix: if passed os.environ is search for values
            with this preflix. if found they are use to override
            the default values. if the key includes a dot ist mean
            the this value override a value of a Section.
    :param cfgfiles: A list of dict like objects. they are used 
            to override the default settings. You can pass as many
            dicts a you like.
    :type env_preflix: ``str``
    :type cfgfiles: ``list``
    """
    def __init__(self, env_preflix=None, cfgfiles=()):
        options = {}

        userconfig = configfile.ConfigFile()
        
        nosave = {}
        
        envconfig = {}
        if self.use_env and env_preflix:
            for key, value in os.environ.items():
                if key.startswith(env_preflix):
                    self.envconfig[key[len(env_preflix):].lower()] = value
                    
        self.cfgfiles = list(cfgfiles)
        fileconfigs = []
        for file in cfgfiles:
            with open(file, 'r') as fd:
                config = configfile.ConfigFile(False)
                config.read(fd)
                fileconfigs.append(config)
        
        super(BaseSettings, self).__init__(self, options, userconfig, nosave, envconfig, fileconfigs)
    
    def set_options(self, args):
        """ Set commandline options for the settingsobject.
        
        Commandline options override all other options, even
        setting set at runtime and presistend in the userconfig file.
        
        :param args: A dict of object passeble by `vars` to get dict.
                if a dot is in the key it is assum to be for a section.
                the return of argparse.ArgumentParser.parse_args() is 
                supported.
        """
        self.options.clear()
        options = args if  isinstance(args, dict) else vars(args)
        for key, value in options.items():
            if '.' in key:
                dkey, key = key.split('.', 1)
                if dkey not in self.options:
                    self.options[dkey.lower()] = {}
                self.options[dkey.lower()][key] = value
            else:
                self.options[key.lower()] = value
    
    def set_userfile(self, userfile):
        """ Set the location of the userconfigfile
        
        This file is used to load all settings set in 
        previous runs of the application. It is also
        used to save all settings that are set on
        this settingsobject.
        
        This is a good way to set this setting
        
        package/settings.py
        
        .. code-block:: python
        
            import os
            from settingslib.basesettings import BaseSettings
    
            class Settings(BaseSettings):
                DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
                USER_CONFIG_FILE = os.path.join('{DATA_DIR}', 'userconfig.conf')
                CONFIG_FILES = []
        
            # create the settingsobject
            settings = Settings('my_app_', [os.path.join(os.path.dirname(__file__) , 'data', 'configfile.conf')])
        
            # this allows os.environ['my_app_config_files'] to be set to a list of file locations
            # all this locations are loaded as config files.
            if len(settings.CONFIG_FILES) > 0:
                for file in settings.CONFIG_FILES:
                    settings.add_cfgfile(file)
                    
            #hack make is so we can just import the settingsobject
            sys.modules[__name__] = settings
        
        package/__main__.py
        
        .. code-block:: python
        
            from . import settings
        
            def main(args=None):
            
                # create and parse args
                options = argparse.ArgumentParser.parse_args(args)
                settings.set_options(options)
                if options.cfgfiles:
                    for file in options.cfgfiles:
                        settings.add_cfgfile(file)

            if __name__ == '__main__':
                main()
        
        using the methode described above the user has a 
        lot of locations to override the settings a multiple 
        locations.
        
        :param userfile: Location of the configfile
        :type userfile: ``str``
        """
        self.userfile = userfile
        with open(userfile, 'r') as fd:
            self.userconfig.read(fd)
    
    def add_cfgfile(self, file):
        """ Add a config file to the config dicts
        
        Lateste added are first look in the config dicts
        config dict are look up just before default are return
        and are the last possibility to override the defaults.
        
        :param file: The locations of the config file
        :type file: ``str``
        """
        self.cfgfiles.insert(0, file)
        with open(file, 'r') as fd:
            config = configfile.ConfigFile()
            config.read(fd)
            self.fileconfigs.insert(0, config)
        
    def save(self):
        """ Save the config file.
        
        You must call this before your application closes.
        """
        if not self.userfile:
            raise SettingsException("You have not set a userconfig file on your settings object")
        with open(self.userfile, 'r') as fd:
            self.userconfig.write(fd)

class Option(object):
    """ Class to construct advanced options
    
    A class to create more advanced options. This is
    done by passing extra ``**kwargs``. This kwargs can
    override values in the extraOptions dict.
    
    Example:
    
    .. code-block:: python
    
        OPTION = Option('default value', 'str', nosave=True)
        " Help message for this option."
        
    for more advance options you can create a subclass
    
    Example:
    
    .. code-block:: python
    
        class OPTION(Option):
            " Help message for this option."
            default = 'default value'
            resolver = 'str'
            nosave = True
    
    The above will (if used in a settingsobject) result in the same result
    as the example before.
    
    :param default: The default value is this setting
    :param resolver: A string type or a ``Resolver`` object. 
            This is used to create the resolver for this setting.
    :param nosave: If set to True runtime set values are no save when the app stops
    :param solid: If set to True the default is always returned
    :param callback: Function to call after a setting is set. It is called
            with the key and new value of the setting.
    :param initialize: Function to call direct after the settingsobject is created.
            This function is with the key and default value.
    """
    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):
            if name in ['Option']:
                return type.__new__(cls, name, bases, attrs)
            
            cls = type.__new__(cls, name, bases, {})
            
            del attrs['__module__']
            
            default = attrs['default']
            del attrs['default']
            
            if 'resolver' in attrs:
                resolver = attrs['resolver']
                del attrs['resolver']
            else:
                resolver = None
            
            return cls(default, resolver, **attrs)

    def __init__(self, default, resolver=None, __doc__=None, **kwargs):
        self.default = default
        
        if isinstance(resolver, Resolver):
            self.resolver = resolver
        elif resolver is not None:
            self.resolver = Resolver(type=resolver)
        else:
            self.resolver = Resolver(type=default.__class__)
        
        self.__doc__ = __doc__
        self.extraOptions = kwargs

class Resolver(object):
    """ This class works the same the ``Option`` class.
    
    Any ``**kwargs`` passed to this object are passed
    along to the resolver constructor. 
    
    Example:
    
    .. code-block:: python
        
        OPTION = Option('default-value.text', Resolver('file', create=True, file_ext='.text'), nosave=True)
        
    for more advance options you can create a subclass
    
    Example:
    
    .. code-block:: python
    
        class OPTION(Option):
            default = 'default value'
            nosave = True
            class resolver(Resolver):
                type = 'file'
                create = True
                file_ext = '.text'
    
    The above will (if used in a settingsobject) result in the same result
    as the example before.
    
    :param type: The string type use to find the correct resolver.
    :param kwargs: Any ``**kwargs`` to be passed to the resolver.
    """
    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):
            if name in ['Resolver']:
                return type.__new__(cls, name, bases, attrs)
            
            cls = type.__new__(cls, name, bases, {})
            
            del attrs['__module__']
            
            type_ = attrs['type']
            del attrs['type']
            
            return cls(type_, **kwargs)
   
    def __init__(self, type, **kwargs):
        self.type = type
        self.resolverKwargs = kwargs
        
######################## Internal #############################
import ast
import inspect

def get_assign_name(node):
    if not isinstance(node , ast.Assign):
        raise AstException("We can only pass Assign nodes")
    if len(node.targets) > 1:
        raise AstException("To many targets, we don't support this")
    return node.targets[0].id

def get_attr_doc(node):
    doc = {}
    lastname = None
    for clsnode in ast.iter_child_nodes(node):
        if isinstance(clsnode, ast.Assign):
            try:
                lastname = get_assign_name(clsnode)
            except AstException:
                lastname = None
            #print lastname
        elif isinstance(clsnode, ast.Expr):
            if isinstance(clsnode.value, ast.Str) and lastname:
                doc[lastname] = clsnode.value.s
                #print doc[lastname]
                lastname = None
        else:
            lastname = None
    return doc

def get_attr_doc_form_class(clsname, module):
    m = ast.parse(inspect.getsource(module))
    
    # try to find the class by name 'clsname'
    clsnode = None
    for node in ast.walk(m):
        if isinstance(node, ast.ClassDef) and node.name == clsname:
            clsnode = node
            break
    if clsnode is not None:
        doc = dict((k,v) for k,v in get_attr_doc(clsnode).items() if k.isupper())
        return doc
    return {}