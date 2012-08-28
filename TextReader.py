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
        if view.settings().get('syntax', "") != u'Packages/Text/Plain text.tmLanguage':
            return
        filename = view.file_name()
        if filename and not filename.lower().endswith(".txt"):
            return
        if view.size() < MIN_FILE_SIZE or view.file_name() in self.settings.get('not_use_reader', []):
            return
        self._change_mode(view)

    def on_modified(self, view):
        waiting_detect_encode = view.settings().get("waiting_detect_encode")
        if waiting_detect_encode:
            if view.settings().get('origin_encoding'):
                view.settings().erase("waiting_detect_encode")
                view.erase_status("waiting_detect_encode")
                self._change_mode(view)
            else:
                if waiting_detect_encode <= 1:
                    view.settings().erase("waiting_detect_encode")
                    view.erase_status("waiting_detect_encode")
                else:
                    view.settings().set("waiting_detect_encode", waiting_detect_encode - 1)

    def on_close(self, view):
        syntax = view.settings().get('syntax', "")
        if view.size() >= MIN_FILE_SIZE and syntax == u'Packages/Text/Plain text.tmLanguage':
            self._reset_not_use_reader(view, True)
            sublime.save_settings(CONFIG)
            return
        if  syntax != u'Packages/Text Reader/TextReader.tmLanguage':
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
        view_encoding = view.encoding()
        if (view_encoding == 'Undefined' or view_encoding == sublime.load_settings('Preferences.sublime-settings').get('fallback_encoding')) \
            and os.path.exists(os.path.join(sublime.packages_path(), "ConvertToUTF8")) \
            and not view.settings().get('origin_encoding'):
                view.set_status("waiting_detect_encode", "Wait ConvertToUTF8 to detect encoding. You may choose TextReader syntax manually")
                view.settings().set("waiting_detect_encode", 10)
                return
        view.set_read_only(True)
        view.set_syntax_file(u'Packages/Text Reader/TextReader.tmLanguage')
        fig = self._digest(view)
        if not fig:
            return
        pos = self.settings.get('history', {}).get(fig)
        if not pos:
            return
        sublime.set_timeout(lambda: self._show(view, pos), 500)

    def _show(self, view, pos):
        view.show(int(pos[1]))
        view.show(int(pos[0]), False)
        view.sel().clear()
        view.sel().add(sublime.Region(int((pos[0]+pos[1])/2)))

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
