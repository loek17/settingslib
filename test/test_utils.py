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

# system imports
import tempfile
import os

from . import basetest

from settingslib.basesettings import BaseSettings, Section, Option
import settingslib.configfile as configfile
import settingslib.utils as utils

class BaseSettingsTestCase(basetest.BaseTestCase):
    
    def test_create_config_file(self):
        class Settings(BaseSettings):
            " this is a comment for the root config file"
            class SOMETHING(Option):
                "this is a settings for SOMETHING"
                default = 1
            class SECTION(Section):
                " subsection is someting"
                SOMEELSE = 'str'
                class SECSECTION(Section):
                    "comment"
        
        settings = Settings()
        file = os.path.join(os.path.dirname(__file__) , 'testfile.conf')
        utils.create_config_file(file, settings)
        lines = [
            '###############################################\n',
            '#  this is a comment for the root config file #\n',
            '###############################################\n',
            '\n',
            'section:\n',
            '    ###########################\n',
            '    #  subsection is someting #\n',
            '    ###########################\n',
            '    #someelse = str\n',
            '    \n',
            '    secsection:\n',
            '        ###########\n',
            '        # comment #\n',
            '        ###########\n',
            '# this is a settings for SOMETHING\n',
            '#something = 1\n'
        ]
        with open(file, 'r') as fd:
            for i, line in enumerate(fd):
                self.assertEqual(line, lines[i])