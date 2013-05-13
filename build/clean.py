#!/usr/bin/env python

import grammar, os, os.path, glob, sys

if len(sys.argv) > 1:
    dir = sys.argv[1]
else:
    dir = os.getcwd()

os.chdir(dir)

for f in glob.glob('*.JSON-tmLanguage'):
    xml = grammar.xml_filename(f)
    if os.path.exists(xml):
        print 'Deleting ' + xml
        os.remove(xml)
