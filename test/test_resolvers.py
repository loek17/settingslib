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

from settingslib.basesettings import BaseSettings , Section, Option, Resolver
import settingslib.basesettings as basesettings
import settingslib.resolvers as resolvers

class ResolverTestCase(basetest.BaseTestCase):
    
    def test_strresolver(self):
        class Settings(BaseSettings):
            STR = "bye"
            STR2 = "world"
            STR3 = "{STR} {STR2}"
            STR4 = "something"
        
        settings = Settings()
        self.assertEqual(settings.STR, "bye")
        self.assertEqual(settings.STR3, "bye world")
        
        settings.STR = "hello"
        self.assertEqual(settings.STR, "hello")
        self.assertEqual(settings.STR3, "hello world")
        self.assertEqual(settings.userconfig["str"], "hello")
        
        settings.STR4 = "{STR3} again"
        self.assertEqual(settings.STR4, "hello world again")
        self.assertEqual(settings.userconfig["str4"], "{STR3} again")
        
    def test_intresolver(self):
        class Settings(BaseSettings):
            INT = 1
        
        settings = Settings()
        self.assertEqual(settings.INT, 1)
        
        settings.INT = 2
        self.assertEqual(settings.INT, 2)
        self.assertEqual(settings.userconfig["int"], "2")
    
    def test_boolresolver(self):
        class Settings(BaseSettings):
            BOOL = True
        
        settings = Settings()
        self.assertEqual(settings.BOOL, True)
        
        settings.BOOL = False
        self.assertEqual(settings.BOOL, False)
        self.assertEqual(settings.userconfig["bool"], "False")
        
        settings.BOOL = True
        self.assertEqual(settings.BOOL, True)
        self.assertEqual(settings.userconfig["bool"], "True")
        
        settings.BOOL = 'no'
        self.assertEqual(settings.BOOL, False)
        self.assertEqual(settings.userconfig["bool"], "no")
        
        settings.BOOL = 'yes'
        self.assertEqual(settings.BOOL, True)
        self.assertEqual(settings.userconfig["bool"], "yes")
        
        def assertExcept():
            settings.BOOL = 'junk'
        self.assertRaises(basesettings.SettingsException, assertExcept)
    
    def test_tupleresolver(self):
        class Settings(BaseSettings):
            ONE = 1
            TO = 'to'
            SOMETHING = Option(('{ONE} , {TO}', 5), Resolver('tuple', childs=['str','int',]))
        
        settings = Settings()
        self.assertEqual(settings.SOMETHING[0], '1 , to')
        self.assertEqual(settings.SOMETHING[1], 5)
        
        settings.SOMETHING = ('somestring', '1')
        self.assertEqual(settings.SOMETHING[0], 'somestring')
        self.assertEqual(settings.SOMETHING[1], 1)
        self.assertEqual(settings.userconfig["something"], 'somestring , 1')
    
    def test_listresolver(self):
        class Settings(BaseSettings):
            SOMETHING = []
            SOMEINTLIST = [1]
            SOMESTRLIST = ['ss']
            SOMESTRTULPE = [('dd',1)]
                
        settings=Settings()
        settings.SOMETHING.append("gggg")
        self.assertEqual(settings.SOMETHING._l, ["gggg"])
        self.assertEqual(settings.userconfig["something"], '["gggg"]')
        settings.SOMETHING.append("hhh")
        self.assertEqual(settings.SOMETHING._l, ["gggg", "hhh"])
        self.assertEqual(settings.userconfig["something"], '["gggg", "hhh"]')
        
        self.assertEqual(settings.SOMEINTLIST._l, [1])
        settings.SOMEINTLIST.append("2")
        self.assertEqual(settings.SOMEINTLIST._l, [1,2])
        self.assertEqual(settings.userconfig["someintlist"], '["1", "2"]')
        
        self.assertEqual(settings.SOMESTRTULPE._l, [('dd',1)])
        settings.SOMESTRTULPE.append(("2", "3"))
        self.assertEqual(settings.SOMESTRTULPE._l, [('dd',1),('2',3)])
        self.assertEqual(settings.userconfig["somestrtulpe"], '["dd , 1", "2 , 3"]')
    
    def test_dictresolver(self):
        class Settings(BaseSettings):
            SOMETHING = {"gggg" : "bye"}
                
        settings=Settings()
        self.assertEqual(settings.SOMETHING["gggg"], "bye")
        settings.SOMETHING["gggg"] = "hello"
        self.assertEqual(settings.SOMETHING["gggg"], "hello")
        self.assertEqual(settings.userconfig["something"], '{"gggg": "hello"}')
        settings.SOMETHING["ff"] = 'ss'
        self.assertEqual(settings.SOMETHING["ff"], "ss")
        self.assertEqual(settings.userconfig["something"], '{"gggg": "hello", "ff": "ss"}')
    
    def test_sectionresolver(self):
        class Settings(BaseSettings):
            class SUBSECTION(Section):
                HELLO = 'string'
                HEY = Option('str', Resolver('str', **{}))
                HEY2 = Option('1', 'int')
        
        settings=Settings()
        self.assertEqual(settings.SUBSECTION.HELLO, 'string')
        self.assertEqual(settings.SUBSECTION.HEY, 'str')
        self.assertEqual(settings.SUBSECTION.HEY2, 1)
        
        settings.SUBSECTION.HELLO = 'hello'
        self.assertEqual(settings.SUBSECTION.HELLO, 'hello')