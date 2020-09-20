from threading import Timer as tym
import getpass
import socket
import os
import json
import re
from Syntax import Syntax as syntax
from About import About as about
from File import FileOpener as fileOpener
from Notebook import Notebook as notebook
from Suggestions import suggestion, Completion, errors, place_search_bar
from Data import *
import subprocess
from subprocess import PIPE
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango, Gio

#result = subprocess.run(command,capture_output=True,text=True,shell=True)

builder = Gtk.Builder()
builder.add_from_file('TextEditor2.glade')

builder2 = Gtk.Builder()
FILE_WIN_KEY = 0
CONSOLE_WIN_KEY = 0
CLOSE_UNSAVED_RESPONSE=None
console_temp_key = 0
current_tag = None
current = None
suggestion_showing = False
auto_save_interval = 0
force_show_suggestion = False
indent_key = 0
err = errors
sugg = None
TEXT=''
INS_KEY = 0


class Window:
    global builder

    def __init__(self, application=None):
        self.window = builder.get_object('PyEdit')
        self.window.set_title('PyEdit')
        self.window.set_default_size(800, 800)
        self.notebook = builder.get_object('notebook')
        self.console_area = builder.get_object('console_area')
        self.css = Gtk.CssProvider()
        self.font = Pango.FontDescription()
        self.font.from_string(settings['font'])
        self.css.load_from_path('./custom_theme.css')
        self.suggestion = builder.get_object('suggestion_win')

        self.suggestion_list = Gtk.ListStore(str)

        self.errorview = builder.get_object('problems_view')
        self.errorlist = Gtk.ListStore(str)

        self.suggestion_view = builder.get_object('suggest_view')
        self.suggestion_view.set_model(self.suggestion_list)
        self.suggestion_scroll = builder.get_object('suggestion_scroll')
        self.screen = Gdk.Display.get_default_screen(Gdk.Display.get_default())
        Gtk.StyleContext().add_provider_for_screen(self.screen, self.css, 600)
        if not application:
            self.window.set_application(application)
        header_bar = Gtk.HeaderBar()

        hb_btn1 = Gtk.Button(label='Open')
        hb_btn1.connect('clicked', self.ctrl_o)
        hb_btn2 = Gtk.Button()
        hb_btn2.connect('clicked', self.ctrl_n)
        self.hb_btn3 = Gtk.Button(label='Save')
        self.hb_btn3.connect('clicked', self.ctrl_s)
        self.menu_btn = Gtk.Button()
        self.menu_btn.connect('clicked', self.popup_menu)
        self.pop = builder.get_object("popoverMenu2")
        # icons
        new_icon2 = Gtk.Image.new_from_icon_name(
            'open-menu-symbolic', Gtk.IconSize.BUTTON)
        new_icon = Gtk.Image.new_from_icon_name(
            'document-new-symbolic', Gtk.IconSize.BUTTON)
        # button boxes
        btn_box1 = Gtk.Box()
        btn_box2 = Gtk.Box()

        # adding images to btn
        hb_btn2.add(new_icon)
        self.menu_btn.add(new_icon2)
        # packing btn in box
        btn_box1.pack_start(hb_btn1, True, True, 0)
        btn_box1.pack_end(hb_btn2, True, True, 1)
        btn_box2.add(self.hb_btn3)
        btn_box2.add(self.menu_btn)
        # Header Bar
        header_bar.set_show_close_button(True)
        header_bar.pack_start(btn_box1)
        header_bar.pack_end(btn_box2)
        header_bar.props.title = "PyEdit"

        self.window.set_titlebar(header_bar)
        self.window.show_all()

    def load(self):
        global files_opened, sugg, err
        builder.get_object('justification').set_active_id(
            settings['justification'])
        builder.get_object('closing_quote').set_active_id(
            settings['closing_quote'])
        builder.get_object('closing_brackets').set_active_id(
            settings['closing_bracket'])
        builder.get_object('save_delay').set_value(settings['auto_save_delay'])
        builder.get_object('save_interval').set_active_id(
            settings['auto_save_timing'])
        autosave = builder.get_object('auto_save')
        if settings['auto_save'] == 'on':
            autosave.set_active(True)
        else:
            autosave.set_active(False)
        self.files_pane()
        li = self.errorlist
        vi = self.errorview
        err = errors(li, vi)
        self.hb_btn3.set_sensitive(False)
        for i in files_opened:
            if os.path.exists(i):
                Notebook().new_page(file_name=i)
                self.update_page()
                Syntax()
                self.line_and_column()

    def show(self, *args):
        self.window.show_all()
        self.load()

    def on_execute(self, *args):
        self.update_page()
        global current
        current_file = Data['files_opened'][current-1]
        if current-1 != -1:
            process = subprocess.Popen(
                ['python3', current_file], stdout=PIPE, stderr=PIPE)
        else:
            return
        print(process.stdout.read().decode())

    def popup_menu(self, args):
        self.pop.set_relative_to(self.menu_btn)
        builder.get_object('search-win').hide()
        self.pop.popup()

    def ctrl_o(self, args):
        FileOpener()

    def ctrl_s(self, *args):
        FileSaveWin().save()


    def delete_range(self,*_):
        global INS_KEY,TEXT
        if _[2].get_line_index() - _[1].get_line_index() > 1:
            TEXT = _[0].get_text(_[1],_[2],True)
            INS_KEY = 1
        else:
            INS_KEY=0
    def notebook_key_press(self, *args):
        global current, force_show_suggestion,TEXT,INS_KEY
        self.update_page()
        current = self.notebook.get_current_page()
        key = str(Gdk.keyval_name(args[1].keyval))
        ctrl = (args[1].state & Gdk.ModifierType.CONTROL_MASK)
        page = current-1
        chars = ['\'','\"','{','[','(','`']
        if key == 'parenleft' and settings['closing_bracket'] == 'on':
            Data['text_buffer'][page].insert_at_cursor(')')
            cursor = Data['text_buffer'][current-1].get_insert()
            start = Data['text_buffer'][current-1].get_iter_at_mark(cursor)
            start.backward_char()
            Data['text_buffer'][page].place_cursor(start)
            if INS_KEY == 1:
                Data['text_buffer'][page].insert_at_cursor(TEXT)
                INS_KEY = 0
                TEXT =''
        elif key == 'quotedbl' and settings['closing_quote'] == 'on':
            Data['text_buffer'][page].insert_at_cursor('\"')
            cursor = Data['text_buffer'][current-1].get_insert()
            start = Data['text_buffer'][current-1].get_iter_at_mark(cursor)
            start.backward_char()
            Data['text_buffer'][page].place_cursor(start)
            if INS_KEY == 1:
                Data['text_buffer'][page].insert_at_cursor(TEXT)
                INS_KEY = 0
                TEXT =''
        elif key == 'apostrophe' and settings['closing_quote'] == 'on':
            Data['text_buffer'][page].insert_at_cursor('\'')
            cursor = Data['text_buffer'][current-1].get_insert()
            start = Data['text_buffer'][current-1].get_iter_at_mark(cursor)
            start.backward_char()
            Data['text_buffer'][page].place_cursor(start)
            if INS_KEY == 1:
                Data['text_buffer'][page].insert_at_cursor(TEXT)
                INS_KEY = 0
                TEXT =''
        elif key == 'bracketleft' and settings['closing_bracket'] == 'on':
            Data['text_buffer'][page].insert_at_cursor(']')
            cursor = Data['text_buffer'][current-1].get_insert()
            start = Data['text_buffer'][current-1].get_iter_at_mark(cursor)
            start.backward_char()
            Data['text_buffer'][page].place_cursor(start)
            if INS_KEY == 1:
                Data['text_buffer'][page].insert_at_cursor(TEXT)
                INS_KEY = 0
                TEXT =''
        elif key == 'braceleft' and settings['closing_bracket'] == 'on':
            Data['text_buffer'][page].insert_at_cursor('}')
            cursor = Data['text_buffer'][current-1].get_insert()
            start = Data['text_buffer'][current-1].get_iter_at_mark(cursor)
            start.backward_char()
            Data['text_buffer'][page].place_cursor(start)
            if INS_KEY == 1:
                Data['text_buffer'][page].insert_at_cursor(TEXT)
                INS_KEY = 0
                TEXT =''
        elif ctrl and key == 'space':
            force_show_suggestion = True
        else:
            force_show_suggestion = False
        for i in range(3):
            self.line_and_column()
        
    def ctrl_n(self, *args):
        num = self.notebook.get_n_pages()
        Notebook().new_page(f'*untitled {num}')

    def indent(self, *args):
        self.update_page()
        global current, suggestion_showing, force_show_suggestion
        global indent_key, sugg
        self.line_and_column()
        key = str(Gdk.keyval_name(args[1].keyval))
        Syntax()
        page = current-1
        if key == 'colon':
            indent_key = 1
        elif key == 'Return':
            if indent_key == 1:
                cur = Data['text_buffer'][page].get_insert()
                l = Data['text_buffer'][page].get_iter_at_mark(cur)
                l.backward_line()
                chars = Data['text_buffer'][page].get_iter_at_mark(
                    cur).get_slice(l)
                chars = str(chars)
                num_of_i = chars.split('\t')
                if len(num_of_i) == 1:
                    num_of_i = chars.split('    ')
                num_of_i = len(num_of_i[:-1])
                indent_key = 0
                if num_of_i == 0:
                    Data['text_buffer'][page].insert_at_cursor('    ')
                else:
                    Data['text_buffer'][page].insert_at_cursor(
                        '    '*int(num_of_i+1))
                indent_key = 0
            else:
                cur = Data['text_buffer'][page].get_insert()
                l = Data['text_buffer'][page].get_iter_at_mark(cur)
                l.backward_line()
                chars = Data['text_buffer'][page].get_iter_at_mark(
                    cur).get_slice(l)
                f = l.forward_search(
                    ':', 0, Data['text_buffer'][page].get_iter_at_mark(cur))
                if f is not None:
                    chars = str(chars)
                    num_of_i = chars.split('\t')
                    if len(num_of_i) == 1:
                        num_of_i = chars.split('    ')
                    num_of_i = len(num_of_i[:-1])
                    indent_key = 0
                    if num_of_i == 0:
                        Data['text_buffer'][page].insert_at_cursor(
                            '    ')
                    else:
                        Data['text_buffer'][page].insert_at_cursor(
                            '    '*int(num_of_i+1))
                    indent_key = 0
                else:
                    chars = str(chars)
                    num_of_i = chars.split('\t')
                    if len(num_of_i) == 1:
                        num_of_i = chars.split('   ')
                    num_of_i = len(num_of_i[:-1])
                    indent_key = 0
                    if num_of_i == 0:
                        pass
                    else:
                        Data['text_buffer'][page].insert_at_cursor(
                            '    '*int(num_of_i))
        # settting popup location
        _text1 = Data['text_buffer'][current-1].get_text(Data['text_buffer'][current-1].get_start_iter(
        ), Data['text_buffer'][current-1].get_iter_at_mark(Data['text_buffer'][current-1].get_insert()), False)
        suggestion(_text1, self.suggestion_list)
        if force_show_suggestion == True:
            sugg = Completion(self)
            sugg.show(current, True)
        else:
            sugg = Completion(self)
            sugg.show(current)
        _text = Data['text_buffer'][current-1].get_text(Data['text_buffer'][current-1].get_start_iter(
        ), Data['text_buffer'][current-1].get_end_iter(), False)
        _err_btn = builder.get_object('err_btn')
        err.error_check(text=_text, err_btn=_err_btn, current=current)

    def close_tab(self, *args):
        global current
        self.update_page()
        self.update_page()
        file_content = Data['text_buffer']
        for i in Data['close_btn']:
            if i == args[0]:
                index = Data['close_btn'].index(i)
                if Data['modified'][index] == True:
                    close_dialog = builder.get_object('close-unsaved')
                    label = close_dialog.get_children()[0].get_children()[0].get_children()[1].get_children()[0]
                    lab_text = str(label.get_text())
                    label.set_text('Save changes to {} before closing'.format(Data['file_label'][index].get_text()))
                    close_dialog.run()
                    if CLOSE_UNSAVED_RESPONSE == 0:
                        return
                    elif CLOSE_UNSAVED_RESPONSE == 2:
                        FileSaveWin().save()
                    elif CLOSE_UNSAVED_RESPONSE == 1:pass
                for j in Data.keys():
                    del Data[j][index]
                self.notebook.remove_page(index+1)

        

    def line_and_column(self, *args):
        global current
        page = current-1
        tb = Data['text_buffer'][page]
        line_lab = builder.get_object('line')
        col_lab = builder.get_object('column')
        cur = tb.get_insert()
        line = tb.get_iter_at_mark(cur).get_line()+1
        col = tb.get_iter_at_mark(cur).get_line_index()
        line_lab.set_text(f'ln {line} ')
        col_lab.set_text(f'col {col}')
        # line numbers
        num_of_lines = tb.get_line_count()
        prev_lab = Data['line_lab'][page].get_text()
        current_line_lab = ''
        for i in range(1, int(num_of_lines)+1):
            current_line_lab = current_line_lab+str(i)+' '+'\n'
        Data['line_lab'][page].set_text(current_line_lab)

    def cursor(self, *args):
        for i in range(3):
            self.line_and_column()
            self.update_page()
        Syntax()
        try:
            sugg.hide()
        except AttributeError:
            return

    def files_pane(self):
        # creating file storage
        self.file_list = Gtk.ListStore(str)
        __files_opened = []
        for i in range(0, len(files_opened)):
            __files_opened.append(files_opened[i].split('/')[-1])
        for i in __files_opened:
            self.file_list.append([i])
        self.file_view = Gtk.TreeView(model=self.file_list)
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn("Files opened", renderer_text, text=0)
        self.file_view.append_column(column_text)
        # displaying the files
        file_box = builder.get_object('files_opened')
        self.file_view.show_all()
        file_box.add(self.file_view)
        file_box.show_all()

    def update_page(self, *args):
        global current
        notebook = builder.get_object('notebook')
        for i in range(5):
            current = notebook.get_current_page()
        if current < 1:
            builder.get_object('err_btn').set_sensitive(False)
            builder.get_object('setting-btn').set_sensitive(False)
            self.hb_btn3.set_sensitive(False)
        else:
            self.hb_btn3.set_sensitive(True)
            builder.get_object('err_btn').set_sensitive(True)
            builder.get_object('setting-btn').set_sensitive(True)
            _text = Data['text_buffer'][current-1].get_text(
               Data['text_buffer'][current-1].get_start_iter(),
               Data['text_buffer'][current-1].get_end_iter(),
               False)
            _err_btn = builder.get_object('err_btn')
            err.error_check(text=_text, err_btn=_err_btn, current=current)

class About:
    def __init__(self):
        self.about = about(Window)

    def show_about(self, *Args):
        self.about.show_about()

class Syntax(Window):
    def __init__(self):
        super().__init__(self)
        self.update_page()
        syntax(current)

class FileOpener:
    def __init__(self):
        fileOpener(Notebook,Window)

class Notebook(notebook):
    def __init__(self):
        super().__init__(Window)

class FileSaveWin(Window):
    def __init__(self):
        super().__init__()

    def save_as(self,force=False):
        global current
        if os.path.exists(Data['files_opened'][current-1]) == False or force==True:
            self.save_win = Gtk.FileChooserDialog(
                title='Create new  file', parent=self.window)
            self.save_win.set_action(Gtk.FileChooserAction.SAVE)
            self.save_win.add_buttons(Gtk.STOCK_CANCEL,
                                      Gtk.ResponseType.CANCEL,
                                      Gtk.STOCK_SAVE,
                                      Gtk.ResponseType.ACCEPT
                                      )
            self.save_win.set_do_overwrite_confirmation(True)
            filt = Gtk.FileFilter()
            filt.set_name('Python Files')
            filt.add_mime_type("text/x-python")
            self.save_win.add_filter(filt)
            response = self.save_win.run()
            if response == Gtk.ResponseType.ACCEPT:
                file_dir = str(self.save_win.get_uri()).split('///')[1]
                self.save_win.destroy()
                if file_dir.endswith('.py') == False:
                    file_dir = file_dir+'.py'
                if file_dir.startswith('/') == False:
                    file_dir = '/'+file_dir
            else:
                self.save_win.destroy()
                return
            buf = Data['text_buffer'][current-1]
            buf_s = buf.get_start_iter()
            buf_e = buf.get_end_iter()
            file_data = buf.get_text(buf_s, buf_e, True)
            label_name = file_dir.split('/')[-1]
            with open(file_dir, 'w') as f:
                f.write(file_data)
                Data['text_buffer'][current-1].set_text(file_data)
                Data['text_buffer'][current-1].set_modified(False)
                Data['modified'][current-1] = False
            Data['file_label'][current-1].set_label(label_name)
            Data['files_opened'][current-1] = file_dir

    def save(self):
        file = Data['files_opened'][current-1]
        if not os.path.isfile(file):
            self.save_as()
            return
        else:
            file_dir = '/'+Data['files_opened'][current-1]
            if os.path.isfile(file_dir):
                buf = Data['text_buffer'][current-1]
                buf_s = buf.get_start_iter()
                buf_e = buf.get_end_iter()
                with open(file_dir, 'w') as f:
                    file_data = buf.get_text(buf_s, buf_e, False)
                    f.write(file_data)
                    Data['text_buffer'][current-1].set_modified(False)
                    Data['modified'][current-1] = False
    def save_all(self):
        for i in Data['files_opened']:
            index = Data['files_opened'].index(i)
            if os.path.exists(i):
                buff = Data['text_buffer'][index]
                st  = buff.get_start_iter()
                end = buff.get_end_iter()
                file_dat = buff.get_text(st,end,False)
                with open(i,'w') as file:
                    file.write(file_dat)
            else:
                buff = Data['text_buffer'][index]
                st  = buff.get_start_iter()
                end = buff.get_end_iter()
                file_dat = buff.get_text(st,end,False)
                self.save_win = Gtk.FileChooserDialog(
                title='Create new file', parent=self.window)
                self.save_win.set_action(Gtk.FileChooserAction.SAVE)
                self.save_win.add_buttons(Gtk.STOCK_CANCEL,
                                          Gtk.ResponseType.CANCEL,
                                          Gtk.STOCK_SAVE,
                                          Gtk.ResponseType.ACCEPT
                                          )
                self.save_win.set_do_overwrite_confirmation(True)
                filt = Gtk.FileFilter()
                filt.set_name('Python Files')
                filt.add_mime_type("text/x-python")
                self.save_win.add_filter(filt)
                response = self.save_win.run()
                if response == Gtk.ResponseType.ACCEPT:
                    file_dir = str(self.save_win.get_uri()).split('///')[1]
                    self.save_win.destroy()
                    if file_dir.endswith('.py') == False:
                        file_dir = file_dir+'.py'
                    if file_dir.startswith('/') == False:
                        file_dir = '/'+file_dir
                else:
                    self.save_win.destroy()
                    continue
                with open(file_dir, 'w') as file:
                    file.write(file_dat)
class Handler(Window):
    def quit(self, *args):
        with open('settings.json', 'w') as js:
            dat = json.dump({
                'setting': settings,
                'color': Syntax_Colors,
                'files_opened': Data['files_opened']
            }, js, indent=2)
        if True in Data['modified']:
            close_dialog = builder.get_object('close-unsaved')
            label = close_dialog.get_children()[0].get_children()[0].get_children()[1].get_children()[0]
            btn = close_dialog.get_children()[0].get_children()[1].get_children()[0].get_children()[2]
            if Data['modified'].count(True) > 1:
                btn.set_label('Save all')
                label.set_text('Save changes to all files before closing')
            elif len(Data['files_opened']) == 1:
                label.set_text('Save changes to \"{}\" before closing'.format(str(Data['file_label'][0].get_text())))
                btn.set_label('Save')
            close_dialog.run()

            if CLOSE_UNSAVED_RESPONSE == 0: ## i.e cancel
                return True
            elif CLOSE_UNSAVED_RESPONSE == 1: ## i.e close without saving
                Gtk.main_quit()                
            elif CLOSE_UNSAVED_RESPONSE == 2:
                FileSaveWin().save_all()
                Gtk.main_quit()
        else:
            Gtk.main_quit()
        return False
    
    def t_a_t(self,*_):
        c_u_s = builder.get_object('close-unsaved')
        c_u_s.run()

    def response(self,btn,*_):
        global CLOSE_UNSAVED_RESPONSE
        c_u_s = builder.get_object('close-unsaved')
        close_without_saving = builder.get_object('close-without-saving-btn')
        cancel = builder.get_object('cancel-close-btn')
        save = builder.get_object('save-close-btn')
        if btn == close_without_saving:
            CLOSE_UNSAVED_RESPONSE = 1 #close without saving
        elif btn == cancel:
            CLOSE_UNSAVED_RESPONSE = 0 #cancel
        elif btn == save:
            CLOSE_UNSAVED_RESPONSE = 2 #Save
        c_u_s.hide()
    def toggle_file_win(self, *args):
        global FILE_WIN_KEY
        file_win = builder.get_object('file_area')
        if FILE_WIN_KEY == 0:
            file_win.set_reveal_child(True)
            file_win.show_all()
            FILE_WIN_KEY = 1
        else:
            FILE_WIN_KEY = 0
            file_win.set_reveal_child(False)
            file_win.show_all()

    def toggle_console_win(self, *args):
        global CONSOLE_WIN_KEY
        console = builder.get_object('console_area')
        if CONSOLE_WIN_KEY == 0:
            console.set_reveal_child(True)
            console.show_all()
            CONSOLE_WIN_KEY = 1
        else:
            console.set_reveal_child(False)
            console.show_all()
            CONSOLE_WIN_KEY = 0

    def toggle_showing(self, *_):
        global suggestion_showing
        suggestion_showing = not suggestion_showing

    def close(self, *args):
        args[0].hide()
        start_clear_s = Data['text_buffer'][current-1].get_start_iter()
        start_clear_e = Data['text_buffer'][current-1].get_end_iter()
        Data['text_buffer'][current -
                            1].remove_tag_by_name('search_tag', start_clear_s, start_clear_e)


    def on_next(self, *args):
        cur = self.notebook.get_current_page()
        self.notebook.next_page()

    def ctrl_f(self, *args):
        self.update_page()
        pop = builder.get_object('search-win')
        place_search_bar(current, self.window, pop)

    def on_key_press(self, *args):
        global keyword, operators
        ctrl = (args[1].state & Gdk.ModifierType.CONTROL_MASK)
        if ctrl and args[1].keyval == Gdk.KEY_f:
            self.ctrl_f()
        elif ctrl and args[1].keyval == Gdk.KEY_n:
            self.ctrl_n()
        elif ctrl and args[1].keyval == Gdk.KEY_o:
            self.on_file_open()

    def on_new(self, *args): self.ctrl_n()
    def on_auto_save(self, *args):
        if args[0].get_state():
            settings['auto_save'] = 'on'
        else:
            settings['auto_save'] = 'off'

    def on_auto_save_delay(self, *args):
        val = args[0].get_value_as_int()
        settings['auto_save_delay'] = val

    def on_save_interval_changed(self, *args):
        val = args[0].get_active_id()
        settings['auto_save_timing'] = val

    def on_about(self, *args):
        About().show_about()

    def on_search_go(self, *args):
        global current, words
        text = args[0].get_text()
        cursor = Data['text_buffer'][current-1].get_insert()
        if Data['text_buffer'][current-1].get_tag_table().lookup('search_tag') != None:
            start_clear_s = Data['text_buffer'][current-1].get_start_iter()
            start_clear_e = Data['text_buffer'][current-1].get_end_iter()
            Data['text_buffer'][current -
                                1].remove_tag_by_name('search_tag', start_clear_s, start_clear_e)
        start = Data['text_buffer'][current-1].get_iter_at_mark(cursor)
        if text != '':
            start = Data['text_buffer'][current-1].get_start_iter()
            self.search_and_mark(text, start)

    def search_and_mark(self, text, start):
        global current, current_tag
        page = current-1
        color = Syntax_Colors['search']
        end = Data['text_buffer'][page].get_end_iter()
        if Data['text_buffer'][page].get_tag_table().lookup('search_tag') == None:
            current_tag = Data['text_buffer'][page].create_tag(
                'search_tag', background=color)
        current_tag.set_property('background', color)
        match = start.forward_search(text, 0, end)
        if match is not None:
            match_start, match_end = match
            Data['text_buffer'][page].apply_tag_by_name(
                'search_tag', match_start, match_end)
            self.search_and_mark(text, match_end)

    def on_setting_close(self, *args):
        setting_tab = builder.get_object('setting_tab')
        setting_body = builder.get_object('setting_body')

    def on_page_removed(self, *args):
        self.update_page()

    def window_key_press(self, *args):
        keyPress_label = builder.get_object('keyPress')
        keyPress_label.set_text(Gdk.keyval_name(args[1].keyval))
        self.window.show_all()

    def font_changed(self, *args):
        global current
        settings['font'] = args[0].get_font()
        self.font.from_string(settings['font'])

    def word_wrap_changed(self, *args):
        val = args[0].get_active_iter()
        if val is not None:
            model = args[0].get_model()
            wrap = model[val][0]

    def justification_changed(self, *args):
        val = args[0].get_active_iter()
        if val is not None:
            model = args[0].get_model()
            justify = model[val][0]
        else:
            return
        settings['justification'] = str(justify).lower()

    def quote_changed(self, *args):
        global settings
        val = args[0].get_active_iter()
        if val is not None:
            model = args[0].get_model()
            quote_val = model[val][0]
        else:
            return
        settings['closing_quote'] = str(quote_val).lower()

    def bracket_changed(self, *args):
        global settings
        val = args[0].get_active_iter()
        if val is not None:
            model = args[0].get_model()
            brack = model[val][0]
        else:
            return
        settings['closing_bracket'] = str(brack).lower()

    def console_key_press(self, view, event):
        modifier_mask = Gtk.accelerator_get_default_mod_mask()
        event_state = event.state & modifier_mask
        if event.keyval == Gdk.KEY_KP_Left or event.keyval == Gdk.KEY_Left or \
                event.keyval == Gdk.KEY_BackSpace:
            buf = view.get_buffer()
            inp = buf.get_iter_at_mark(buf.get_mark('terminal'))
            cur = buf.get_iter_at_mark(buf.get_insert())
            if inp.compare(cur) == 0:
                if not event_state:
                    buf.place_cursor(inp)
                return True
            return False

    def on_settings(self, *args): pass

    def apply_suggested_word(self, word):
        global current
        skip = [' ', '\'', '\"', '(', '{', '.', '@','_']
        page = current-1
        cur = Data['text_buffer'][page].get_insert()
        it1 = Data['text_buffer'][page].get_iter_at_mark(cur)
        it2 = Data['text_buffer'][page].get_iter_at_mark(cur)
        it1.backward_char()
        prevl_ = Data['text_buffer'][page].get_text(it1, it2, False)
        it1.forward_char()
        if prevl_ not in skip:
            it1.backward_word_start()
            Data['text_buffer'][page].delete(it1, it2)
        Data['text_buffer'][page].insert(it2, word)

    def on_suggest_activated(self, *args):
        global sugg
        sellection = args[0].get_selection().get_selected_rows()
        model, pathlist = sellection
        val = ''
        for p in pathlist:
            tree = model.get_iter(p)
            val = model.get_value(tree, 0)
            sugg.hide()
        self.apply_suggested_word(val)
        args[0].get_selection().unselect_all()

    def errors(self, *args):
        console_notebook = builder.get_object('console_notebook')
        console_notebook.set_current_page(1)
        self.toggle_console_win()

    def on_page_added(self, *_):
        self.update_page()
        for i in range(2):
            if len(Data['files_opened']) > 0:
                Syntax()
                self.line_and_column()

    def search_win_leave(self, *_):
        self.window.present()

    def toggle_replace(self, *_):
        rev = builder.get_object('replace-rev')
        img = builder.get_object('reveal-replace-entry')
        revealed = rev.get_child_revealed()
        cur_rev = not revealed
        rev.set_reveal_child(cur_rev)
        if cur_rev == False:
            img.set_from_icon_name('go-down', Gtk.IconSize.MENU)
        else:
            img.set_from_icon_name('go-up', Gtk.IconSize.MENU)

    def focus_left_window(self, widget, event, *_):
        global sugg
        s_win = builder.get_object('search')
        try:
            sugg.hide()
        except AttributeError:
            pass

    def showing(self, *args):
        pass

    def win_state_event(self, *_):
        if not self.window.is_active():
            builder.get_object('search-win').hide()
        else:
            try:
                place_search_bar(current,
                                self.window,
                                builder.get_object('search-win'))
            except:return
    def win_resized(self,*_):
        pass
    def on_save_as(self,*a_r_g_s_):
        FileSaveWin().save_as(True)
    def on_preference(self,*_):
        pref = builder.get_object('Preferences')
        pref.run()
    def close_pref(self,*_):
        _[0].hide()

builder.connect_signals(Handler())

if __name__ == '__main__':
    win = Window()
    win.show()
    Gtk.main()
