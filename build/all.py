#!/usr/bin/env python

import grammar, os, os.path, glob, sys

def must_build(source, target):
	return (not os.path.exists(target)) \
		or (os.path.getmtime(source) >= os.path.getmtime(target))

if len(sys.argv) > 1:
    dir = sys.argv[1]
else:
    dir = os.getcwd()

os.chdir(dir)

for source in glob.glob('*.JSON-tmLanguage'):
	target = grammar.xml_filename(source)
	if must_build(source, target):
		print 'Building %s' % target
		grammar.build(source)
	else:
		print '%s is up to date.' % target
