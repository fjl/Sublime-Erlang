import sublime, sublime_plugin, string

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

class ErlangGotoDefinition(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
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

        self.window.run_command('goto_definition', {'symbol': gotosym})

    def is_enabled(self):
        return self.window.active_view() is not None

def strip_before(char, s):
    pos = s.find(char)
    return s[pos+1:]
