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

""" 
==================    
Default Resolvers
==================

This module holds all the default resolvers used by "BaseSettings".

Normally you don't have to import something form this module, Resolver
are found automatic based on the default type or the name of the key.

based on the following steps we try to find the resolver.

1. If the developer provided a type, use it to find the resolver.

2. Try to use the default.__class__ , name of the setting and the default to find the resolver.

3. return default "SettingResolver"

The following table is used to map the resolvers.

+----------------------+-------------+----------------+--------------+------------------------------+------------+
| String type          | class       | key startswith | key endswith | Resover                      | Requires   |
+======================+=============+================+==============+==============================+============+
| 'default'            |             |                |              | `SettingsResolver`           |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'int'                | ``int``     |                |              | `IntSettingsResolver`        |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'float'              | ``float``   |                |              | `FloatSettingsResolver`      |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'bool'               | ``bool``    |                |              | `BoolSettingsResolver`       |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'str'                | ``str``     |                |              | `StrSettingsResolver`        |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'unicode'            | ``unicode`` |                |              | `UnicodeSettingsResolver`    |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'path'               |             |                |              | `PathSettingsResolver`       |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'dir'                |             |                | 'dir'        | `DirSettingsResolver`        |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'file'               |             |                | 'file'       | `FileSettingsResolver`       |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'secret'             |             |                |              | `SecretSettingsResolver`     |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'password', 'pass'   |             |                |              | `PassSettingsResolver`       |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'timedelta'          |``timedelta``|                |              | `TimeDeltaSettingsResolver`  |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'datetime'           |``datetime`` |                |              | `DateTimeSettingsResolver`   |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'time'               | ``time``    |                |              | `TimeSettingsResolver`       |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'date'               | ``date``    |                |              | `DateSettingsResolver`       |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'tulpe'              | ``tulpe``   |                |              | `TulpeSettingsResolver`      |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'namedtulpe'         |             |                |              | `NamedTulpeSettingsResolver` |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'list'               | ``list``    |                |              | `ListSettingsResolver`       |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
| 'dict'               | ``dict``    |                |              | `DictSettingsResolver`       |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
|                      | ``Section`` |                |              | `SectionSettingsResolver`    |            |
+----------------------+-------------+----------------+--------------+------------------------------+------------+
"""
from __future__ import absolute_import

import re
import sys
import collections
import logging
import os
import hashlib
import base64
import json
import datetime

from . import configfile
from . import basesettings

logger = logging.getLogger(__name__)

__all__ = ['SettingsResolver' , 'IntSettingsResolver', 'FloatSettingsResolver', 'BoolSettingsResolver',
            'StrSettingsResolver', 'UnicodeSettingsResolver', 'DirSettingsResolver', 'FileSettingsResolver',
            'PassSettingsResolver', 'SecretSettingsResolver', 'DateSettingsResolver', 'TimeSettingsResolver',
            'DatetimeSettingsResolver', 
            'TupleSettingsResolver', 'NamedTupleSettingsResolver', 'ListSettingsResolver', 'DictSettingsResolver',
            'SectionSettingsResolver', 'ResolveException']

class ResolveException(Exception):
    pass

class SettingsResolver(object):
    """ Default SettingsResolver 
    
    :param settings: The settingsobject this resolver belongs to
    :param validate: Must be a callable that accecpts (self, value), Must return True of False based on value
    :type settings: `BaseSettings`
    :type validate: Fuction or Callable
    :return: return description
    :rtype: the return type description
    """
    
    multivalue = False
    """ True is the get value can hold childs, else False."""
    
    resolve_types = ('default',)
    """ The string types and real type this resolver supports."""
    
    def __init__(self , settings, validate=None):
        self.settings = settings
        self.validate_fuc = validate
        
    def get(self, value):
        """ Coerce the str value to the types used in the app.
        
        :param value: The value to coerce to the final type
        :type value: `str` of final type
        :return: Return same value as passed to the function
        :rtype: The same type as passed to the function
        """
        return value
    
    def raw(self, value):
        """ Turn the value in to a str so it can be saved to a file using the configfile module.
        
        This function is called we a attribute of `BaseSettings` is set. Its job is to turn the
        value in a string. The function `get` must be able to load this string to the final type.
        
        :param value: The value to coerce to a savable type
        :type value: supported type of this resolver
        :return: Returns the savable converted value
        :rtype: `str`
        """
        return str(value)
    
    def validate(self, value):
        """ Validate if ``value`` is a validate value for this settings attribute.
        
        This is called before a value is set to a settings attribute to make sure
        it is a valid value. If not `BaseSettings` will raise an Exception.
        
        If ``__init__`` was provided with a `validate` keyword, this is used to 
        validate the value. Else the default is used.
        
        :param value: The value to validate
        :type value: supported type of this resolver
        :return: Returns True of False based on the value provided
        :rtype: ``bool``
        """
        if self.validate_fuc is not None:
            return self.validate_fuc(value)
        return self._validate(value)
    
    def _validate(self, value):
        """ Default validate function.
        
        :param value: The value to validate
        :type value: supported type of this resolver
        :return: Returns True of False based on the value provided
        :rtype: bool
        """
        return True
    
    @classmethod
    def supports(cls, type=None, key=None, default=None):
        """ Checks of this Resolver supports a settings attribute base on type, attribute key and default value.
        
        We first check if the attribute is supported base on the key and the default. If
        that is not the case we check if type is in ``resolve_types``.
        
        :param type: A string descripting a resolver type of the python class.
        :param key: The name of settings attribute.
        :param default: The default value of the settings attribute.
        :type type: ``type`` (Python Class) of ``str``
        :type key: ``str``
        :type default: supported final type
        :return: Returns True if attribute is supported else False.
        :rtype: ``bool``
        """
        try:
            if cls._supports(key, default):
                return True
        except:
            pass
        return type in cls.resolve_types
    
    @classmethod
    def _supports(cls, key, default):
        """ Checks of this Resolver supports a settings attribute base on attribute key and default value."""
        return False

class IntSettingsResolver(SettingsResolver):
    """ Resolver to coerce values to `int`
    
    :param min: the minimum int value allowed
    :param max: the maximum int value allowed
    :param step: steps just like in xrange, use with `min` and `max`
    :param choices: a list of int allowed to be set, use without min, max and step
    :type min: ``int``
    :type max: ``int``
    :type step: ``int``
    :type choices: ``list``
    """
    resolve_types = ('int', int)
    
    def __init__(self, settings, validate=None, min=None, max=None, step=None, choices=None):
        super(IntSettingsResolver, self).__init__(settings, validate)
        self.min = min
        self.max = max
        if step and min and max:
            self.choices = [x for x in xrange(min, max, step)]
            self.max = None
            self.min = None
        else:
            self.choices = choices
    
    def get(self, value):
        """ Coerce ``value`` to ``int``.
        
        :return: Value as int.
        :rtype: ``int``
        """
        return int(value)
    
    def _validate(self, value):
        """ Validate if value is between min and max or is in choices
        
        :param value: A value to validate
        :type value: ``int``
        :return: True or False based of value
        :rtype: ``bool``
        """
        if self.max or self.min:
            if self.max:
                return self.min < value < self.max
            else:
                return self.min < value
        
        if self.choices:
            return value in self.choices
        
        return super(IntSettingsResolver, self)._validate(value)

class FloatSettingsResolver(IntSettingsResolver):
    """ Resolver to coerce values to ``float`` """
    
    resolve_types = ('float', float)
    
    def get(self, value):
        """ Coerce `value` to `float`.
        
        :return: Value as float
        :rtype: `float`
        """
        return float(value)

class BoolSettingsResolver(IntSettingsResolver):
    """ Resolver to coerce values to `bool`.
    
    We are very strict so only the following values are
    considered False:
    
    - False, "False", 0, "0", "no", "n"
    
    
    Only the following values are considered True
    
    - True, "True", 1, "1", "yes", "y"
    
    We don't alway empty lists and dicts because the don't coerce well
    to string.
    
    No extra validate args are needed.
    """
    
    NO_VALUES = [False, "False", 0, "0", "no", "n"]
    YES_VALUES = [True, "True", 1, "1", "yes", "y"]
    
    resolve_types = ('bool', bool)
    
    def __init__(self, settings, validate=None):
        super(BoolSettingsResolver, self).__init__(settings, validate, choices=self.NO_VALUES + self.YES_VALUES)
    
    def get(self, value):
        """ Coerce `value` to `bool`.
        
        :param value: The value to coerce
        :type value: `str`, `int` or `bool`
        :return: Value as bool
        :rtype: `bool`
        """
        if value in self.NO_VALUES:
            return False
        elif value in self.YES_VALUES:
            return True

class StrSettingsResolver(SettingsResolver):
    """ Resolver to coerce values to `str`.
    
    This resolver also implements the functionalty to
    make string based on other settings values. This 
    is done using the `str.format()` function. 
    
    Example:
    
    .. code-block:: python
    
        class Settings(BaseSettings):
            IP = '127.0.0.1'
            PORT = 5589
            HOST = '{HOST}:{PORT}'
    
    :param choices: List of valid strings for this setting
    :type choices: ``list``
    """
    
    SETTING_REGEX = '\{([1-9A-Z_\.]+)\}'
    
    resolve_types = ('str', str)
    
    def __init__(self, settings, validate=None, choices=None):
        super(StrSettingsResolver, self).__init__(settings, validate)
        self.choices = choices
        
    def get(self, value):
        """ Coerce `value` to ``str``.
        
        :param value: The value to coerce
        :type value: ``str``
        :return: Value as string, value replace is done.
        :rtype: ``str``
        """
        value = str(value)
        if re.search(self.SETTING_REGEX, value):
            kwargs = dict((v.split('.')[0] , self.settings.root.get(v.split('.')[0])) for v in re.findall(self.SETTING_REGEX, value))
        else:
            kwargs = {}
        
        return value.format(**kwargs)
    
    def _validate(self, value):
        """ Validate if value is in choices (if choices was supplied)
        
        :param value: A value to validate
        :type value: ``str``
        :return: True or False based of value
        :rtype: ``bool``
        """
        if self.choices and value in self.choices:
            return True
        elif self.choices:
            return False
        
        return super(StrSettingsResolver, self)._validate(value)

class UnicodeSettingsResolver(StrSettingsResolver):
    """ Resolver to coerce values to ``unicode``.
    
    Works the same as the ``StrSettingsResolver``.
    
    :param choices: List of valid strings for this setting.
    :type choices: ``list``
    """
    
    resolve_types = ('unicode', unicode)
    
    def get(self, value):
        """ Coerce `value` to ``unicode``.
        
        :param value: The value to coerce.
        :type value: ``str``
        :return: Value as string, value replace is done.
        :rtype: ``unicode``
        """
        return super(UnicodeSettingsResolver, self).get(value).decode('utf8')
    
    def raw(self, value): 
        return super(UnicodeSettingsResolver, self).set_value(value).encode('utf8')

class PathSettingsResolver(StrSettingsResolver):
    """ Resolver to proper return paths based on platform.
    
    On Unix "\\"-slashes are replaces by "/"-slashes. 
    
    On Windows  "/"-slashes are replaces by "\\"-slashes. 
    
    Formatting like `StrSettingsResolver` is supported.
    """
    
    resolve_types = ('path',)
    
    def __init__(self, settings, validate=None):
        super(StrSettingsResolver, self).__init__(settings, validate)
        self.choices = choices
    
    def get(self, value):
        """ Coerce ``value`` to proper path.
        
        :param value: The value to coerce
        :type value: ``str``
        :return: path as string, value replace is done, slashes are according to platform.
        :rtype: ``str``
        """
        value = super(PathSettingsResolver, self).get(value)
        
        if sys.platform == 'win32':
            value = value.replace('/', '\\') if '/' in value else value
        else:
            value = value.replace('\\', '/') if '\\' in value else value
        return value

class DirSettingsResolver(PathSettingsResolver):
    """ Resolver to proper return dir-paths based on platform.
    
    On Unix "\"-slashes are replaces by "/"-slashes. 
    
    On Windows  "/"-slashes are replaces by "\"-slashes. 
    
    Formatting like `StrSettingsResolver` is supported.
    
    Dir can be automatic create when the path is requested.
    
    :param create: Automatic create the dir if is doesn't exists. True is default.
    :type create: ``bool``
    """
    
    resolve_types = ('dir',)
    
    def __init__(self, settings, validate=None, create=True):
        super(DirSettingsResolver, self).__init__(settings, validate)
        self.create = create

    def get(self, value):
        """ Coerce `value` to proper path.
        
        If path does not exist and create is True the path is created.
        
        :param value: The value to coerce
        :type value: ``str``
        :return: path as string, value replace is done, slashes are according to platform.
        :rtype: ``str``
        """
        value = super(DirSettingsResolver, self).get(value)
        
        if self.create and not os.path.isdir(value):
            os.makedirs(value)
        return value
    
    @classmethod
    def _supports(self, key=None, default=None):
        return key.lower().endswith('dir')
                

class FileSettingsResolver(PathSettingsResolver):
    """ Resolver to proper return dir-paths based on platform.
    
    On Unix "\"-slashes are replaces by "/"-slashes. 
    
    On Windows  "/"-slashes are replaces by "\"-slashes. 
    
    Formatting like `StrSettingsResolver` is supported.
    
    File and dir of file can be automatic create when the path is requested.
    
    :param create: Automatic create the file if is doesn't exists. False is default.
    :param create_dir: Automatic create the dir in with the file lives if is doesn't exists. True is default.
    :param file_ext: Validate if a file has the correct extension. 
    :type create: ``bool``
    :type create_dir: ``bool``
    :type file_ext: ``str``
    """
    
    resolve_types = ('file',)
    
    def __init__(self, settings, validate=None, create=False, create_dir=True, file_ext=None):
        super(FileSettingsResolver, self).__init__(settings, validate)
        self.create = create
        self.create_dir = create_dir
        self.file_ext = file_ext
    
    def get(self, value):
        """ Coerce `value` to proper path.
        
        If file does not exist and create is True the file is created.
        If dir of file does not exist and create_dir is True the dir is created.
        
        :param value: The value to coerce
        :type value: `str`
        :return: path as string, value replace is done, slashes are according to platform.
        :rtype: `str`
        """
        value = super(FileSettingsResolver, self).get(value)
            
        if self.create and not os.path.isfile(value):
            open(value, 'a').close()
        if self.create_dir and not os.path.isdir(os.path.dirname(value)):
            os.makedirs(value)
        return value
    
    def _validate(self, value):
        if self.file_ext and not value.endswith(self.file_ext):
            return False
        return super(FileSettingsResolver, self)._validate(value)
    
    @classmethod
    def _supports(cls, key=None, default=None):
        return key.lower().endswith('file')

class SecretSettingsResolver(SettingsResolver):
    """ Resolver that encrypts value before storing it.
    
    Formatting like ``StrSettingsResolver`` is supported.
    
    .. warning::
        The default must already be encrypted, use SecretSettingsResolver.encrypte(key, value)
        to use the default implementation.
    
    This is a basic implementation. It is not 100% save.
    
    :param get_secret: Function to the key, takes must take 1 args, this is the resolver (self), 
            the default implentation returns settings.SECRET_KEY or raises ResolveException
    :param encode: Callable to override de default implementation. Must take 2 args, (key, encrypte_text) 
    :param decode: Callable to override de default implementation. Must take 2 args, (key, text) 
    :type get_secret: ``callable``
    :type encode: ``callable``
    :type decode: ``callable``
    """
    
    resolve_types = ('secret',)
    
    def __init__(self, settings, validate=None, get_secret=None, encode=None, decode=None):
        super(SecretSettingsResolver, self).__init__(settings, validate)
        self.get_secret = get_secret if get_secret is not None else self.get_secret
        self.encode = encode if encode is not None else self.encode
        self.decode = decode if decode is not None else self.decode
    
    def get(self, value):
        """ Return decrypted text."""
        dec = self.decrypte(self.get_secret(), value)
        return super(SecretSettingsResolver , self).get(dec)
    
    def raw(self, value):
        """ Return encrypted text."""
        return self.encrypte(self.get_secret(), value)
    
    def get_secret(self):
        """ Default implementation of `get_key` function.
        
        Default implementation return SECRET_KEY attribute of root settings
        """
        try:
            return self.settings.root.SECRET_KEY
        except AttributeError:
            raise ResolveException("SecretSettingsResolver : You must provide a get_key function or set SECRET_KEY on the root settings")
    
    @staticmethod
    def encrypte(key, clear):
        """ Default encrypt implementation.
        
        This implenentation is not 100% safe.
        
        :param key: Key returned by `get_secret`
        :param clear: Plaintext to encrypte.
        :type key: ``str``
        :type clear: ``str``
        :return: Return encrypted text, baseencoded.
        :rtype: ``str``
        """
        enc = []
        for i in range(len(clear)):
            key_c = key[i % len(key)]
            enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
            enc.append(enc_c)
        return base64.urlsafe_b64encode("".join(enc))
    
    @staticmethod
    def decrypte(key, enc):
        """ Default decrypt implementation.
        
        Only works with default encrypt implementation 
        
        :param key: Key returned by `get_secret`
        :param clear: Encrypted text to decrypte.
        :type key: ``str``
        :type clear: ``str``
        :return: Return encrypted text, baseencoded.
        :rtype: ``str``
        """
        dec = []
        enc = base64.urlsafe_b64decode(enc)
        for i in range(len(enc)):
            key_c = key[i % len(key)]
            dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
            dec.append(dec_c)
        return "".join(dec)

class PassSettingsResolver(SettingsResolver):
    """ Resolver returns a password object, use it to compare given password to stored password.
    
    .. warning::
        The default must already be hashed, use SecretSettingsResolver.hash(password, SecretSettingsResolver.salt())
        to use the default implementation.
    
    This resolver return a special object. It can be used to match plain passwords to 
    the hashed password sorted in the settings object.
    
    Example:
    
    .. code-block
        password = "some plain password"
        if settings.PASSWORD == password: # or settings.PASSWORD.equals(password)
            # do something special
            pass
    
    :param salt: Function to get the salt, or salt as `str`, this is passed to the hasher
    :param hasher: Callable to override de default implementation. Must take 2 args, (password, salt) 
    :type salt: ``callable``
    :type hasher: ``callable``
    """
    
    resolve_types = ('pass','password')
    
    class Password(object):
        def __init__(self, password, hasher, salt):
            self.password = password
            self.hasher = hasher
            self.salt = salt
        
        def equals(self, other):
            return self.password == self.hasher(other)
        
        def __eq__(self, other):
            return self.equals(other)
        
        def __str__(self):  
            return self.password
        
        def __repr__(self): 
            return '{name}({password})'.format(name=self.__name__, password=self.password)
    
    def __init__(self, settings, validate=None, salt=None, hasher=None):
        super(PassSettingsResolver, self).__init__(settings, validate)
        self.salt = salt if salt is not None else self.salt
        self.hash = hasher if hasher is not None else self.hash
    
    def get(self, value):
        """ Returns password object.
        
        :return: Special object to match plain text password
        :rtype: ``Password``
        """
        return self.Password(value, self.hash, self.salt)
    
    def raw(self, value):
        """ Hash the value if it is not a Password type.
        
        :return: The hashed value of `value`
        :rtype: ``str``
        """
        if isinstance(value , self.Password):
            return value.password
        return self.hash(value, self.salt(value))
    
    @staticmethod
    def hash(value, salt):
        """ Default hash implementation. 
        
        :param value: The value to hash.
        :param salt: A salt to use in the hash procces
        :type value: ``str``
        :type salt: ``str``
        :return: Return hashed password, (as hexdigest).
        :rtype: ``str``
        """
        if callable(salt):
            salt = salt(value)
        return hashlib.sha256('{}.{}'.format(value,salt)).hexdigest()
    
    @staticmethod
    def salt(value=None):
        """ Return the default salt ('default')
        
        :param value: The value that is going to be hashed..
        :type value: ``str``
        :return: The salt to use in the hash, this function returns `'default'`
        :rtype: ``str``
        """
        return 'default'
    
    @classmethod
    def _supports(self, key=None, default=None):
        return key.lower().endswith('password')

class TimeDeltaSettingsResolver(SettingsResolver):
    """ Resolver to coerce value to TimeDelta object.
    
    :param min: The minimum valid timedelta
    :param max: The maximum valid timedelta
    :type min: ``timedelta``
    :type max: ``timedelta``
    """
    resolve_types = ('timedelta', datetime.timedelta)
    
    def __init__(self, settings, validate=None, min=None, max=None):
        super(TimeDeltaSettingsResolver, self).__init__(settings, validate)
        self.min = min
        self.max = max

    def get(self, value):
        if isinstance(value, datetime.timedelta):
            return value
        return datetime.timedelta(seconds=int(value))
    
    def raw(self, value):
        return value.total_seconds()
    
    def _validate(self, value):
        if self.max is not None and value > self.max:
            return False
        if self.min is not None and value < self.min:
            return False
        return True

class DatetimeSettingsResolver(SettingsResolver):
    """ Resolver to coerce value to Datetime object.
    
    :param min: The minimum valid datetime
    :param max: The maximum valid datetime
    :type min: ``datetime``
    :type max: ``datetime``
    """
    
    resolve_types = ('datetime', datetime.datetime)
    format = "%Y-%m-%d %H:%M:%S"
    
    def __init__(self, settings, validate=None, min=None, max=None):
        super(DatetimeSettingsResolver, self).__init__(settings, validate)
        self.min = min
        self.max = max
    
    def get(self, value):
        if isinstance(value, datetime.datetime):    
            return value
        return datetime.datetime.strptime(value, self.format)
    
    def raw(self, value):
        return value.strftime(self.format)
    
    def _validate(self, value):
        if self.max is not None and value > self.max:
            return False
        if self.min is not None and value < self.min:
            return False
        return True

class TimeSettingsResolver(DatetimeSettingsResolver):
    """ Resolver to coerce value to Time objects.
    
    Take the same args as `DatetimeSettingsResolver` only
    with time objects.
    """
    resolve_types = ('time', datetime.time)
    format = "%H:%M:%S"
    
    def get(self, value):
        if isinstance(value, datetime.time):    
            return value
        return super(TimeSettingsResover, self).get(value).time()
    
class DateSettingsResolver(DatetimeSettingsResolver):
    """ Resolver to coerce value to Date objects.
    
    Take the same args as `DatetimeSettingsResolver` only
    with date objects.
    """
    resolve_types = ('date', datetime.date)
    format = "%Y-%m-%d"
    
    def get(self, value):
        if isinstance(value, datetime.time):    
            return value
        return super(DateSettingsResolver, self).get(value).date()

class MultiValueSettingsResolver(SettingsResolver):
    """ Baseclass for resolver handing type that can hold other """
    multivalue = True
    resolvers = False
    
    def has_childs(self):
        """ Checks if child resolvers are already set on a multivalue resolver
        
        :return: True or False based on if the childs resolvers are set on a resovler.
        :rtype: `bool`
        """
        return bool(self.resolvers)
    
    def set_childs(self, default):
        """ If the child resolvers are not set this function called with the default 
        value. The resolver can use this to set the correct child resolvers.
        
        :param default: The default value for this settings.
        """
        pass
    
class TupleSettingsResolver(MultiValueSettingsResolver):
    """ Resolver to coerce value to tulpe.
    
    We expect that the value in tuples are always in the same order
    and the same type. If childs was passed this is used to determine 
    what the type of the childs where, else we use the default value.
    
    example:
    
    .. code-block
        #if childs was passed
        childs = ['str', 'path', 'int')  --> TupleSettingsResolver(StrSettingsResolver, PathSettingsResolver, IntSettingsResolver)
    
        if childs is None:
            (1 , 'hello', u'test')  --> TupleSettingsResolver(IntSettingsResolver, StrSettingsResolver, UnicodeSettingsResolver)
    
    :param childs: A list of str type or `Resolver` used to determine what the childs types are.
    :type chidls: `list`
    """
    
    delimiter = ','
    resolve_types = ('tuple', tuple)
    
    def __init__(self, settings, validate=None, childs=None):
        super(TupleSettingsResolver, self).__init__(settings, validate)
        self.resolvers = []
        
        if childs:
            for r in childs:
                if isinstance(r, basesettings.Resolver):
                    resolver = settings._get_resolver(r.type, kwargs=r.resolverKwargs)
                else:
                    resolver = settings._get_resolver(r)
                self.resolvers.append(resolver)
        
    def get(self, value):
        """ Returns tuple using ' , ' to split string in tuple childs
        
        :return: Tulpe, all childs resolvers are applied to the childs
        :rtype: ``tuple``
        """
        if isinstance(value, basestring):
            value = value.split(self.delimiter)
        return tuple(self.resolvers[i].get(v) for i,v in enumerate(value))
    
    def raw(self, value):
        """ Coerce ``tuple`` to ``str``
        
        Childs are passed to there raw function and joined using a `,`.
        
        :return: Childs as str, joined with a `,`
        :rtype: ``str``
        """
        l = []
        for i,v in enumerate(value):
            l.append(self.resolvers[i].raw(v))
            if self.delimiter in l[i]:
                logger.warning("Delimiter in raw value, key : {key}, value : {value}".format(key=ReferenceResolverMixin.get_key(self), value=value))
        return self.delimiter.join(l)
    
    def _validate(self, value):
        if len(value) != len(self.resolvers):
            return False
        for i,v in enumerate(value):
            if not self.resolvers[i].validate(value):
                return False
        return True
    
    def set_childs(self, defaults):
        for i,d in enumerate(defaults):
            r = self.settings._get_resolver(d.__class__, None, d, kwargs={})
            if r.multivalue and not r.has_childs():
                r.set_childs(d)
            self.resolvers.append(r)

class NamedTupleSettingsResolver(TupleSettingsResolver):
    """ Same as TupleSettingsResolver, but takes a extra
    key parameter. This is passed to the namedtuple factory.
    
    :param key: ``list`` of names passed to ``namedtulpe`` factory.
    :type key: ``list``
    """
    
    resolve_types = ('namedtuple',)
    
    def __init__(self, settings, validate=None, keys=(), childs=()):
        super(NamedTupleSettingsResolver).__init__(settings, validate ,childs)
        self.cls = collections.namedtuple("NamedSettingsTulpe" , keys)
        
    def get(self, value):
        return self.cls(*super(NamedTupleSettingsResolver).get(value))

class ReferenceResolverMixin(object):
    """ Mixin for object that are mutable
    
    Provide a `get_key` function so the resolver can update the settingsvalue
    each time the mutable object changes.
    
    :return: The key this resolver is linked to
    :rtype: ``str``
    """
    def get_key(self):  
        for key, resolver in self.settings.resolvers.items():
            if self is resolver:
                return key
        
class ListSettingsResolver(MultiValueSettingsResolver, ReferenceResolverMixin):
    """ Resolver to coerce value to ``list``
    
    This resolver returns a special SyncList. This acts the same as a list,
    but syncs all changes back to the settingsobject. We expect that a list
    only contain the same type.
    
    Json is used to coerce the list to string format.
    
    :param child: string type or resolver to construct the resolver used for all childs
    :param duplicate: True of False allowing duplicate entries in the `list`
    :param options: A list withs contain all allowed values a entry in the list may be.
    :param sort: A function to sort the list. It is called after each change to the list
            and is called with the list as param
    :param minLen: the minimum length of the list
    :param maxLen: the maximum length of the list
    :type child: ``str`` or `Resolver`
    :type duplicate: ``bool``
    :type options: ``list``
    :type sort: ``callable``
    :type minLen: ``int``
    :type maxLen: ``int``
    """
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
    
    def __init__(self, settings, validate=None, child=None, duplicate=False, options = None, sort=None, minLen=None, maxLen=None):
        super(ListSettingsResolver, self).__init__(settings, validate)
        self.resolver = None
        self.resolvers = []
        self.duplicate = duplicate
        self.options = options
        self.minLen = minLen
        self.maxLen = maxLen
        self.sort = sort
        
        if child:
            if isinstance(child, basesettings.Resolver):
                self.resolver = settings._get_resolver(child.type, kwargs=child.resolverKwargs)
            else:
                self.resolver = settings._get_resolver(child)
            self.resolvers = (self.resolver,)
        
    def get(self, values):
        """ Returns the SyncList based on the list.
        
        :return: Special SyncList to sync back all changes to settings object.
        :rtype: ``SyncList``
        """
        key = self.get_key()
        if isinstance(values, self.SyncList):
            raise ResolveException("ListSettingsResolver : We are getting a synclist in the get function, this should not be possible")
        elif isinstance(values, list):
            values = values[:]
        else:
            values = self._get(values)
        return self.SyncList(key, values, self, self.settings)
    
    def _get(self, values):
        """ Internal function to coerce value to `list`"""
        l = []
        for val in json.loads(values):
            l.append(self.resolver.get(val))
        return l
    
    def raw(self, value):
        if isinstance(value, self.SyncList):
            value = value._l
        return self._raw(value)
    
    def _raw(self, values):
        """ Internal function to coerce list to `str`"""
        return json.dumps([self.resolver.raw(value) for value in values])
    
    def _validate(self, values):
        for value in values:
            if self.options and value not in self.options:
                return False

        if self.minLen and len(values) < self.minLen:
            return False
        
        if self.maxLen and len(values) > self.maxLen:
            return False
        
        if not self.duplicate and len(set(values)) != len(values):
            return False
        
        return super(StrSettingsResolver, self)._validate(value)
    
    def set_childs(self, defaults):
        if defaults:
            r = self.settings._get_resolver(defaults[0].__class__, {})
            if r.multivalue and not r.has_childs():
                r.set_childs(defaults[0])
            self.resolver = r
        else:
            self.resolver = StrSettingsResolver(self.settings)
        self.resolvers = (self.resolver,)
            
    
class DictSettingsResolver(MultiValueSettingsResolver, ReferenceResolverMixin):
    """ Resolver to load and dump dict.
    
    It not a good idea to use the dicts in your settings, you have sections so use them!!!
    
    ** Warning : dict are save and loaded by json not using resolvers so string formatting won't work **
    
    This resolver returns a dict like object (SyncDict) to sync back changes to the settings object.
    
    :param default: value to pass to ``dict.setdefault``.
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

    def __init__(self, settings, validate=None, default=None):
        super(DictSettingsResolver, self).__init__(settings, validate)
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
        """ Internal function to coerce json to `dict`"""
        return json.loads(value)
    
    def raw(self,value):
        if isinstance(value, self.SyncDict):
            value = value._d
        return self._raw(value)
    
    def _raw(self, value):
        """ Internal function to coerce dict to `str`"""
        return json.dumps(value)
    
    def _validate(self, value):
        return True

class SectionSettingsResolver(SettingsResolver, ReferenceResolverMixin):
    """ A special resolver used for Sections.
    
    This resolver makes sure subsection are correct supported.
    """
    resolve_types = (basesettings.Section,)
    
    def __init__(self , settings, validate=None):
        super(SectionSettingsResolver, self).__init__(settings, validate)
    
    def get(self, value):
        key = self.get_key()
        if isinstance(value, basesettings.Section):
            # the default is passed 
            section = value
        else:
            section = self.settings.defaults[key.lower()]
        
        # try to get the userconfig of this section, if it does not exist we create it.
        userconfig = self.settings.userconfig[key.lower()]
        
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
        
        return section(self.settings, options, userconfig, nosave, envconfig, fileconfigs)
    
    def raw(self, value): 
        raise ResolveException("It is not possible to set a section")
    
    @classmethod
    def _supports(cls, key=None, default=None):
        return issubclass(default, basesettings.Section)

# register all resolvers with base settings cls
basesettings.add_resolver_type(SettingsResolver)
basesettings.add_resolver_type(IntSettingsResolver)
basesettings.add_resolver_type(FloatSettingsResolver)
basesettings.add_resolver_type(BoolSettingsResolver)
basesettings.add_resolver_type(StrSettingsResolver)
basesettings.add_resolver_type(UnicodeSettingsResolver)
basesettings.add_resolver_type(PathSettingsResolver)
basesettings.add_resolver_type(DirSettingsResolver)
basesettings.add_resolver_type(FileSettingsResolver)
basesettings.add_resolver_type(SecretSettingsResolver)
basesettings.add_resolver_type(PassSettingsResolver)
basesettings.add_resolver_type(DatetimeSettingsResolver)
basesettings.add_resolver_type(TimeSettingsResolver)
basesettings.add_resolver_type(DateSettingsResolver)
basesettings.add_resolver_type(TupleSettingsResolver)
basesettings.add_resolver_type(NamedTupleSettingsResolver)
basesettings.add_resolver_type(ListSettingsResolver)
basesettings.add_resolver_type(DictSettingsResolver)
basesettings.add_resolver_type(SectionSettingsResolver)
