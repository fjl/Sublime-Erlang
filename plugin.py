import sublime, sublime_plugin

if (sublime.version() != '') and (sublime.version() < '3000'):
    pass
else:
    from .st3 import ErlangCommandHooks

class ExecInProjectFolderCommand(sublime_plugin.WindowCommand):
    def run(self, **kwargs):
        folders = self.window.folders()
        if len(folders) >= 1:
            kwargs['working_dir'] = folders[0]
            v = self.window.active_view()
            if v is not None and v.file_name() is not None:
                for folder in folders:
                    if v.file_name().startswith(folder):
                        kwargs['working_dir'] = folder
                        break

        self.window.run_command("exec", kwargs)
