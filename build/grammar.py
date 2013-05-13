#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, re, plistlib, json, traceback

def iter_tree_dicts(tree, initpath = u''):
    stack = []
    stack.append((initpath, tree))
    while stack:
        (path, obj) = stack.pop()
        if isinstance(obj, list):
            for i in xrange(0, len(obj)):
                np = u'[%d]' % i
                stack.append((path + np, obj[i]))
        elif isinstance(obj, dict):
            yield (path, obj)
            for (k, v) in obj.iteritems():
                np = u'/' + k
                stack.append((path + np, v))

class CompilerError(ValueError):
    pass

class TokenReplacement:
    @classmethod
    def run(cls, grammar):
        if u'tokens' in grammar:
            instance = cls(grammar[u'tokens'])
            result = instance.in_grammar(grammar)
            instance.print_counts()
            del grammar[u'tokens']
            return result
        else:
            print 'No "tokens" in grammar.'
            return grammar

    def __init__(self, token_dict):
        self.token_dict = token_dict
        self.replace_counts = {}
        for k in token_dict: self.replace_counts[k] = 0

    def in_string(self, value, path):
        def replacement(match):
            name = match.group(1)
            if name in self.token_dict:
                self.replace_counts[name] += 1
                return u'(?:' + self.token_dict[name] + u')'
            else:
                msg = u'Reference to undefined token: "%s" at %s' % (name, path)
                raise CompilerError, msg

        return re.sub(u'⟪([^⟫]*)⟫', replacement, value)

    def in_tree(self, tree, initpath):
        for (path, node) in iter_tree_dicts(tree, initpath):
            for (k, v) in node.iteritems():
                if k in [u'begin', u'end', u'match']:
                    itempath = path + u'/' + k
                    node[k] = self.in_string(v, itempath)

    def in_grammar(self, grammar):
        self.in_tree(grammar.get(u'patterns', []), u'/patterns')
        for (name, r_item) in grammar.get(u'repository', {}).iteritems():
            self.in_tree(r_item, u'/repository/' + name)

    def print_counts(self):
        for (t,n) in self.replace_counts.iteritems():
            print 'Replaced %d occurrences of %s.' % (n,t)

class IncludeCheck:
    @classmethod
    def run(cls, grammar):
        cls(grammar).check_includes()
        return grammar

    def __init__(self, grammar):
        self.grammar = grammar
        self.repository = grammar.get(u'repository', {})
        self.grammar_includes = set()
        self.repo_includes = dict([(k, set()) for k in self.repository])

    def check_includes(self):
        patterns = self.grammar.get(u'patterns', [])
        for (path, node) in iter_tree_dicts(patterns, u'/patterns'):
            if u'include' in node:
                self.add_include(node[u'include'], self.grammar_includes, path)
        for (name, item) in self.repository.iteritems():
            for (path, node) in iter_tree_dicts(item, u'/repository/' + name):
                if u'include' in node:
                    incset = self.repo_includes[name]
                    self.add_include(node[u'include'], incset, path)
        self.print_unused()

    def add_include(self, name, set, path):
        if name.startswith('#'):
            item = name[1:]
            if item in self.repository:
                set.add(item)
            else:
                msg = u'Undefined repository item "%s" at %s' % (item, path)
                raise CompilerError, msg

    def print_unused(self):
        for item in self.unused_items():
            print u'Repository item "%s" is not used.' % item

    def unused_items(self):
        used = set()
        for item in self.grammar_includes:
            used |= self.usage_closure(item, used)
        return set(self.repository) - used

    def usage_closure(self, item, closure = set()):
        if item not in closure:
            closure.add(item)
            for used_item in self.repo_includes[item]:
                closure |= self.usage_closure(used_item, closure)
        return closure

PASSES = [TokenReplacement, IncludeCheck]

def xml_filename(json_file):
    path, fname = os.path.split(json_file)
    fbase, old_ext = os.path.splitext(fname)
    return os.path.join(path, fbase + '.tmLanguage')

def build(json_file):
    grammar = None
    try:
        with open(json_file) as json_content:
            grammar = json.load(json_content)
    except ValueError, e:
        print "Error parsing JSON in %s:\n  %s" % (json_file, e)
    else:
        for op in PASSES:
            try:
                op.run(grammar)
            except CompilerError, e:
                print u'Error during %s:\n  %s' % (op.__name__, e)
                return None
            except Exception:
                traceback.print_exc()
                return None

        plistlib.writePlist(grammar, xml_filename(json_file))

if __name__ == '__main__':
    build(sys.argv[1])