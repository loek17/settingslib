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

from . import basetest

from settingslib.basesettings import BaseSettings, Section, Option, Resolver
import settingslib.configfile as configfile

class BaseSettingsTestCase(basetest.BaseTestCase):
    def test_default(self):
        class Settings(BaseSettings):
            SOMETHING = 1
            SOME = Option(1, 'int')
            SOMETHING3 = Option("3", 'int')
            SOMESTR = Option(1, Resolver('str', **{}))
            class SUBSECTION(Section):
                SOM = 1
                SOM3 = 1
            
        settings = Settings()
        self.assertEqual(settings.SOMETHING, 1)
        self.assertEqual(settings.SOMETHING3, 3)
        self.assertEqual(settings.SOME, 1)
        self.assertEqual(settings.SOMESTR, "1")
        self.assertEqual(settings.SUBSECTION.SOM, 1)
        self.assertEqual(settings.SUBSECTION.SOM3, 1)
        
    def test_options(self):
        class Settings(BaseSettings):
            SOMETHING = 1
            SOMETHING3 = 3
            SOME = Option(1, 'int')
            SOMESTR = Option(1, Resolver('str', **{}))
            class SUBSECTION(Section):
                SOM = 1
                SOM3 = 1
            
        settings = Settings()
        settings.set_options({"SOMETHING3": 4, "subsection.som3":3, "some" : 3})
        self.assertEqual(settings.SOMETHING3, 4)
        self.assertEqual(settings.SOME, 3)
        self.assertEqual(settings.SUBSECTION.SOM3, 3)
        self.assertEqual(settings.SUBSECTION.SOM, 1)
        
    def test_userconfig(self):
        class Settings(BaseSettings):
            SOMETHING = 1
            SOMETHING3 = 3
            SOME = Option(1, 'int')
            SOMESTR = Option(1, Resolver('str', **{}))
            class SUBSECTION(Section):
                SOM = 1
                SOM3 = 1
            
        settings = Settings()
        config = configfile.ConfigFile()
        config["some"] = "3"
        settings.__dict__['userconfig'] = config
        settings.SOMETHING = 4
        settings.SUBSECTION.SOM = 5
        self.assertEqual(settings.SOME, 3)
        self.assertEqual(config["something"], "4")
        self.assertEqual(settings.SOMETHING, 4)
        self.assertEqual(config["subsection"]['som'], "5")
        self.assertEqual(settings.SUBSECTION.SOM, 5)
        
    def test_classoptions(self):
        class Settings(BaseSettings):
            class SOMETHING(Option):
                "hello I am some help message"
                default = 1
                resolver = ('int', {})
                save = False
        
        settings = Settings()
        self.assertEqual(settings.SOMETHING, 1)
        self.assertEqual(settings.extraOptions['something']['__doc__'], "hello I am some help message")
    