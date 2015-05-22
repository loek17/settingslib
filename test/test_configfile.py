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

import cStringIO as StringIO

from . import basetest

from settingslib.configfile import ConfigFile

class ConfigFileTestCase(basetest.BaseTestCase):
    def test_cmp(self):
        cfg1 = ConfigFile()
        cfg1['level1'] = "new val"
        cfg2 = ConfigFile()
        cfg2['level1'] = "new val"
        self.assertEqual(cfg1, cfg2)
        cfg2['level1'] = "another val"
        self.assertNotEqual(cfg1, cfg2)

    def test_get_item(self):
        self.assertEqual(ConfigFile(), ConfigFile())
        cfg = ConfigFile()
        self.assertEqual(cfg['level1'], ConfigFile())

    def test_set_item(self):
        cfg = ConfigFile()
        cfg['level1'] = "new val"
        self.assertEqual(cfg['level1'], "new val")

    def test_set_item_2deep(self):
        cfg = ConfigFile()
        cfg['level1']['level2'] = "new val"
        self.assertEqual(cfg['level1']['level2'], "new val")

    def test_set_attr(self):
        cfg = ConfigFile()
        cfg.level1 = "new val"
        self.assertEqual(cfg.level1, "new val")

    def test_set_attr_2deep(self):
        cfg = ConfigFile()
        cfg.level1.level2 = "new val"
        self.assertEqual(cfg.level1.level2, "new val")
        
    def test_write(self):
        fp = StringIO.StringIO()
        cfg = ConfigFile()
        cfg.level1 = "new val"
        cfg.set_help("level1", "a comment")
        cfg.section1.set_help(None, "a section comment")
        cfg.section1.item1 = "item 1"
        cfg.section1.set_help("item1", "a comment for item1")
        cfg.section1.subsection.item2 = "item 2"
        cfg.section2.subsection.item3 = "item 3"
        cfg.section3.elses = "elses"
        cfg.section3.set_help(None, 'a section comment')
        cfg['empty section1'] = ConfigFile()
        cfg['very last'] = "7"
        cfg.write(fp)
        fp.seek(0,0)
        lines = [
            '# a comment\n',
            'level1 = new val\n',
            '\n',
            'section1:\n',
            '    #####################\n',
            '    # a section comment #\n',
            '    #####################\n',
            '    # a comment for item1\n',
            '    item1 = item 1\n',
            '    \n',
            '    subsection:\n',
            '        item2 = item 2\n',
            '\n',
            
            'section2:\n',
            '    \n',
            '    subsection:\n',
            '        item3 = item 3\n',
            '\n',
            'section3:\n',
            '    #####################\n',
            '    # a section comment #\n',
            '    #####################\n',
            '    elses = elses\n',
            '\n',
            'empty section1:\n',
            'very last = 7\n'
        ]
        for i, line in enumerate(fp):
            self.assertEqual(line, lines[i])

    def test_read(self):
        fp = StringIO.StringIO(''.join([
            'empty section1:\n',
            'level1 = new val\n',
            'section1:\n',
            '    #####################\n',
            '    # a section comment #\n',
            '    #####################\n',
            '# this is a comment for section1.item1:\n',
            '    item1 = item 1\n',
            '          # this is another comment\n',
            '    subsection:\n',
            '        item2 = item 2\n',
            'section2:\n',
            '    subsection:\n',
            '        item3 = item 3\n',
            'very last = 7\n'
        ]))
        cfg = ConfigFile()
        cfg.read(fp)
        self.assertEqual(cfg.keys(),
                        ['empty section1', 'level1',
                         'section1', 'section2', 'very last'])
        self.assertEqual(cfg.section1.keys(),
                         ['item1', 'subsection'])
        self.assertEqual(cfg['empty section1'], ConfigFile())
        self.assertEqual(cfg.level1, "new val")
        self.assertEqual(cfg.section1.item1, "item 1")
        self.assertEqual(cfg.section1.subsection.item2, "item 2")
        self.assertEqual(cfg.section2.subsection.item3, "item 3")
        self.assertEqual(cfg['very last'], "7")
        self.assertEqual(cfg.section1.help(), "a section comment")
        self.assertEqual(cfg.section1.help("item1"), "this is a comment for section1.item1:")

    def test_varying_indents(self):
        fp = StringIO.StringIO(''.join([
            'empty section1:\n',
            'level1 = new val\n',
            'section1:\n',
            '	item1 = item 1\n',
            '	subsection:\n',
            '	    item2 = item 2\n',
            'section2:\n',
            ' subsection:\n',
            ' 	item3 = item 3\n',
            'very last = 7\n'
        ]))
        cfg = ConfigFile()
        cfg.read(fp)
        self.assertEqual(cfg.keys(),
                        ['empty section1', 'level1',
                         'section1', 'section2', 'very last'])
        self.assertEqual(cfg.section1.keys(),
                         ['item1', 'subsection'])
        self.assertEqual(cfg['empty section1'], ConfigFile())
        self.assertEqual(cfg.level1, "new val")
        self.assertEqual(cfg.section1.item1, "item 1")
        self.assertEqual(cfg.section1.subsection.item2, "item 2")
        self.assertEqual(cfg.section2.subsection.item3, "item 3")
        self.assertEqual(cfg['very last'], "7")