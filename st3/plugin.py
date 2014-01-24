import sublime, sublime_plugin
import Default.symbol
import re, os.path

# ------------------------------------------------------------------------------
# -- Generic Command Hooks
TEXT_CMD_HOOKS = {}
WINDOW_CMD_HOOKS = {}

def hook_text_command(command_name, selector):
    def decorate(func):
        TEXT_CMD_HOOKS[command_name] = (selector, func)
        return func
    return decorate

def hook_window_command(command_name, selector):
    def decorate(func):
        WINDOW_CMD_HOOKS[command_name] = (selector, func)
        return func
    return decorate

class ErlangCommandHooks(sublime_plugin.EventListener):
    def on_text_command(self, view, name, args):
        if args is None:
            args = {}
        if name in TEXT_CMD_HOOKS:
            (selector, hook) = TEXT_CMD_HOOKS[name]
            if self.is_enabled(view, selector):
                return hook(view, **args)

    def on_window_command(self, window, name, args):
        if args is None:
            args = {}
        if name in WINDOW_CMD_HOOKS:
            (selector, hook) = WINDOW_CMD_HOOKS[name]
            if self.is_enabled(window.active_view(), selector):
                return hook(window, **args)

    def is_enabled(self, view, selector):
        if view:
            p = view.sel()[0].begin()
            s = view.score_selector(p, selector)
            return s > 0

# ------------------------------------------------------------------------------
# -- Goto Definition
PREFIX_MAP = [
    ('Function',  'meta.function.erlang'),
    ('Function',  'meta.function.module.erlang'),
    ('Function',  'entity.name.function.erlang'),
    ('Function',  'entity.name.function.definition.erlang'),
    ('Type',      'storage.type.erlang'),
    ('Type',      'storage.type.module.erlang'),
    ('Type',      'storage.type.definition.erlang'),
    ('Record',    'storage.type.record.erlang'),
    ('Record',    'storage.type.record.definition.erlang'),
    ('Macro',     'keyword.other.macro.erlang'),
    ('Module',    'entity.name.type.class.module.erlang'),
    ('Yecc Rule', 'entity.name.token.unquoted.yecc'),
    ('Yecc Rule', 'entity.name.token.quoted.yecc')
]

ERLANG_EXTENSIONS = ['.erl', '.hrl', '.xrl', '.yrl']

class GotoExactDefinition:
    def __init__(self, view):
        # GotoDefinition could change at any time, but I don't feel like
        # writing all of its code again just for the sake of being future-proof
        self.view = view
        self.window = view.window()
        self.goto = Default.symbol.GotoDefinition(self.window)

    def at_position(self, kind, point):
        (module, funcname, is_local) = self.get_module_in_call(point)
        matches = self.goto.lookup_symbol(kind + ': ' + funcname)
        locations = [loc for loc in matches if self.loc_is_module(loc, module)]

        if len(locations) == 0:
            sublime.status_message("No matches for %s %s:%s" %
                                   (kind.lower(), module, funcname))
            if is_local: return
            # try to find the module if nothing matched
            mod_matches = self.goto.lookup_symbol('Module: ' + module)
            if len(mod_matches) == 0:
                if len(matches) == 0:
                    sublime.status_message("No matches for %s %s" %
                                           (kind.lower(), funcname))
                else:
                    self.goto_panel(matches) # open panel with inexact matches
            elif len(mod_matches) == 1:
                self.goto.goto_location(mod_matches[0])
            else:
                self.goto_panel(mod_matches) # open panel with modules
        elif len(locations) == 1:
            self.goto.goto_location(locations[0])
        else:
            self.goto_panel(locations)

    def get_module_in_call(self, point):
        v = self.view
        this_module = self.module_name(v.file_name())
        expclass = sublime.CLASS_WORD_END | sublime.CLASS_WORD_START
        word_sep =' \"\t\n(){}[]+-*/=>,.;'
        call = v.substr(v.expand_by_class(point, expclass, word_sep))
        match = re.split('\'?:\'?', call)
        if len(match) == 2:
            return (match[0], match[1], match[0] == this_module)
        else:
            return (this_module, match[0], True)

    def loc_is_module(self, loc, expected):
        # TODO: escripts?
        lmod = self.module_name(loc[0])
        return (lmod != None) and (lmod == expected)

    def module_name(self, filename):
        (root, ext) = os.path.splitext(re.split('/', filename)[-1])
        if ext in ERLANG_EXTENSIONS:
            return root
        else:
            return None

    def goto_panel(self, locations):
        sel_idx = self.local_match_idx(locations)

        # apparently, on_highlight is not called on entry
        self.on_highlight_entry(sel_idx, locations)

        self.window.show_quick_panel(
            [self.goto.format_location(l) for l in locations],
            on_select = lambda x: self.on_select_entry(x, locations),
            selected_index = sel_idx,
            on_highlight = lambda x: self.on_highlight_entry(x, locations))

    def on_select_entry(self, x, locations):
        self.goto.select_entry(locations, x, self.view, None)

    def on_highlight_entry(self, x, locations):
        self.goto.highlight_entry(locations, x)

    def local_match_idx(self, locations):
        for idx in range(len(locations)):
            if locations[idx][0] == self.view.file_name():
                return idx
        return 0

@hook_window_command('goto_definition', 'source.erlang, source.yecc')
def erlang_goto_definition(window, symbol=None):
    if symbol is not None:
        return None

    view = window.active_view()
    point = view.sel()[0].begin()
    scope = view.scope_name(point)
    symbol = view.substr(view.word(point))

    scores = map(lambda s: sublime.score_selector(scope, s[1]), PREFIX_MAP)
    (maxscore, match) = max(zip(scores, PREFIX_MAP), key=lambda z: z[0])
    kind = match[0]

    if maxscore == 0:
        gotosym = symbol
    elif kind == 'Macro':
        gotosym = kind + ': ' + strip_before('?', symbol)
    elif kind == 'Record':
        gotosym = kind + ': ' + strip_before('#', symbol)
    elif kind == 'Function':
        GotoExactDefinition(view).at_position(kind, point)
        return ('noop', None)
    elif kind == 'Type':
        GotoExactDefinition(view).at_position(kind, point)
        return ('noop', None)
    else:
        gotosym = kind + ': ' + symbol

    return ('goto_definition', {'symbol': gotosym})

def strip_before(char, s):
    pos = s.find(char)
    return s[pos+1:]
