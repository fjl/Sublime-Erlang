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
    ('Function',  'entity.name.function.erlang'),
    ('Function',  'entity.name.function.definition.erlang'),
    ('Type',      'storage.type.erlang'),
    ('Type',      'storage.type.definition.erlang'),
    ('Record',    'storage.type.record.erlang'),
    ('Record',    'storage.type.record.definition.erlang'),
    ('Macro',     'keyword.other.macro.erlang'),
    ('Module',    'entity.name.type.class.module.erlang'),
    ('Yecc Rule', 'entity.name.token.unquoted.yecc'),
    ('Yecc Rule', 'entity.name.token.quoted.yecc')
]

ERLANG_EXTENSIONS = ['.erl', '.hrl', '.xrl', '.yrl']

def basename(filename):
    return re.split('/', filename)[-1]

def loc_is_module(loc, module_name):
    # TODO: escripts?
    (root, ext) = os.path.splitext(basename(loc[0]))
    return (ext in ERLANG_EXTENSIONS) and (root == module_name)

def get_module_in_call(view, point):
    expclass = sublime.CLASS_WORD_END | sublime.CLASS_WORD_START
    call_r = view.expand_by_class(point, expclass, ' \"\t\n(){}[]+-*/=>,.;')
    call = view.substr(call_r)
    match = re.split('\'?:\'?', call)
    if len(match) == 2:
        return (match[0], match[1])

def goto_exact_definition(kind, view, point):
    window = view.window()
    expanded = get_module_in_call(view, point)
    if expanded is None:
        return False
    else:
        (module, funcname) = expanded

    # GotoDefinition could change at any time, but I don't feel like
    # writing all of its code again just for the sake of being future-proof
    goto = Default.symbol.GotoDefinition(window)
    matches = goto.lookup_symbol(kind + ': ' + funcname)
    locations = [loc for loc in matches if loc_is_module(loc, module)]

    if len(locations) == 0:
        return False  # run across all modules if nothing matches
    elif len(locations) == 1:
        goto.goto_location(locations[0])
    else:
        window.show_quick_panel(
            [goto.format_location(l) for l in locations],
            on_select = lambda x: goto.select_entry(locations, x, view, None),
            on_highlight = lambda x: goto.highlight_entry(locations, x))
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
    elif kind == 'Function' and goto_exact_definition(kind, view, point):
        return None  # abort if there was an exact match
    elif kind == 'Type' and goto_exact_definition(kind, view, point):
        return None  # abort if there was an exact match
    else:
        gotosym = kind + ': ' + symbol

    return ('goto_definition', {'symbol': gotosym})

def strip_before(char, s):
    pos = s.find(char)
    return s[pos+1:]
