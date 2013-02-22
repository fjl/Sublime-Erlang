import sublime, sublime_plugin

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

@hook_window_command('goto_definition', 'source.erlang, source.yecc')
def erlang_goto_definition(window, symbol=None):
    if symbol is not None:
        return None

    view = window.active_view()
    position = view.sel()[0].begin()
    scope = view.scope_name(position)
    symbol = view.substr(view.word(position))

    scores = map(lambda s: sublime.score_selector(scope, s[1]), PREFIX_MAP)
    (maxscore, match) = max(zip(scores, PREFIX_MAP), key=lambda z: z[0])

    if maxscore == 0:
        gotosym = symbol
    elif match[0] == 'Macro':
        gotosym = match[0] + ': ' + strip_before('?', symbol)
    elif match[0] == 'Record':
        gotosym = match[0] + ': ' + strip_before('#', symbol)
    else:
        gotosym = match[0] + ': ' + symbol

    return ('goto_definition', {'symbol': gotosym})

def strip_before(char, s):
    pos = s.find(char)
    return s[pos+1:]
