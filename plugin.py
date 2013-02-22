import sublime
import sublime_plugin

if (sublime.version() != '') and (sublime.version() < '3000'):
    pass
else:
    from .st3 import ErlangCommandHooks
