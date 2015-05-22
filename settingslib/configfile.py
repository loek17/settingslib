#!/usr/bin/env python
"""
An alternative config file parser written in response to the ConfigParser
shootout: http://wiki.python.org/moin/ConfigParserShootout
Author: Skip Montanaro (skip@pobox.com)
Significant points:
    * File format is indentation-based (where'd he get that idea???)
    * Both attribute-style and dictionary-style access supported
    * File format is *not* compatible with Windows INI file
      - section introduced by line ending with colon (another brilliant
      coup!)
      - values are specified by simple key = value lines
    * Nesting to arbitrary depths is supported
    * Read and write with round trip, though comments are not currently
    preserved.
    * Proof-of-concept only - there's not much of an api yet - no
    sections(), has_section(), as_dict() methods, etc.  That should be easy
    enough to add later.
    * Typeless - everything's a string.  Python has plenty of ways to
    convert strings to other types of objects.

Edited to allow the passing and writing of comments (Loek17)

"""

import cStringIO as StringIO
import re

class ConfigFile(object):
    def __init__(self, autogrown=True , help=None):
        self.__dict__['_ConfigFile__values'] = []
        self.__dict__['_ConfigFile__sections'] = []
        self.__dict__['_ConfigFile__comments'] = {}
        self.__dict__['_ConfigFile__section_comment'] = help if help is not None else []
        self.__dict__['_ConfigFile__autogrown'] = autogrown

    def __cmp__(self, other):
        v1 = self.__values[:]
        v1.sort()
        v2 = self.__values[:]
        v2.sort()
        result = cmp(v1, v2)
        if result:
            return result
        for attr in v1:
            result = cmp(self[attr], other[attr])
            if result:
                return result
        return 0

    def __eq__(self, other):
        if isinstance(other, ConfigFile):
            return self.__cmp__(other) == 0
        return False

    def __getitem__(self, key):
        if key in self.__values:
            return self.__dict__[key]
        if self.__autogrown:
            self.__dict__[key] = ConfigFile()
            self.__values.append(key)
            return self.__dict__[key]
        raise KeyError, "Key does not exits, key : {key}".format(key=key)
    __getattr__ = __getitem__

    def __setitem__(self, key, val):
        self.__dict__[key] = val
        if key not in self.__values:
            self.__values.append(key)
    __setattr__ = __setitem__
    
    def keys(self):
        return self.__values
    
    def values(self):
        return [self[key] for key in self.__values]
    
    def items(self):
        return [(key, self[key]) for key in self.__values]
    
    def sections(self):
        return [section for section in self.__values if isinstance(self[section], ConfigFile)]
    
    def help(self, key=None):
        if key is None:
            return "\n".join(self.__section_comment)
        elif key in self.__values:
            return "\n".join(self.__comments[key]) if key in self.__comments else ""
        else:   
            return self[key].help()
    
    def set_help(self, key=None, message=None):
        if message is None:
            return
        if isinstance(message, basestring):
            message = message.split('\n')
        if key is None: 
            self.__section_comment.extend(message)
        elif key in self.__values:
            self.__comments[key] = message
        else:
            self[key].set_help(None, message)
    
    def write(self, fp):
        if self.__section_comment:
            lengte = 5 # min lengte
            for line in self.__section_comment:
                if lengte < len(line.strip()):
                    lengte = len(line)
            lengte += 4
            fp.write("{}\n".format("#"*lengte))
            for line in self.__section_comment:
                fp.write("# {} #\n".format(line.ljust(lengte-4)))
            fp.write("{}\n".format("#"*lengte))
            
        for attr in self.__values:
            item = self[attr]
            if isinstance(item, ConfigFile):
                subfp = StringIO.StringIO()
                item.write(subfp)
                fp.write('\n')
                fp.write("%s:\n" % attr)
                subfp.seek(0)
                section_open = False
                for line in subfp:
                    fp.write(" "*4)
                    fp.write(line)
            else:
                if attr in self.__comments:
                    for line in self.__comments[attr]:
                        fp.write("# %s\n" % line)
                fp.write("%s = %s\n" % (attr, item))

    def read(self, fp):
        for v in self.__values:
            delattr(self, v)
            
        self.read_helper(PushBackFile(fp), "")

    def read_helper(self, fp, indent):
        #print ">", id(self)
        section_comment_open = False
        key = None
        section_comment = []
        comments = []
        
        for line in fp:
            mat = re.match(r'([ \t]*)(.*)$', line)
            left, right = mat.groups()
            
            if not right:
                # empty line, we skip it
                continue
            elif right.startswith("#"):
                # comments
                if right.startswith("#"*5):
                    # open the section comment with minimal 5 times #
                    section_comment_open = not section_comment_open
                elif section_comment_open:
                    # we are in section comment, add it to section_comment
                    self.__section_comment.append(right[1:].strip(' #'))
                else:
                    # normal comment, add it to comment list and add it to the next key
                    comments.append(right.strip(' #'))
            elif len(left) < len(indent):
                # indent is smaller the the passed indent, section ended, returning
                # push the line back to the "file"
                fp.push(line)
                #print "<", id(self), "extinging indent", len(left), "line", line
                return
            
            elif len(left) > len(indent):
                # multi line values, append them to the last key
                if not key:
                    raise ValueError, "Extra indent, but no lastkey, line %d" % fp.lineno
                self[key.strip()] += " %s" % right
                # add extra fond comments to the comments list of the current key
                if comments:
                    self.__comments[key.strip()] += comments
                    comments = []
            elif right[-1:] == ':':
                # new section
                section = right[:-1].strip()
                if not section:
                    raise ValueError, "Empty section, line %d" % fp.lineno
                cfg = self[section] = ConfigFile()
                # reset the comments
                comments = []
                # get the next line (with text) add push is back directly
                while True:
                    newline = fp.next(stack=False)
                    fp.push(newline)
                    if newline.strip() and not newline.strip().startswith("#"):
                        break
                if newline:
                    mat = re.match(r'([ \t]*)', newline)
                    # if indent is bigger read the new subsection
                    if len(mat.group(0)) > len(indent):
                        cfg.read_helper(fp, mat.group(0))
            else:
                # a key value combination
                #print "adding key, value : ", right
                if '=' in right:
                    key, val = right.split('=', 1)
                    if "#" in val:
                        # if there is a comment behind the value we also add it to commentlist
                        val, extra_comment = right.split('#', 1)
                        comments.append(extra_comment)
                else:
                    # empty value
                    key, val = right, ""
                self[key.strip()] = val.strip()
                # if there where comments in front of the key add them
                # reset the comment list after we fond a new key
                #print "adding comments to ", key, "comments : ", comments
                self.__comments[key.strip()] = comments
                comments = []

    def __str__(self):
        return "<ConfigFile @ 0x%x>" % id(self)
    __repr__ = __str__

class PushBackFile(object):
    def __init__(self, fp):
        self.fp = fp
        self.stack = []
        self.lineno = 0

    def __iter__(self):
        return self

    def next(self, stack=True):
        #while True:
        if self.stack and stack:
            line = self.stack.pop()
        else:
            line = self.fp.next()
            #if line.strip()[:1] != "#":
            #    break
        self.lineno += 1
        line = self.untab(line.rstrip())
        #print "+", line
        return line

    def push(self, line):
        if line:
            self.lineno -= 1
        #print "-", line.rstrip()
        self.stack.insert(0,line)

    def untab(self, line):
        "expand tabs in leading whitespace to spaces"
        newline = []
        line = list(line)
        while line:
            c = line[0]
            del line[0]
            if c == " ":
                newline.append(" ")
            elif c == "\t":
                newline.append(" ")
                while len(newline) % 4:
                    newline.append(" ")
            else:
                newline.append(c)
                newline.extend(line)
                line = []
        return "".join(newline)