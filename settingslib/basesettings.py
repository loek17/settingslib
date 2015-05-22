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

from . import configfile

logger = logging.getLogger(__name__)

__all__ = ['Option', 'Resolver', 'BaseSettings', 'Section',
            'SettingsException', 'add_resolver_type']

class SettingsException(Exception):
    pass
            
def add_resolver_type(cls):
    Section.resolverTypes.append((cls.resolve_types, cls,))
    
class Section(object):
    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):
            if object in bases:
                return type.__new__(cls, name, bases, attrs)

            defaults = {}
            resolvers = {}
            extraOptions = {}
            
            for key, value in attrs.items():
                if key.isupper():
                    if isinstance(value, Option):
                        defaults[key.lower()] = value.default
                        resolvers[key.lower()] = value.resolver
                        extraOptions[key.lower()] = value.extraOptions
                    else:
                        defaults[key.lower()] = value
                        resolvers[key.lower()] = Resolver(value.__class__ if not isinstance(value, type) else value)
                        extraOptions[key.lower()] = {}
                    del attrs[key]
            
            attrs['defaults'] = defaults
            attrs['raw_resolvers'] = resolvers
            attrs['raw_extraOptions'] = extraOptions
            
            return type.__new__(cls, name, bases,attrs)

    defaultExtraOptions = {
        "save" : True,
        "__doc__" : None,                  # A help message for this option
        #"commandoption : False,           # Maybe add support for this later
        #"commandkwargs : False,           # Maybe add support for this later
        "callback" : lambda k,v : None,    # callback called after a settings is set with setting as arg
        "initialize" : lambda k,v : None,  # called with the default, returning something does not update the value, is this usefull??
        "solid" : False                    # If True this value can't be changed, the default is always returned
    }
    
    resolverTypes = []
    use_env = True

    def __init__(self, options, userconfig, nosave, envconfig ,configs):
        
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
            self.extraOptions[key.lower()] = dict(self.defaultExtraOptions)
            self.extraOptions[key.lower()].update(self.raw_extraOptions[key.lower()])
        
        self.resolvers = {}
        for key, resolver in self.raw_resolvers.items():
            r = self.get_resolver(resolver.type, resolver.resolverKwargs)
            self.resolvers[key.lower()] = r
            
            if r.multivalue and not r.has_childs():
                r.set_childs(self.defaults[key.lower()])
            
        for key, default in self.defaults.items():
            self.extraOptions[key.lower()]['initialize'](key, default)
        
        
    
    def __getattr__(self, key):
        " getattr is only called if the key is not found in __dict__"
        if not key.isupper():
            raise AttributeError("Key is not upper and not in __dict__, key : {key}".format(key=key))
        key = key.lower()
        for setting in [self.options, self.userconfig, self.nosave, self.envconfig] + self.fileconfigs + [self.defaults]:
            if key in setting.keys():
                return self.resolvers[key].get(setting[key])
        raise AttributeError("Key does not exists in Settings object, key : {key}".format(key=key))
    
    def __setattr__(self, key, value):
        if not key.isupper():
            return object.__setattr__(self, key, value)
        if self.resolvers[key.lower()].validate(value):
            if self.extraOptions[key.lower()]['save'] is not False:
                self.userconfig[key.lower()] = self.resolvers[key.lower()].raw(value)
            else:
                self.nosave[key.lower()] = value
        else:
            raise SettingsException("This value is not valid for this key, key : {key}, value : {value}, {resolver}".format(key=key,value=value,resolver=self))
        # call the callback after the setting is set.
        self.extraOptions[key.lower()]['callback'](key, value)
    
    def get(self, key):
        return self.__getattr__(key.upper())
    
    def set(self, key, value):
        self.__setattr__(key.upper(), value)
    
    def has(self, key):
        return key.upper() in self.keys()
    
    def keys(self):
        return [key.upper() for key in self.defaults.keys()]
    
    def values(self):
        values = []
        for key in self.keys():
            values.append(self.get(key))
        return values
    
    def items(self):
        return [(key, self.get(key)) for key in self.keys()]
    
    def get_dict(self):
        d = {}
        for key, value in self.items():
            if isinstance(value, _Settings):
                d[key] = value.get_dict()
            else:
                d[key] = value
        return d
    
    def get_resolver(self, types, kwargs={}):
        if isinstance(types, type): # it is a class
            types = types.__mro__ # we search the mro, maybe it is a subclass of an known type
        if not isinstance(types, (list, tuple)): # its a string
            types = [types]
            
        for cls in types: 
            for clstypes , class_ in self.__class__.resolverTypes:
                if cls in clstypes:   
                    return class_(self, **kwargs)
        logger.warning("We can't find type : {type}, using the default.".format(type=type))
        
        from . import resolvers
        return resolvers.SettingsResolver(self, **kwargs) 

class BaseSettings(Section):

    def __init__(self, env_preflix=None, cfgfiles=()):
        options = {}

        userconfig = configfile.ConfigFile(False)
        
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
        
        super(BaseSettings, self).__init__(options, userconfig, nosave, envconfig, fileconfigs)
    
    def set_options(self, args):
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
        self.userfile = userfile
        with open(userfile, 'r') as fd:
            self.userconfig.read(fd)
    
    def add_cfgfile(self, file):
        self.cfgfiles.append(file)
        with open(file, 'r') as fd:
            config = configfile.ConfigFile(False)
            config.read(fd)
            self.fileconfigs.append(config)
        
    def save(self):
        if not self.userfile:
            raise SettingsException("You have not set a userconfig file on your settings object")
        with open(self.userfile, 'r') as fd:
            self.userconfig.write(fd)

class Option(object):
    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):
            if object in bases:
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

    def __init__(self, default, resolver=None, **kwargs):
        self.default = default
        
        if isinstance(resolver, Resolver):
            self.resolver = resolver
        elif resolver is not None:
            self.resolver = Resolver(type=resolver)
        else:
            self.resolver = Resolver(type=default.__class__)

        self.extraOptions = kwargs

class Resolver(object):
    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):
            if object in bases:
                return type.__new__(cls, name, bases, attrs)
            
            cls = type.__new__(cls, name, bases, {})
            
            del attrs['__module__']
            
            type_ = attrs['type']
            del attrs['type']
            
            return cls(type_, **kwargs)
   
    def __init__(self, type, **kwargs):
        self.type = type
        self.resolverKwargs = kwargs
        
