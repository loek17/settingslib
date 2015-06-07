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
    Section.resolverTypes.append(cls)
    
class Section(object):
    class __metaclass__(type):
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

    defaultExtraOptions = {
        "save" : True,
        #"commandoption" : False,           # Maybe add support for this later
        #"commandkwargs" : False,           # Maybe add support for this later
        "callback" : lambda k,v : None,    # callback called after a settings is set with setting as arg
        "initialize" : lambda k,v : None,  # called with the default, returning something does not update the value, is this usefull??
        "solid" : False                    # If True this value can't be changed, the default is always returned
    }
    
    resolverTypes = []
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
            self.extraOptions[key.lower()] = dict(self.defaultExtraOptions)
            self.extraOptions[key.lower()].update(self.raw_extraOptions[key.lower()])
        
        self.resolvers = {}
        for key, resolver in self.raw_resolvers.items():
            if resolver is not None:
                r = self.get_resolver(resolver.type,key=None, default=None, kwargs=resolver.resolverKwargs)
            else:
                r = self.get_resolver(self.defaults[key.lower()].__class__, key=key.lower(), default=self.defaults[key.lower()])
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

        if self.extraOptions[key]['solid'] is True:
            return self.defaults[key]

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
        settings = self
        for k in key.split('.')[:-1]:
            settings = settings.__getattr__(k)
        return settings.__getattr__(key.split('.')[-1].upper())
    
    def set(self, key, value):
        settings = self
        for k in key.split('.')[:-1]:
            settings = settings.get(k)
        settings.__setattr__(key.split('.')[-1].upper(), value)
    
    def has(self, key):
        try:
            self.get(key)
        except AttributeError:
            return False
        else:
            return True
    
    def keys(self):
        return [key.upper() for key in self.defaults.keys()]
    
    def values(self):
        values = []
        for key in self.keys():
            values.append(self.get(key))
        return values
    
    def items(self):
        return [(key, self.get(key)) for key in self.keys()]
    
    def sections(self):
        return [key.upper() for key, value in self.defaults.keys() if issubclass(value, Section)]
    
    def help(self, key=None):
        if key is None:
            return self.__doc__ or "No help description."
        for k in key.split('.')[:-1]:
            settings = settings.get(k)
        if key.split('.')[:-1] in settings.sections():
            return settings.get(key.split('.')[:-1]).help()
        else:
            try:
                return self.help_dict[key.split('.')[:-1].lower()]
            except KeyError:
                return "No help description."
            
        
    
    def get_dict(self):
        d = {}
        for key, value in self.items():
            if isinstance(value, Section):
                d[key] = value.get_dict()
            else:
                d[key] = value
        return d
    
    def get_resolver(self, type_=None, key=None, default=None ,kwargs={}):
        for cls in reversed(self.resolverTypes):
            if cls.supports(type_, key, default):
                return cls(self, **kwargs)
        for subtype in type_.__mro__:
            for cls in reversed(self.resolverTypes):
                if cls.supports(subtype, key, default):
                    return cls(self, **kwargs)
        return self.get_resolver('default')

class BaseSettings(Section):

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