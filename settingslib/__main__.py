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

import sys
import argparse

from . import utils

def main(args = None):

    parser = argparse.ArgumentParser(
                        description='Create a configfile from a settings module in a package.'
                    )
    
    parser.add_argument(
                        'module', 
                        help='The module to use to create the configfile, must be importeble with __import__, example package.settings'
                    )
    
    parser.add_argument(
                        'configfile', 
                        type=argparse.FileType('r'),
                        default=sys.stdout,
                        help='The file to write is to.'
                    )
    
    parser.add_argument(
                        '--nodisable', 
                        action='store_false',
                        dest='disable',
                        help="Don't prefix all settings with a '#'"
                    )

    
    args = parser.parse_args(args)
    
    settings = __import__(args.module)
    utils.create_config_file(args.configfile, settings, args.disable)
        
    
if __name__ == "__main__":
    main()