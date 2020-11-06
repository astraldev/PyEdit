from json import dumps, loads
import gi, shutil, getpass
from shutil import move
import os
import re
gi.require_version("GtkSource", "4")
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
gi.require_version('Vte', '2.91')
from datetime import datetime as deltime
from gi.repository import Gtk, Gdk, GLib, WebKit2, Pango, Gio, Vte, GtkSource
from PyEditxN import new_page, modify, save, save_as, change_font, get_f_img
from autopep8 import fix_code

USRNAME = getpass.getuser()
builder = Gtk.Builder()
builder.add_from_file('./ui.ui')

menu_items = ["New page","Open File","New file","Create folder", "Open folder","<hr>","Save","Run file", "Format document"]
folder_menu = ["New file","New folder","<hr>","Cut","Copy","Copy path","<hr>","Rename","Delete"]
delete_popup_text = "Are you sure you want to delete <b>{}</b> "
pages = []
content = {
    "temp": {
        'text_buffers': [],
        "files_opened": [],
        'text_views': [],
        "modified": [],
        "tab-label":[],
        "mime-types":[]
    },
    'window': builder.get_object('Window'),
    'about': builder.get_object('About'),
    'header_bar': builder.get_object('header-bar'),
    "t-box":builder.get_object("t-box"),
    'notebook': builder.get_object('Notebook'),
    'p_bar': builder.get_object('save-progress'),

    'menu-popup': builder.get_object('menu-popup'),
    'file-chooser': builder.get_object('file-chooser'),
    "file-chooser2": builder.get_object('file-chooser2'),
    "create-folder":builder.get_object("create-folder"),

    "prog-rev": builder.get_object('prog-rev'),
    "line-lab": builder.get_object('line-label'),
    "col-lab": builder.get_object('col-label'),
    "folder-tree":builder.get_object("folder-tree"),
    "s-list": Gtk.ListStore(str),
    "folder-menu":Gtk.Menu(),
    "pref": builder.get_object("Preferences"),
    "s-popup": builder.get_object('popup'),
    "s-view": builder.get_object('ccc'),
    "close-popup": builder.get_object("close-unsaved"),
    "doc-win": builder.get_object('doc-win'),
    "save-close-btn": builder.get_object('save-close-btn'),
    "doc-box": builder.get_object('doc-box'),
    "webview": WebKit2.WebView(),
    "f-bar-rev":builder.get_object('f-bar-rev'),
    "f-o-list":builder.get_object('files-opened-listbox'),
    "n-menu":Gtk.Menu(),
    "f-exists-p":builder.get_object("f-exists-popup"),
    "f-label":builder.get_object("f-info-lab"),
    "treestore":Gtk.TreeStore(str, str),
    "f-chooser":builder.get_object("folder-chooser"),
    "d-popup":builder.get_object("delete-popup"),
    "t-rev":builder.get_object("t-rev"),
    "t-notebook":builder.get_object("t-notebook"),
    "settings": {
        "font": "sans 12",
        "font-size": 12,
        "format_on_save": False,
        "auto-save-delay": 0,
        "auto-save": False,
        'closing-b': True,
        "closing-q": True
    }
}
folder_open = None

css = Gtk.CssProvider()
css.load_from_path('./custom_theme.css')
screen = Gdk.Display.get_default_screen(Gdk.Display.get_default())
Gtk.StyleContext().add_provider_for_screen(screen, css, 600)
# Handler


class Handler:
    def __init__(self):
        self.pulse = 0
        self.about = content['about']
        content['doc-box'].pack_start(content['webview'], True, True, 0)
        self.file_chooser = content['file-chooser']
        self.file_save = content['file-chooser2']
        self.open_rev = Gtk.Image()
        self.open_rev.set_from_icon_name("go-next",Gtk.IconSize.MENU)
        self.close_rev = Gtk.Image()
        self.close_rev.set_from_icon_name('go-previous',Gtk.IconSize.MENU)
        self.ipy_lab = Gtk.Label(label="IPython")
        self.ipy = Vte.Terminal()
        self.ipy.spawn_async(Vte.PtyFlags.DEFAULT,
            os.environ["HOME"],
            ["/bin/sh"],
            None,
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,None, -1,
            None,None)
        self.python3_t = Vte.Terminal()
        self.python3_t.spawn_async(Vte.PtyFlags.DEFAULT,
            os.environ["HOME"],
            ["/bin/sh"],
            None,
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,None, -1,
            None,None)
        builder.get_object("ipycont").add(self.python3_t)

        _hh = Gtk.ScrolledWindow()
        _hh.add(self.ipy)
        content['t-notebook'].append_page(_hh, self.ipy_lab)

        #self.ipy.feed_child(bytes("ipython \n", "utf-8"))
        #self.ipy.feed_child_binary(bytes("ipython\r\n", 'utf-8'))
        self.about.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK
        )
        content['create-folder'].add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK
        )
        self.terminal = Vte.Terminal()
        self.terminal.spawn_async(Vte.PtyFlags.DEFAULT,
            os.environ["HOME"],
            ["/bin/bash"],
            None,
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,None, -1,
            None,None
        )
        cc = Gdk.RGBA()
        cc.parse("rgb(24, 24, 24)")
        self.terminal.set_color_background(cc)
        content["t-box"].add(self.terminal)
        self.f_chooser = content['f-chooser']
        self.f_chooser.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK
        )
        content['folder-tree'].set_model(content['treestore'])
        self.file_chooser.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK
        )
        content['file-chooser2'].add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE,
            Gtk.ResponseType.ACCEPT
        )
        self.menu = content["n-menu"]
        sugg_cell = Gtk.CellRendererText()
        pic_cell = Gtk.CellRendererPixbuf()
        sugg_col = Gtk.TreeViewColumn("")
        sugg_col.pack_start(pic_cell,False)
        sugg_col.pack_start(sugg_cell,True)
        content['folder-tree'].append_column(sugg_col)
        sugg_col.set_cell_data_func(pic_cell, self.pixcellprop )
        sugg_col.add_attribute(sugg_cell,"text", 1)
        self.foldercolumn = sugg_cell
        sugg_cell.connect("edited",self.f_cell_edited)
        sugg_cell.connect("editing-canceled",self.f_cell_edited)

        content['folder-tree'].show()
        for i in menu_items:
          if i == "<hr>":
            self.menu.append(Gtk.SeparatorMenuItem())
            #del menu_items[menu_items.index(i)-1]
            continue
          mitem = Gtk.MenuItem(label=i)
          self.menu.append(mitem)
          self.menu.show_all()
          mitem.connect("activate", self.on_n_menu)
        for i in folder_menu:
            if i == "<hr>":
                content['folder-menu'].append(Gtk.SeparatorMenuItem())
                #del folder_menu[folder_menu.index(i)-1]
                continue
            mitem = Gtk.MenuItem(label=i)
            content['folder-menu'].append(mitem)
            mitem.connect("activate",self.foldermenu)
        self.foldercell = False
        content['folder-menu'].show_all()
        liststore = content['s-list']
        list_view = content['s-view']
        sugg_cell = Gtk.CellRendererText()
        sugg_col = Gtk.TreeViewColumn(' Sugggestion', sugg_cell, text=0)
        list_view.set_model(liststore)
        list_view.append_column(sugg_col)
        scheme = GtkSource.StyleSchemeManager()
        scheme.append_search_path("./Data")
        self.scheme = scheme.get_scheme("default")
    
    def run_file(self, *args):
        c = content['notebook'].get_current_page()
        f = content['temp']["files_opened"][c]
        content["t-rev"].set_reveal_child(True)
        content["t-notebook"].set_current_page(0)
        self.terminal.feed_child(bytes("/bin/python3 "+f+"\n","utf-8"))

    def foldermenu(self,*args):
        fun_dict = [self.new_file,self.new_folder, None, None, None, self.copy_path,None,self.rename,self.delete]
        fdict = {}
        for i in folder_menu:
            fdict[i] = fun_dict[folder_menu.index(i)]
        fdict[args[0].get_label()]()
    
    def new_file(self, b=False):
        if b:
            new_page(content)
            content["notebook"].show_all()
            self.save_cb()
            return
        store = content['folder-tree']
        curcur = store.get_cursor()
        sellection = store.get_selection().get_selected_rows()
        model, pathlist = sellection
        val = ''
        if len(pathlist) > 0:
            for p in pathlist:
                tree = model.get_iter(p)
                val = model.get_value(tree, 1)
                stree = model.get_string_from_iter(tree)
            if content["treestore"][stree][0] == "folder":
                pass
            elif len(stree) == 1:
                stree = None
            else:
                if stree.find(":") == -1:
                    stree=None
                else:
                    stree = stree[:stree.rindex(":")]

            if stree is not None:stree = model.get_iter_from_string(stree)
        else : 
            stree = None

        self.foldercolumn.set_property("editable", True)
        it = content['treestore'].append(stree,["",''])
        if stree is not None:
            store.expand_row(model.get_path(stree), True)
        last = content['treestore'].iter_n_children()-1
        store.get_selection().select_path(model.get_path(it))
        curcur = store.get_cursor()

        store.grab_focus()
        store.set_cursor(model.get_path(it))
        curcur = store.get_cursor()
        store.set_cursor(curcur[0],curcur[1],True)

    def new_folder(self):
        store = content['folder-tree']
        curcur = store.get_cursor()
        sellection = store.get_selection().get_selected_rows()
        model, pathlist = sellection
        val = ''
        if len(pathlist) > 0:
            for p in pathlist:
                tree = model.get_iter(p)
                val = model.get_value(tree, 1)
                stree = model.get_string_from_iter(tree)
            if content["treestore"][stree][0] == "folder":
                pass
            elif len(stree) == 1:
                stree = None
            else:
                stree=stree[:stree.rindex(":")]

            if stree is not None:stree = model.get_iter_from_string(stree)
        else : 
            stree = None

        self.foldercolumn.set_property("editable", True)
        it = content['treestore'].append(stree,["folder",''])
        if stree is not None:
            store.expand_row(model.get_path(stree), True)
        last = content['treestore'].iter_n_children()-1
        store.get_selection().select_path(model.get_path(it))
        curcur = store.get_cursor()
        store.grab_focus()
        store.set_cursor(model.get_path(it))
        curcur = store.get_cursor()
        store.set_cursor(curcur[0],curcur[1],True)

    def rename(self,*args):
        store = content['folder-tree']
        curcur = store.get_cursor()
        sellection = store.get_selection().get_selected_rows()
        model, pathlist = sellection
        val = ''
        for p in pathlist:
            tree = model.get_iter(p)
            val = model.get_value(tree, 1)
        self.foldercolumn.set_property("editable", True)
        store.set_cursor(p,curcur[1],True)

    def delete(self,*args):
        store = content['folder-tree']
        sellection = store.get_selection().get_selected_rows()
        model, pathlist = sellection
        val = ''
        for p in pathlist:
            tree = model.get_iter(p)
            val = model.get_value(tree, 1)
        curr = content['notebook'].get_current_page()

        iters = store.get_cursor()[0].to_string().split(":")

        name = ""
        it_p = ""
        for i, x in enumerate(iters,0):
            if i != 0:
                it_p = it_p + ":" + iters[i]

            else:it_p = x
            it = content['folder-tree'].get_model().get_iter(it_p)
            name = name+ "/" + content['folder-tree'].get_model().get_value(it, 1)

        fld = folder_open+name
        lab = content['d-popup'].get_children()[0]\
            .get_children()[0]\
            .get_children()[1]\
            .get_children()[0]
        lab.set_markup(delete_popup_text.format(name[1:]))
        response = content['d-popup'].run()

        content['d-popup'].hide()
        if response == Gtk.ResponseType.YES:
            t = deltime.now().timetuple()
            trdir = "/home/{}/.local/share/Trash/files".format(USRNAME)
            trdatdir = "/home/{}/.local/share/Trash/info".format(USRNAME)
            info = """[Trash Info]\npath={}\nDeletionDate={}
            """
            time = "{0}-{1}-{2}T{hr}:{min}:{sec}".format(t[0],t[1],t[2],hr=t[3],min=t[4],sec=t[5])
            info = info.format(fld,time)
            with open(trdatdir+fld.split("/")[-1],"w") as ddat:
                ddat.write(info)
            try:
               move(fld, trdir)
            except shutil.Error:
                try:
                    os.remove(fld)
                except IsADirectoryError:
                    os.rmdir(fld)
            content['treestore'].remove(tree)
            if fld in content['temp']['files_opened']:
                content['temp']['tab-label'][content['temp']['files_opened'].index(fld)].set_label(\
                    content['temp']['tab-label'][content['temp']['files_opened'].index(fld)].get_label()+' [deleted]')

    def copy_path(self):
        store = content['folder-tree']
        sellection = store.get_selection().get_selected_rows()
        model, pathlist = sellection
        iters = store.get_cursor()[0].to_string().split(":")
        val = ''
        for p in pathlist:
            tree = model.get_iter(p)
            val = model.get_value(tree, 1)

        name = ""
        it_p = ""
        for i, x in enumerate(iters,0):
            if i != 0:
                it_p = it_p + ":" + iters[i]

            else:it_p = x
            it = content['folder-tree'].get_model().get_iter(it_p)
            name = name+ "/" + content['folder-tree'].get_model().get_value(it, 1)

        curr = content['notebook'].get_current_page()
        tv = content['temp']['text_views'][curr]
        clipboard = tv.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(folder_open+name,-1)

    def _pulse_p_bar(self, *args):
        content['p_bar'].pulse()
        if self.pulse == 120 and len(args) == 0:
            self.pulse += 1
            content['p_bar'].set_fraction(0.0)
            self.pulse = 0
            return False
        return True

    def on_new_cb(self, *args, **kwargs):
        GLib.idle_add(new_page, content)

    def save_cb(self, *args, **kwargs):
        content["prog-rev"].set_reveal_child(True)
        current = int(content['notebook'].get_current_page())
        if not os.path.isfile(content['temp']['files_opened'][current]):
            _t = GLib.timeout_add(10, self._pulse_p_bar, 1)
            self.file_save.run()
            self.file_save.hide()
            if self.file_save.get_uri() is not None:
                file_name = self.file_save.get_filename()
                save_as(file_name, current, content)
            GLib.source_remove(_t)
            content['p_bar'].set_fraction(0.0)
        else:
            _t = GLib.timeout_add(10, self._pulse_p_bar, 0)
            save(current, content)
        content["prog-rev"].set_reveal_child(False)
        self._open_folder(folder_open)

    def save_as(self, *args, current=None):
        content["prog-rev"].set_reveal_child(True)
        _t = GLib.timeout_add(10, self._pulse_p_bar, 1)
        if current is None:
            current = int(content['notebook'].get_current_page())
        self.file_save.run()
        self.file_save.hide()
        if self.file_save.get_uri() is not None:
            file_name = self.file_save.get_filename()
            save_as(file_name, current, content)
        GLib.source_remove(_t)
        content["prog-rev"].set_reveal_child(False)
        content['p_bar'].set_fraction(0.0)
        self._open_folder(folder_open)

    def on_about_cb(self, btn, *args):
        content['about'].run()
        content['about'].hide()

    def on_menu(self, btn, *args):
        content['menu-popup'].popup()

    def on_open_cb(self, *args):
        response = self.file_chooser.run()
        if response == Gtk.ResponseType.OK:
            file_name = self.file_chooser.get_filename()
            new_page(content, file_name)
        self.file_chooser.hide()

    def set_font(self, font: str):
        font = Pango.FontDescription(font)
        for i in content['line-label']:
            i.modify_font(font)
        for i in content['temp']['text_views']:
            i.modify_font(font)

    def page_removed_cb(self, *args):
        for i in content['temp'].keys():
            del content['temp'][i][args[-1]]

        if content['notebook'].get_n_pages() < 2:
            content['notebook'].set_show_tabs(False)
        listbox = content["f-o-list"]
        listbox_items = listbox.get_children()
        curr = content['notebook'].get_current_page()
        try:
          listbox.remove(listbox_items[args[-1]])
        except IndexError:
          pass
        try:
            fn = content["temp"]['files_opened'][curr].split("/")[-1]
            content['header_bar'].set_title(f"{fn} - PyEdit ")
        except:
            pass

    def page_added_cb(self, *args):
        if args[-1] == 0:
            content['notebook'].set_show_tabs(False)
        else:
            content['notebook'].set_show_tabs(True)
        #Create file box and put in filesopened
        b1 = Gtk.VBox()
        b2 = Gtk.Box()
        img = Gtk.Image()
        lab = Gtk.Label()
        listbox = content["f-o-list"]
        file = content['temp']['files_opened'][args[-1]]
        if file is not None:
            filen = content['temp']['files_opened'][args[-1]].split("/")[-1]
            mimeico = Gio.content_type_guess(filen,data=None)[0]
            mimeico = Gio.content_type_get_icon(mimeico)
        else:
            pass
        img.set_from_gicon(mimeico, Gtk.IconSize.MENU)
        lab.set_text(filen)
        b2.pack_start(img,False,False,0)
        b2.set_spacing(5)
        b2.add(lab)
        b2.set_tooltip_text(file)
        b1.add(b2)
        b2.show_all()
        b1.show_all()
        listbox.add(b1)
        listbox.show()
        args[1].get_children()[0].get_buffer().set_style_scheme(self.scheme)
        try:
            if folder_open is not None:
                self._open_folder(folder_open)
        except Exception as e:
            print("[Error] ::",e)
    
    def f_list_row_selected(self,listbox,listboxrow,*args):
      l_of_children = listboxrow.get_children()[0].get_children()[0].get_children()[1].get_text()
      f = None
      for i in content['temp']['files_opened']:
        k=False
        for j in i.split("/"):
          if j == l_of_children:
            k = True
            f = content['temp']['files_opened'].index(i)
            break 
        if k:break
      content['notebook'].set_current_page(f)

    def page_changed(self, notebook, page, num, *args):
        if num != -1:
            fn = content["temp"]['files_opened'][num].split("/")[-1]
        content['header_bar'].set_title(f"{fn} - PyEdit")

    def reordered_cb(self, *args):
        prev_page = content['notebook'].get_current_page()-1
        to_page = args[-1]
        for i in content['temp'].keys():
            temp = content['temp'][i][prev_page]
            content['temp'][i][prev_page] = content['temp'][i][to_page]
            content['temp'][i][to_page] = temp
        modify(to_page, prev_page)

    def s_selected(self, *args):
        cur = content['notebook'].get_current_page()
        buff = content['temp']['text_buffers'][cur]
        sellection = args[0].get_selection().get_selected_rows()
        model, pathlist = sellection
        val = ''
        for p in pathlist:
            tree = model.get_iter(p)
            val = model.get_value(tree, 0)
        text = buff.get_insert()
        start_it = buff.get_start_iter()
        text = str(buff.get_text(start_it, buff.get_iter_at_mark(text), False))
        sp1 = text.split(' ')[-1].split('.')
        if sp1[-1] in ["\'", "\""]:
            sp1 = sp1[:len(sp1-1)]
        if len(sp1) > 2:
            sp1 = "".join(sp1[1:])
            com = "".join(val.split(sp1))
        else:
            com = val
        if len(com) == len(val):
            it1 = buff.get_iter_at_mark(buff.get_insert())
            it2 = buff.get_iter_at_mark(buff.get_insert())
            lin = it1.get_line()
            while 1:
                _k = it1.backward_char()
                if not _k:
                    break
                #if sp1[-1] == it1.get_char():
                #    break
                if it1.get_line() < lin:
                    it1.forward_char()
                    break
                if it1.get_char().isspace():
                    it1.forward_char()
                    break
                if '\n' in list(it1.get_char()):
                    it1.forward_char()
                    break
                if it1.get_char() != "_" and it1.get_char().isalnum() is False:
                    it1.forward_char()
                    break
            buff.delete(it1, it2)
        buff.insert_at_cursor(com)
        content['temp']['text_views'][content['notebook'].get_current_page()].grab_focus()
        content['s-popup'].hide()

    def s_focus_out(self, *args):
        content['temp']['text_views'][content['notebook'].get_current_page()
                                      ].grab_focus()
        content['s-popup'].hide()

    def s_key_press(self, widget, event, *user_data):
        """Connect or catch only arrow keys if any other, send 
        focus to main textview widget"""
        key = Gdk.keyval_name(event.keyval)
        if key not in ['Down', 'Up', 'Return']:
            content['temp']['text_views'][content['notebook'].get_current_page()
                                          ].grab_focus()
            content['s-popup'].hide()
            return True

    def quit(self, window, *args):
        def_lab = 'Save changes to file "{}" before closing'
        lab = content["close-popup"]\
            .get_children()[0]\
            .get_children()[0]\
            .get_children()[1]\
            .get_children()[0]
        if content['temp']['modified'].count(True) > 1:
            content["save-close-btn"].set_label("Save all")
            lab.set_text(def_lab.replace('to file \"{}\"', "to all files"))
        elif content['temp']['modified'].count(True) == 1:
            ind = content['temp']['modified'].index(True)
            fn = content["temp"]['files_opened'][ind].split("/")[-1]
            lab.set_text(def_lab.format(fn).replace('to file \"', "to \""))
        if True in content['temp']['modified']:
            response = content['close-popup'].run()
            content['close-popup'].hide()
            if response == 0:
                pass
            elif response == 1:
                return True
            elif response == 2:
                self.save_all()
        with open("./Data/settings.json", 'w') as f:
            content['settings']['opened'] = [
                i for i in content['temp']['files_opened'] if os.path.isfile(i)]
            _cache_folder = "/"+os.path.abspath('Data/__cache__/cached.json')
            _c_obj = {}
            for i in content['temp']['files_opened']:
                ind = content['temp']['files_opened'].index(i)
                if not os.path.isfile(i):
                    _c_obj[i] = content['temp']['text_buffers'][ind].get_text(
                        content['temp']['text_buffers'][ind].get_start_iter(),
                        content['temp']['text_buffers'][ind].get_end_iter(), True)
            with open(_cache_folder, 'w') as o:
                o.write(dumps(_c_obj, indent=2))
            f.write(dumps(content['settings'], indent=2))
        Gtk.main_quit()

    def show(self, window, *args):
        fdat = None
        with open("./Data/settings.json", 'r') as f:
            fdat = f.read()
        try:
            content['settings'] = loads(fdat)
            if len(content['settings']['opened']) != 0:
                for i in content['settings']['opened']:
                    new_page(content, i)
            else:
                self.on_new_cb()
            if content['settings']['folder-open'] is not None and\
                 os.path.isdir(content['settings']['folder-open']):
                self._open_folder(content['settings']['folder-open'])
                self.terminal.spawn_async(Vte.PtyFlags.DEFAULT,
                    content['settings']['folder-open'],
                    ["/bin/bash"],
                    None,
                    GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                    None,None, -1,
                    None,None
                )
        except Exception as e:
            print(e)
            self.on_new_cb()
        GLib.timeout_add_seconds(1, self._set_terms)
        return False

    def _set_terms(self,  *args):
        self.ipy.feed_child(bytes("ipython\n", "utf-8"))
        self.python3_t.feed_child(bytes("python3\n", "utf-8"))

    def win_key_released(self, window, event, *args):
        key = Gdk.keyval_name(event.keyval)
        ctrl = (event.state & Gdk.ModifierType.CONTROL_MASK)
        if ctrl and key == "s":
            self.save_cb()
        elif ctrl and key == "o":
            self.on_open_cb()
        elif ctrl and key == "n":
            self.on_new_cb()

    def save_all(self, *args):
        for i in range(0, len(content['temp']['files_opened'])):
            if os.path.isfile(content['temp']['files_opened'][i]):
                save(i, content)
            else:
                self.save_as(current=i)
    
    def _format_doc(self,*curr):
      curr = content['notebook'].get_current_page()
      st = content['temp']['text_buffers'][curr].get_start_iter()
      en = content['temp']['text_buffers'][curr].get_end_iter()
      text=content['temp']['text_buffers'][curr].get_text(st,en,False)
      text = fix_code(text)
      content['temp']['text_buffers'][curr].set_text(text)

    def rev_file_bar(self,*args):
      rev = not content['f-bar-rev'].get_reveal_child()
      content['f-bar-rev'].set_reveal_child(rev)
      if not rev:
        builder.get_object("rev-btn").set_image(self.open_rev)
      else:builder.get_object("rev-btn").set_image(self.close_rev)

    def _open_folder(self,folder,*args):
        global folder_open
        folder_open = folder
        ff = folder
        folder = os.walk(folder)
        parent = {}
        treestore = content['treestore']
        treestore.clear()
        #content['f-bar-rev'].set_reveal_child(True)
        content['settings']['folder-open'] = ff
        content['folder-tree'].get_column(0).set_title(ff.split("/")[-1])
        for (path,dirs,files) in folder:
            treestore = content['treestore']
            for sbdir in dirs:
                parent[os.path.join(path,sbdir)] = treestore.append(parent.get(path,None), ["folder",\
                        sbdir])
            for item in files:
                mod = content['folder-tree'].get_model()
                mimeico = Gio.content_type_guess(item,data=None)[0]
                treestore.append(parent.get(path,None), [mimeico,item])

    def pixcellprop(self, col, cell, mod, it, *args):
        try:
          val = mod.get_value(it,0).replace("/","-")
          icon = get_f_img(val, mod, it)
          cell.set_property("pixbuf", icon)
        except Exception as e:
            return 

    def f_cell_edited(self,*args):
        args[0].set_property("editable", False)
        if len(args) < 2:return
        if isinstance(args[1], bool):return
        isfile = False
        rn = False
        iters = args[1].split(":")
        name = ""
        it_p = ""
        for i, x in enumerate(iters,0):
            if i != 0:
                it_p = it_p + ":" + iters[i]

            else:it_p = x
            it = content['folder-tree'].get_model().get_iter(it_p)
            name = name+ "/" + content['folder-tree'].get_model().get_value(it, 1)
        name1 = name
        rn = True

        iters = args[1].split(":")

        if content["treestore"][args[1]][1] == "" and content["treestore"][args[1]][1] != args[2] and content['treestore'][args[1]][0] != 'folder':
            content["treestore"][args[1]][1] = args[2]
            isfile = True

        elif content['treestore'][args[1]][0] == "folder":
            content['treestore'][args[1]][1] = args[2]
            iters = args[1].split(":")
            name = ""
            it_p = ""
            for i, x in enumerate(iters,0):
                if i != 0:
                    it_p = it_p + ":" + iters[i]
    
                else:it_p = x
                it = content['folder-tree'].get_model().get_iter(it_p)
                name = name+ "/" + content['folder-tree'].get_model().get_value(it, 1)
            name2 = name
            try:
                os.mkdir(folder_open+name2)
            except FileExistsError as e:
                content['f-label'].set_text(e)


        elif content["treestore"][args[1]][1] != args[2]:
            mimeico = Gio.content_type_guess(args[2],data=None)[0].replace('/',"-")
            content["treestore"][args[1]][0] = mimeico
            content["treestore"][args[1]][1] = args[2]
            iters = args[1].split(":")
            name = ""
            it_p = ""
            for i, x in enumerate(iters,0):
                if i != 0:
                    it_p = it_p + ":" + iters[i]
    
                else:it_p = x
                it = content['folder-tree'].get_model().get_iter(it_p)
                name = name+ "/" + content['folder-tree'].get_model().get_value(it, 1)
            name2 = name
            try:
                content['temp']["files_opened"][content['temp']['files_opened'].index(folder_open+name1)] = folder_open+name2
            except ValueError:
                pass
            os.rename(folder_open+name1, folder_open+name2)

        elif content['treestore'][args[1]][1] == args[2]:pass
        else:
            it = content['folder-tree'].get_model().get_iter(args[1])
            content['treestore'].remove(it)

        self.foldercolumn = args[0]
        iters = args[1].split(":")
        name = ""
        it_p = ""
        for i, x in enumerate(iters,0):
            if i != 0:
                it_p = it_p + ":" + iters[i]

            else:it_p = x
            it = content['folder-tree'].get_model().get_iter(it_p)
            name = name+ "/" + content['folder-tree'].get_model().get_value(it, 1)
        if isfile:
            if os.path.isfile(folder_open+name):
                res = content['f-exists-p'].run()
                content['f-exists-p'].hide()
                if res != Gtk.ResponseType.CANCEL:
                    with open(folder_open+name,"w"):pass
            else:
                with open(folder_open+name,"w"):pass

        self._open_folder(folder_open)

    def open_folder(self,*args):
        global folder_open
        fil = self.f_chooser.run()
        self.f_chooser.hide()
        if fil == Gtk.ResponseType.OK:
            fil = self.f_chooser.get_filename()
            folder_open = fil
            self._open_folder(fil)
            content['f-bar-rev'].set_reveal_child(True)
            self.terminal.feed_child(bytes(f"cd {fil}\rclear\r", "utf-8"))

    def create_folder(self, *args):
        fpopup = content['create-folder']
        res = fpopup.run()
        fpopup.hide()

    def on_n_menu(self, *args):
      comm = [self.on_new_cb, self.on_open_cb, self.new_file,self.create_folder, self.open_folder, None, self.save_cb, self.run_file,self._format_doc]
      cdict = {}
      for m in menu_items:
        if m != "<hr>":
          cdict[m] = comm[menu_items.index(m)]
      if cdict[args[0].get_label()] == comm[2] :
          cdict[args[0].get_label()](b=True)
          return
      cdict[args[0].get_label()](args[0])
    
    def folder_row(self,*args):
        store = content['folder-tree']
        sellection = store.get_selection().get_selected_rows()
        model, pathlist = sellection
        iters = store.get_cursor()[0].to_string().split(":")
        val = ''
        for p in pathlist:
            tree = model.get_iter(p)
            val = model.get_value(tree, 1)
        name = ""
        it_p = ""
        for i, x in enumerate(iters,0):
            if i != 0:
                it_p = it_p + ":" + iters[i]

            else:it_p = x
            it = content['folder-tree'].get_model().get_iter(it_p)
            name = name+ "/" + content['folder-tree'].get_model().get_value(it, 1)

        curr = content['notebook'].get_current_page()
        tv = content['temp']['text_views'][curr]
        fld = folder_open+name
        if os.path.isfile(fld): new_page(content, fld)

    def folder_area(self,*args):
        if args[1].button == 3:
            content['folder-menu'].popup(None,None,None,None,args[1].button,args[1].time)
    
    def tips_tricks(self, *args):
        cur = ["notebook"].get_current_page()
        content['temp']['text_buffers'][cur].scroll_to_iter(content['temp']['text_buffers'][cur].get_end_iter())

    def problems_btn(self, *btn):
        content['t-rev'].set_reveal_child(not content['t-rev'].get_reveal_child())

    def s_create_backup_file(self, *btn):
        content['settings']["create_b_file"] = btn[0].get_active()
    
    def on_settings_cb(self, *btn):
        content['pref'].show()
    def pref_closed_cb(Self, *args):
        content['pref'].hide()
        return True
    def win_state_changed(self, *args):
        self._open_folder(folder_open)
    #"Settings Handlers"
    def font_changed_cb(self, *args):
        fnt = str(args[0].get_font())
        content['settings']['font'] = fnt
        change_font(content, fnt)
        
if __name__ == '__main__':
    win = content['window']
    builder.connect_signals(Handler())
    win.show_all()
    Gtk.main()