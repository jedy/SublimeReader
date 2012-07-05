import sublime
import sublime_plugin
import hashlib
import os.path

CONFIG = "TextReader.sublime-settings"
MIN_FILE_SIZE = 10240

class TextReader(sublime_plugin.EventListener):

    def __init__(self, *args, **kwargs):
        super(TextReader, self).__init__(*args, **kwargs)
        self.settings = sublime.load_settings(CONFIG)

    def on_load(self, view):
        self._change_mode(view)

    def on_modified(self, view):
        if view.settings().get("waiting_detect_encode") and view.settings().get('origin_encoding'):
            view.settings().erase("waiting_detect_encode")
            view.erase_status("waiting_detect_encode")
            self._change_mode(view)

    def on_close(self, view):
        syntax = view.settings().get('syntax', "")
        if view.size() >= MIN_FILE_SIZE and syntax == u'Packages/Text/Plain text.tmLanguage':
            self._reset_not_use_reader(view, True)
            sublime.save_settings(CONFIG)
            return
        if  syntax != u'Packages/TextReader/TextReader.tmLanguage':
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

    def _change_mode(self, view):
        if view.settings().get('syntax', "") != u'Packages/Text/Plain text.tmLanguage':
            return
        if view.size() < MIN_FILE_SIZE or view.file_name() in self.settings.get('not_use_reader', []):
            return
        view_encoding = view.encoding()
        if (view_encoding == 'Undefined' or view_encoding == sublime.load_settings('Preferences.sublime-settings').get('fallback_encoding')) \
            and os.path.exists(os.path.join(sublime.packages_path(), "ConvertToUTF8")) \
            and not view.settings().get('origin_encoding'):
                view.set_status("waiting_detect_encode", "Wait ConvertToUTF8 to detect encode. You may choose TextReader syntax manually")
                view.settings().set("waiting_detect_encode", True)
                return
        view.set_read_only(True)
        view.set_syntax_file(u'Packages/TextReader/TextReader.tmLanguage')
        fig = self._digest(view)
        if not fig:
            return
        pos = self.settings.get('history', {}).get(fig)
        if not pos:
            return
        view.show(int(pos[1]))
        view.show(int(pos[0]), False)

    def _digest(self, view):
        vsize = min(10240, view.size())
        src = view.substr(sublime.Region(0, vsize)).strip()
        if not src:
            return
        sha1 = hashlib.sha1()
        sha1.update(src.encode('utf8'))
        return sha1.hexdigest()

    def _reset_not_use_reader(self, view, add_cur_file=False):
        not_use_reader = self.settings.get('not_use_reader', [])
        fn = view.file_name()
        if not fn:
            return
        try:
            not_use_reader.remove(fn)
        except ValueError:
            pass
        if add_cur_file:
            not_use_reader.append(fn)
        if len(not_use_reader) > 30:
            not_use_reader.pop(0)
        self.settings.set('not_use_reader', not_use_reader)
