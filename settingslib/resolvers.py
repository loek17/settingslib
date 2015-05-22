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

import re
import sys
import collections
import logging
import os
import hashlib
import base64
import json

from . import configfile
from . import basesettings

logger = logging.getLogger(__name__)

#__all__ = ['SettingsResolver' , 'IntSettingsResolver', 'FloatSettingsResolver', 'BoolSettingsResolver',
#            'StrSettingsResolver', 'UnicodeSettingsResolver', 'DirSettingsResolver', 'FileSettingsResolver',
#            'PassSettingsResolver', 'SecretSettingsResolver',
#            'TupleSettingsResolver', 'NamedTupleSettingsResolver', 'ListSettingsResolver', 'DictSettingsResolver',
#            'SectionSettingsResolver', 'ResolveException']

class ResolveException(Exception):
    pass

class SettingsResolver(object):
    multivalue = False
    
    resolve_types = ('default', None)
    
    def __init__(self , settings):
        self.settings = settings
    
    def __iter__(self):
        " We implent __iter__ so we kan be passed to 'settings.get_resolver(type, kwargs)' as many time a needed without problems. "
        return (self, None)
        
    def get(self, value):
        " Cast the str value to the types used in the app."
        return value
    
    def raw(self, value):
        " Turn the value in to a str so it can be saved to a file using the configfile module."
        return str(value)
    
    def validate(self, value):
        return True

class IntSettingsResolver(SettingsResolver):
    
    resolve_types = ('int', int)
    
    def __init__(self, settings, min=None, max=None, step=None, choices=None):
        super(IntSettingsResolver, self).__init__(settings)
        self.min = min
        self.max = max
        if step and min and max:
            self.choices = [x for x in xrange(min, max, step)]
            self.max = None
            self.min = None
        else:
            self.choices = choices
    
    def get(self, value):
        return int(value)
    
    def validate(self, value):
        if self.max or self.min:
            if self.max:
                return self.min < value < self.max
            else:
                return self.min < value
        
        if self.choices:
            return value in self.choices
        
        return super(IntSettingsResolver, self).validate(value)

class FloatSettingsResolver(IntSettingsResolver):
    
    resolve_types = ('float', float)
    
    def get(self, value):
        return float(value)

class BoolSettingsResolver(IntSettingsResolver):

    NO_VALUES = [False, "False", 0, "0", "no", "n"]
    YES_VALUES = [True, "True", 1, "1", "yes", "y"]
    
    resolve_types = ('bool', bool)
    
    def __init__(self, settings):
        super(BoolSettingsResolver, self).__init__(settings, choices=self.NO_VALUES + self.YES_VALUES)
    
    def get(self, value):
        if value in self.NO_VALUES:
            return False
        elif value in self.YES_VALUES:
            return True

class StrSettingsResolver(SettingsResolver):
    
    SETTING_REGEX = '\{(\w+)\}'
    
    resolve_types = ('str', str)
    
    def __init__(self, settings, choices=None):
        super(StrSettingsResolver, self).__init__(settings)
        self.choices = choices
        
    def get(self, value):
        value = str(value)
        if re.search(self.SETTING_REGEX, value):
            kwargs = dict((v , self.settings.get(v)) for v in re.findall(self.SETTING_REGEX, value) if self.settings.has(v))
        else:
            kwargs = {}
        
        return value.format(**kwargs)
    
    def validate(self, value):
        if self.choices and value in self.choices:
            return True
        elif self.choices:
            return False
        
        return super(StrSettingsResolver, self).validate(value)

class UnicodeSettingsResolver(StrSettingsResolver):
    
    resolve_types = ('unicode', unicode)
    
    def get(self, value):
        return super(UnicodeSettingsResolver, self).get(value).decode('utf8')
    
    def raw(self, value): 
        return super(UnicodeSettingsResolver, self).set_value(value).encode('utf8')

class PathSettingsResolver(StrSettingsResolver):
    
    resolve_types = ('path',)
    
    def __init__(self, settings):
        super(DirSettingsResolver, self).__init__(settings)
    
    def get(self, value):
        value = super(PathSettingsResolver, self).get(value)
        
        if sys.platform == 'win32':
            value = value.replace('/', '\\') if '/' in value else value
        else:
            value = value.replace('\\', '/') if '\\' in value else value
        return value

class DirSettingsResolver(PathSettingsResolver):
    
    resolve_types = ('dir',)
    
    def __init__(self, settings, create=False):
        super(DirSettingsResolver, self).__init__(settings)
        self.create = create

    def get(self, value):
        value = super(DirSettingsResolver, self).get(value)
        
        if self.create and not os.path.isdir(value):
            os.makedirs(value)
        return value
                

class FileSettingsResolver(PathSettingsResolver):
    
    resolve_types = ('file',)
    
    def __init__(self, settings, create=False, file_ext=None):
        super(FileSettingsResolver, self).__init__(settings)
        self.create = create
        self.file_ext = file_ext
    
    def get(self, value):
        value = super(FileSettingsResolver, self).get(value)
            
        if self.create and not os.path.isfile(value):
            open(value, 'a').close()
        return value
    
    def validate(self, value):
        if self.file_ext and not value.endswith(self.file_ext):
            return False
        return super(FileSettingsResolver, self).validate(value)

class SecretSettingsResolver(SettingsResolver):
    
    resolve_types = ('secret',)
    
    def __init__(self, settings, get_secret=None, encode=None, decode=None):
        super(SecretSettingsResolver, self).__init__(settings)
        self.get_secret = get_secret if get_secret is not None else self.get_secret
        self.encode = encode if encode is not None else self.encode
        self.decode = decode if decode is not None else self.decode
    
    def get(self, value):
        return self.decode(self.get_secret(), value)
    
    def raw(self, value):
        return self.encode(self.get_secret(), value)
    
    def get_secret(self):
        try:
            return self.settings.SECRET_KEY
        except AttributeError:
            return "kvlsadvc_super_secret_key_vslkvnre"
    
    def encode(self, key, clear):
        enc = []
        for i in range(len(clear)):
            key_c = key[i % len(key)]
            enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
            enc.append(enc_c)
        return base64.urlsafe_b64encode("".join(enc))

    def decode(self, key, enc):
        dec = []
        enc = base64.urlsafe_b64decode(enc)
        for i in range(len(enc)):
            key_c = key[i % len(key)]
            dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
            dec.append(dec_c)
        return "".join(dec)

class PassSettingsResolver(SettingsResolver):
    
    resolve_types = ('pass','password')
    
    class Password(object):
        def __init__(self, password, resolver):
            self.hasher = hasher
            self.password = password
        
        def equals(self, other):
            return self.password == self.hasher(other)
        
        def __eq__(self, other):
            return self.equals(other)
        
        def __str__(self):  
            return self.password
        
        def __repr__(self): 
            return '{name}({password})'.format(name=self.__name__, password=self.password)
    
    def __init__(self, settings, get_salt=None, hasher=None):
        super(PassSettingsResolver, self).__init__(settings)
        self.get_salt = get_salt if get_salt is not None else self.get_salt
        self.hasher = hasher if hasher is not None else self.hasher
    
    def get(self, value):
        return self.Password(value, self.hash)
    
    def raw(self, value):
        return self.hash(value)
    
    def hash(self, value, salt):
        return hashlib.sha256('{}.{}'.format(value,salt).hexdigest())
    
    def get_salt(self, value):
        return ''
        
class MultiValueSettingsResolver(SettingsResolver):
    multivalue = True
    resolvers = False
    
    def has_childs(self):
        return bool(self.resolvers)
    
    def set_childs(self, default):
        return
    
class TupleSettingsResolver(MultiValueSettingsResolver):
    """
    tuple setting, child resolvers are used to get the values in the tuple
    """
    delimiter = ' , '
    resolve_types = ('tuple', tuple)
    
    def __init__(self, settings, childs=None):
        super(TupleSettingsResolver, self).__init__(settings)
        self.resolvers = []
        
        if childs:
            for r in childs:
                if isinstance(r, basesettings.Resolver):
                    resolver = settings.get_resolver(r.type, r.resolverKwargs)
                else:
                    resolver = settings.get_resolver(r)
                self.resolvers.append(resolver)
        
    def get(self, value):
        if isinstance(value, basestring):
            value = value.split(self.delimiter)
        return tuple(self.resolvers[i].get(v) for i,v in enumerate(value))
    
    def raw(self, value):
        l = []
        for i,v in enumerate(value):
            l.append(self.resolvers[i].raw(v))
            if self.delimiter in l[i]:
                logger.warning("Delimiter in raw value, key : {key}, value : {value}".format(key=ReferenceResolverMixin.get_key(self), value=value))
        return self.delimiter.join(l)
    
    def validate(self, value):
        if len(value) != len(self.resolvers):
            return False
        for i,v in enumerate(value):
            if not self.resolvers[i].validate(value):
                return False
        return True
    
    def set_childs(self, defaults):
        for i,d in enumerate(defaults):
            r = self.settings.get_resolver(d.__class__, {})
            if r.multivalue and not r.has_childs():
                r.set_childs(d)
            self.resolvers.append(r)

class NamedTupleSettingsResolver(TupleSettingsResolver):
    
    resolve_types = ('namedtuple',)
    
    def __init__(self, settings, keys=(), childs=()):
        super(NamedTupleSettingsResolver).__init__(settings, childs)
        self.cls = collections.namedtuple("NamedSettingsTulpe" , keys)
        
    def get(self, value):
        return self.cls(*super(NamedTupleSettingsResolver).get(value))

class ReferenceResolverMixin(object):
    def get_key(self):  
        for key, resolver in self.settings.resolvers.items():
            if self is resolver:
                return key
        
class ListSettingsResolver(MultiValueSettingsResolver, ReferenceResolverMixin):
    
    resolve_types = ('list', list)
    
    class SyncList(list):
        
        def __init__(self, key, l, resolver, settings):
            self._l = l
            self._key = key
            self._resolver = resolver
            self._settings = settings
        
        def __sort(self):
            if self._resolver.sort is not None:
                self._resolver.sort(self._l)
        
        def __sync(self):
            " This function makes sure that we write all changes to the list back to the userfile. "
            self.__sort()
            self._settings.userconfig[self._key.lower()] = self._resolver._raw(self._l)
        
        def append(self, v):
            self._l.append(self._resolver.resolver.get(v))
            self.__sync()
        def count(self):
            return self._l.count()
        def extend(self, l):
            self._l.extend(self._resolver.get(l))
            self.__sync()
        def index(self, obj):
            return self._l.index(obj)
        def insert(self, i, obj):
            self._l.insert(i, self._resolver.resolver.get(obj))
            self.__sync()
        def pop(self):
            v = self._l.pop()
            self.__sync()
            return v
        def remove(self, obj):
            self._l.remove(self._resolver.resolver.get(obj))
            self.__sync()
        def reverse(self):
            if self._resolver.sort is not None:
                raise Exception("The sorting of this list is solid")
            self._l.reverse()
            self.__sync()
        def sort(self,func):
            if self._resolver.sort is not None:
                raise Exception("The sorting of this list is solid")
            self._l.sort(func)
            self.__sync()

        def __getitem__(self,i):
            return self._l[i]
        def __setitem__(self,i, value):
            self._l[i] = self._resolver.resolver.get(value)
            self.__sync()
        def __delitem__(self,i):
            del self._l[i]
            self.__sync()

        def __getslice__(self, start, end):
            return self._l[start:end]
        def __setslice__(self, start, end, value):
            self._l[start:end] = self._resolver.get(value)._l
            self.__sync()
        def __delslice__(self, start, end):
            del self._l[start:end]
            self.__sync()

        def __eq__(self, other):    
            return self._l.__eq__(other)
        def __ge__(self, other): 
            return self._l.__ge__(other)
        def __gt__(self, other):
            return self._l.__gt__(other)  
        def __lt__(self, other):
            return self._l.__lt__(other)
        def __ne__(self, other):  
            return self._l.__ne__(other)
            
        def __add__(self, value):
            return self._l + self._resolver.get(value)._l
        def __iadd__(self, value):
            self._l =+ self._resolver.get(value)._l
            self.__sync()
        def __mul__(self, i):
            return self._l.__mul__(i)
        def __rmul__(self, i):
            return self._l.__rmul__(i)
        def __imul__(self, i):
            self._l.__imul__(i)
            self.__sync()
        
        
        def __contains__(self, value):
            return self._resolver.resolver.get(value) in self._l
        def __len__(self):
            return len(self._l)
        def __iter__(self):
            return iter(self._l) 
        def __format__(self):
            return self._l.__format__()
        def __reversed__(self):
            return reversed(self._l)

        def __reduce__(self):
            return self._l.__reduce__()
        def __reduce_ex__(self, protocol):
            return self._l.__reduce_ex__(protocol)
    
    def __init__(self, settings, child=None, duplicate=False, options = None, sort=None, minLen=None, maxLen=None):
        super(ListSettingsResolver, self).__init__(settings)
        self.resolver = None
        self.resolvers = []
        self.duplicate = duplicate
        self.options = options
        self.minLen = minLen
        self.maxLen = maxLen
        self.sort = sort
        
        if child:
            if isinstance(child, basesettings.Resolver):
                self.resolver = settings.get_resolver(child.type, child.resolverKwargs)
            else:
                self.resolver = settings.get_resolver(child)
            self.resolvers = (self.resolver,)
        
    def get(self, values):
        key = self.get_key()
        if isinstance(values, self.SyncList):
            raise ResolveException("ListSettingsResolver : We are getting a synclist in the get function, this should not be possible")
        elif isinstance(values, list):
            values = values[:]
        else:
            values = self._get(values)
        return self.SyncList(key, values, self, self.settings)
    
    def _get(self, values):
        l = []
        for val in json.loads(values):
            l.append(self.resolver.get(val))
        return l
    
    def raw(self, value):
        if isinstance(value, self.SyncList):
            value = value._l
        return self._raw(value)
    
    def _raw(self, values):
        return json.dumps([self.resolver.raw(value) for value in values])
    
    def validate(self, values):
        for value in values:
            if self.options and value not in self.options:
                return False

        if self.minLen and len(values) < self.minLen:
            return False
        
        if self.maxLen and len(values) > self.maxLen:
            return False
        
        if not self.duplicate and len(set(values)) != len(values):
            return False
        
        return super(StrSettingsResolver, self).validate(value)
    
    def set_childs(self, defaults):
        if defaults:
            r = self.settings.get_resolver(defaults[0].__class__, {})
            if r.multivalue and not r.has_childs():
                r.set_childs(defaults[0])
            self.resolver = r
        else:
            self.resolver = StrSettingsResolver(self.settings)
        self.resolvers = (self.resolver,)
            
    
class DictSettingsResolver(MultiValueSettingsResolver, ReferenceResolverMixin):
    """ 
    It not a good idea to use the dicts in your settings, you have sections so use them!!!
    
    Warning : all values in a dict will always be str type
    """
    
    resolve_types = ('dict', dict)
    
    class SyncDict(dict):
        def __init__(self, key, d, resolver, settings):
            self._d = d
            self._key = key
            self._resolver = resolver
            self._settings = settings
            
            if resolver.default is not None:
                self._d.setdefault(resolver.default)
        
        def __sync(self):
            " This function makes sure that we write all changes to the list back to the userfile. "
            self._settings.userconfig[self._key.lower()] = self._resolver._raw(self._d)
        
        def copy(self):
            return self._d.copy()
        def clear(self):
            self._d.clear()
            self.__sync()
        def update(self, d):
            self._d.update(d)
            self.__sync()
        def get(self, key, default=None):
            return self._d.get(key, default)
            
        def fromkeys(self, keys, value=None):
            self._d.fromkeys(keys, value)
            self.__sync()
        def setdefault(self, default):
            ResolveException("this is not possible, use the default keyword of the resolver")
        def has_key(self, key):
            return self._d.has_key(key)
        
        def pop(self, key, default=None):
            v =  self._d.pop(key, default)
            self.__sync()
            return v
        def popitem(self):
            v = self._d.popitem()
            self.__sync()
            return v

        def keys(self):
            return self._d.keys()
        def values(self):
            return self._d.values()
        def items(self):
            return self._d.items()
        
        def iterkeys(self):
            return self._d.iterkeys()
        def itervalues(self):
            return self._d.itervalues()
        def iteritems(self):
            return self._d.iteritems()
        
        def viewkeys(self): 
            return self._d.viewkeys()
        def viewvalues(self):
            return self._d.viewvalues()
        def viewitems(self):    
            return self._d.viewitems()
        
        #def __getattribute__(self, key):
        #    return self._d.__dict__['__getattribute__'](key)
        #def __setattr__(self, key, value):
        #    self._d.__setattr__(key, value)
        #def __delattr__(self, key):
        #    self._d.__delattr__(key)
        
        def __getitem__(self, key):
            return self._d[key]
            self.__sync() # if defaults are set than getitem may change the dict
        def __setitem__(self, key, value):
            self._d[key] = value
            self.__sync()
        def __delitem__(self, key):
            del self._d[key]
            self.__sync()
        
        def __cmp__(self, other):
            return self._d.__cmp__(other)
        def __eq__(self, other):
            return self._d.__eq__(other)
        def __gt__(self, other):
            return self._d.__gt__(other)
        def __ge__(self, other):    
            return self._d.__ge__(other)
        def __le__(self, other):
            return self._d.__le__(other)
        def __lt__(self, other):
            return self._d.__lt__(other)
        def __ne__(self, other):
            return self._d.__ne__(other)
            
        def __format__(self):
            return self._d.__format__(self)
        def __contains__(self, key):
            return key in self._d
        def __iter__(self):
            return iter(self._d)
        def __len__(self):
            return len(self._d)
        def __sizeof__(self):
            return self._d.__sizeof__()
         
        def __reduce__(self):
            return self._d.__reduce__()
        def __reduce_ex__(self, protocol):
            return self._d.__reduce_ex__(protocol)

    def __init__(self, settings, default=None):
        super(DictSettingsResolver, self).__init__(settings)
        self.default = default
        self.resolvers = True
    
    def get(self, values):
        key = self.get_key()
        if isinstance(values, self.SyncDict):
            raise ResolveException("DictSettingsResolver : We are getting a syncdict in the get function, this should not be possible")
        elif isinstance(values, dict):
            values = dict(values)
        else:
            values = self._get(values)
        return self.SyncDict(key, values, self, self.settings)
    
    def _get(self, value):
        return json.loads(value)
    
    def raw(self,value):
        if isinstance(value, self.SyncDict):
            value = value._d
        return self._raw(value)
    
    def _raw(self, value):
        return json.dumps(value)
    
    def validate(self, value):
        return True

class SectionSettingsResolver(SettingsResolver, ReferenceResolverMixin):
    
    resolve_types = ('subsection', basesettings.Section)
    
    def __init__(self , settings):
        super(SectionSettingsResolver, self).__init__(settings)
    
    def get(self, value):
        key = self.get_key()
        if isinstance(value, basesettings.Section):
            # the default is passed 
            section = value
        else:
            section = self.settings.defaults[key.lower()]
        
        # try to get the userconfig of this section, if it does not exist we create it.
        try:
            userconfig = self.settings.userconfig[key.lower()]
        except KeyError:
            userconfig = self.settings.userconfig[key.lower()] = configfile.ConfigFile(autogrown=False)
        
        # try to pasover the nosave values for this section
        try:
            nosave = self.settings.nosave[key.lower()]
        except KeyError:
            nosave = self.settings.nosave[key.lower()] = {}

        
        # try to get the this section form a the config files, if it does not exist we pass.
        fileconfigs = []
        for cfg in self.settings.fileconfigs:
            try:
                fileconfigs.append(cfg[key.lower()])
            except KeyError:
                pass
        
        try:
            options = self.settings.options[key.lower()]
        except KeyError:
            options = self.settings.options[key.lower()] = {}
        
        try:
            envconfig = self.settings.envconfig[key.lower()]
        except KeyError:
            envconfig = self.settings.envconfig[key.lower()] = {}
        
        return section(options, userconfig, nosave, envconfig, fileconfigs)
    
    def raw(self, value): 
        raise ResolveException("It is not possible to set a section")

# register all resolvers with base settings cls
for name, cls in globals().items():
    if hasattr(cls, 'resolve_types'):
        basesettings.add_resolver_type(cls)
