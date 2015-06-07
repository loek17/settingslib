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
import re
import cStringIO as StringIO

from . import configfile
from . import basesettings

logger = logging.getLogger(__name__)

def create_config_file(file, settings, disable=True):
    config = create_config_object(settings)
    with open(file, 'w') as fd:
        tmpfd = StringIO.StringIO()
        config.write(tmpfd)
        tmpfd.seek(0,0)
        for line in tmpfd:
            mat = re.match(r'([ \t]*)(.*)$', line)
            left, right = mat.groups()
            if disable and line.strip() and not line.split('#')[0].strip().endswith(':') and not right.startswith('#'):
                line = "{space}#{setting}\n".format(space=left,setting=right)
            fd.write(line)

def create_config_object(settings):
    config = configfile.ConfigFile()
    config.set_help(None, settings.__doc__)
    for key, value in settings.defaults.items():
        if isinstance(value, type):
            config[key] = create_config_object(settings.resolvers[key].get(value))
        else:
            config[key] = settings.resolvers[key].raw(value)
            if key in settings.help_dict:
                config.set_help(key, settings.help_dict[key])
    
    return config
            


