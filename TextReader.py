import sublime
import sublime_plugin
import sha

CONFIG = "TextReader.sublime-settings"
MIN_FILE_SIZE = 10240

class TextReader(sublime_plugin.EventListener):

    def __init__(self, *args, **kwargs):
        super(TextReader, self).__init__(*args, **kwargs)
        self.settings = sublime.load_settings(CONFIG)

    def on_load(self, view):
        if view.settings().get('syntax', "").lower() != u'Packages/Text/Plain text.tmLanguage'.lower():
            return
        if view.size() < MIN_FILE_SIZE or view.file_name() in self.settings.get('not_use_reader', []):
            return
        view.set_syntax_file(u'Packages/TextReader/TextReader.tmLanguage')
        view.set_read_only(True)
        fig = self._digest(view)
        if not fig:
            return
        pos = self.settings.get('history', {}).get(fig)
        if not pos:
            return
        view.show(int(pos[1]))
        view.show(int(pos[0]), False)

    def on_close(self, view):
        syntax = view.settings().get('syntax', "").lower()
        if view.size() >= MIN_FILE_SIZE and syntax == u'Packages/Text/Plain text.tmLanguage'.lower():
            self._reset_not_use_reader(view, True)
            sublime.save_settings(CONFIG)
            return
        if  syntax != u'Packages/TextReader/TextReader.tmLanguage'.lower():
            return
        self._reset_not_use_reader(view)
        fig = self._digest(view)
        if not fig:
            return
        pos = view.visible_region()
        pos = [pos.begin(), pos.end()]
        history = self.settings.get('history', {})
        history[fig] = pos
        self.settings.set('history', history)
        sublime.save_settings(CONFIG)

    def _digest(self, view):
        vsize = view.size()
        src = view.substr(sublime.Region(0, vsize)).strip()
        if not src:
            return
        return sha.sha(src.encode('utf8')).hexdigest()

    def _reset_not_use_reader(self, view, add_cur_file=False):
        not_use_reader = self.settings.get('not_use_reader', [])
        fn = view.file_name()
        try:
            not_use_reader.remove(fn)
        except ValueError:
            pass
        if add_cur_file:
            not_use_reader.append(fn)
        if len(not_use_reader) > 30:
            not_use_reader.pop(0)
        self.settings.set('not_use_reader', not_use_reader)
