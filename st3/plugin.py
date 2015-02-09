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
        self.view = view
        self.window = view.window()

    def at_position(self, kind, point):
        (module, funcname, is_local) = self.get_module_in_call(point)
        matches = lookupsym(self.window, kind + ': ' + funcname)
        locations = [loc for loc in matches if loc_is_module(loc, module)]
        if len(locations) > 0:
            # qualified call, jump to results
            return self.jump(kind, funcname, locations)
        elif not is_local:
            # try to at least jump to the module
            mod_matches = lookupsym(self.window, 'Module: ' + module)
            return self.jump('Module', module, mod_matches)
        else:
            # no exact matches, no module info: search for just the name
            return self.jump(kind, funcname, matches)

    def get_module_in_call(self, point):
        v = self.view
        this_module = file_module_name(v.file_name())
        expclass = sublime.CLASS_WORD_END | sublime.CLASS_WORD_START
        word_sep =' \"\t\n(){}[]+-*/=>,.;'
        call = v.substr(v.expand_by_class(point, expclass, word_sep))
        match = re.split('\'?:\'?', call)
        # TODO: handle case when module is macro
        if len(match) == 2:
            return (match[0], match[1], match[0] == this_module)
        else:
            return (this_module, match[0], True)

    def jump(self, kind, symbol, locations):
        if len(locations) == 0:
            sublime.status_message('Unable to find: ' + symbol)
            return ('noop', None)
        elif len(locations) == 1 or allsamefile(locations):
            fname, display_fname, rowcol = locations[0]
            row, col = rowcol
            self.window.open_file(fname + ":" + str(row) + ":" + str(col), sublime.ENCODED_POSITION)
            return ('noop', None)
        else:
            # Fall back to builtin Goto Symbol.
            # Older versions of the code used to be more clever
            # and tried to improve the user experience of the Goto Definition
            # panel in this case. We're less clever now, because the implementation
            # of that panel is not stable and we'd need to adapt to changes all
            # the time.
            return ('goto_definition', {'symbol': kind + ': ' + symbol})

def loc_is_module(loc, expected):
    # TODO: escripts?
    lmod = file_module_name(loc[0])
    return (lmod != None) and (lmod == expected)

def file_module_name(filename):
    (root, ext) = os.path.splitext(re.split('/', filename)[-1])
    if ext in ERLANG_EXTENSIONS:
        return root
    else:
        return None

def lookupsym(window, symbol):
    if sublime.version() < '3069':
        return Default.symbol.GotoDefinition(window).lookup_symbol(symbol)
    else:
        matches = Default.symbol.lookup_symbol(window, symbol)
        if matches is None:
            matches = []
        return matches

def allsamefile(locs):
    f0, _, _ = locs[0]
    for loc in locs[1:]:
        f, _, _ = loc
        if f != f0:
            return False
    return True

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
        return GotoExactDefinition(view).at_position(kind, point)
    elif kind == 'Type':
        return GotoExactDefinition(view).at_position(kind, point)
    else:
        gotosym = kind + ': ' + symbol
    return ('goto_definition', {'symbol': gotosym})

def strip_before(char, s):
    pos = s.find(char)
    return s[pos+1:]
