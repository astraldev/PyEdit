#!bin/env python3

import re
from autopep8 import fix_code
from pyedit.PyEditxN import new_page, modify, save, save_as, change_font, get_f_img, set_content, is_app
from datetime import datetime as deltime
from json import dumps, loads
import gi
import shutil
import getpass
from shutil import move
import os
import asyncio
gi.require_version("GtkSource", "4")
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Gdk, GLib, WebKit2, Pango, Gio, Vte, GtkSource

USRNAME = getpass.getuser()
AUTOSAVE_ID = None
DIREC = f"/home/{USRNAME}/.local/share"
CACHE = f"/home/{USRNAME}/.pyedit"
USR_REPLACE = False
if not os.path.exists(CACHE):
    os.mkdir(CACHE)
builder = Gtk.Builder()
builder.add_from_file(f'{DIREC}/PyEdit/Data/ui.ui')

menu_items = ["New page", "Open File", "New file", "Create folder",
              "Open folder", "<hr>", "Copy", "Cut", "Paste", "<hr>", "Save", "Run file", "Format document"]

folder_menu = ["New file", "New folder", "Open Folder", "<hr>",
               "Copy path", "Copy relative path", "<hr>", "Rename", "Delete"]

delete_popup_text = "Are you sure you want to delete <b>{}</b> "
pages = []
content = {
    "c-dir": CACHE,
    "temp": {
        'text_buffers': [],
        "files_opened": [],
        'text_views': [],
        "modified": [],
        "tab-label": [],
        "mime-types": []
    },
    'window': builder.get_object('Window'),
    'about': builder.get_object('About'),
    'header_bar': builder.get_object('header-bar'),
    "t-box": builder.get_object("t-box"),
    'notebook': builder.get_object('Notebook'),
    'p_bar': builder.get_object('save-progress'),

    'menu-popup': builder.get_object('menu-popup'),
    'file-chooser': builder.get_object('file-chooser'),
    "file-chooser2": builder.get_object('file-chooser2'),
    "create-folder": builder.get_object("create-folder"),

    "prog-rev": builder.get_object('prog-rev'),
    "line-lab": builder.get_object('line-label'),
    "col-lab": builder.get_object('col-label'),
    "folder-tree": builder.get_object("folder-tree"),
    "s-list": Gtk.ListStore(str),
    "folder-menu": Gtk.Menu(),
    "pref": builder.get_object("Preferences"),
    "s-popup": builder.get_object('popup'),
    "s-view": builder.get_object('ccc'),
    "close-popup": builder.get_object("close-unsaved"),
    "doc-win": builder.get_object('doc-win'),
    "save-close-btn": builder.get_object('save-close-btn'),
    "doc-box": builder.get_object('doc-box'),
    "webview": WebKit2.WebView(),
    "f-bar-rev": builder.get_object('f-bar-rev'),
    "f-o-list": builder.get_object('files-opened-listbox'),
    "n-menu": Gtk.Menu(),
    "f-exists-p": builder.get_object("f-exists-popup"),
    "f-label": builder.get_object("f-info-lab"),
    "treestore": Gtk.TreeStore(str, str),
    "f-chooser": builder.get_object("folder-chooser"),
    "d-popup": builder.get_object("delete-popup"),
    "t-rev": builder.get_object("t-rev"),
    "t-notebook": builder.get_object("t-notebook"),
    "search-bar": builder.get_object("search-bar"),
    "line-entry": builder.get_object("line-entry"),
    "extc": builder.get_object("extc"),
    "extc_list": Gtk.ListStore(str, str),
    "folder_menu_items_dict": {
        0: None,
        1: None,
        2: None,
        3: None,
        4: None,
        5: None,
        6: None
    },
    "menu_items_dict": {
        0: None,
        1: None,
        2: None,
        3: None,
        4: None,
        5: None,
        6: None,
        7: None,
        8: None,
        9: None,
        10: None,
        11: None,
        12: None
    },
    "buttons": {
        "auto-save-btn": builder.get_object("auto-save-btn"),
        "auto-save-box": builder.get_object("auto-save-content"),
        "auto-save-delay": builder.get_object("auto-save-delay"),
        "format-on_save-btn": builder.get_object("format_on_save"),
        "save-timer": builder.get_object("save-delay"),
        "tab-btn": builder.get_object("tab-length"),
        "font-btn": builder.get_object("font-family"),
        "font-size-btn": builder.get_object("fnt-s-btn")

    },
    "settings": {
        "font": "Sahadeva 16",
        "font-size": 16,
        "format_on_save": False,
        "auto-save-delay": 0,
        "save-delay": "seconds",
        "auto-save": False,
        'closing-b': True,
        "closing-q": True,
        "tab-length": 4,
        "opened": [],
        "folder-open": "",
        "sugg-style": "mild",
        "create_b_file": False,
        "maximized": False,
        "interpreter": "python3.7",
        "extc": [[".py", "/bin/env python3 ${filename}"], [".js", "node ${filename}"]]
    }
}
folder_open = None

css = Gtk.CssProvider()
css.load_from_path(f'{DIREC}/PyEdit/Data/custom_theme.css')
screen = Gdk.Display.get_default_screen(Gdk.Display.get_default())
Gtk.StyleContext().add_provider_for_screen(screen, css, 600)
# Handler


class Handler:
    async def loader(self, *args):
        self.pulse = 0
        self.window = content['window']
        self.about = content['about']
        content['doc-box'].pack_start(content['webview'], True, True, 0)
        self.file_chooser = content['file-chooser']
        self.file_save = content['file-chooser2']
        self.open_rev = Gtk.Image()
        self.open_rev.set_from_icon_name("go-next", Gtk.IconSize.MENU)
        self.close_rev = Gtk.Image()
        self.close_rev.set_from_icon_name('go-previous', Gtk.IconSize.MENU)
        self.ipy_lab = Gtk.Label(label="IPython")

        cc = Gdk.RGBA()
        cc.parse("rgb(24, 24, 24)")

        self.python3_t = Vte.Terminal()
        self.python3_t.spawn_async(Vte.PtyFlags.DEFAULT,
                                   os.environ["HOME"],
                                   ["/bin/sh"],
                                   None,
                                   GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                   None, None, -1,
                                   None, None)
        self.python3_t.set_color_background(cc.copy())

        builder.get_object("ipycont").add(self.python3_t)
        if is_app("ipython"):
            self.ipy = Vte.Terminal()
            self.ipy.spawn_async(Vte.PtyFlags.DEFAULT,
                                 os.environ["HOME"],
                                 ["/bin/sh"],
                                 None,
                                 GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                 None, None, -1,
                                 None, None)
            self.ipy.set_color_background(cc.copy())
            _hh = Gtk.ScrolledWindow()
            _hh.add(self.ipy)
            content['t-notebook'].append_page(_hh, self.ipy_lab)

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
                                  None, None, -1,
                                  None, None
                                  )

        self.terminal.set_color_background(cc.copy())
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
        sugg_col.pack_start(pic_cell, False)
        sugg_col.pack_start(sugg_cell, True)
        content['folder-tree'].append_column(sugg_col)
        content['folder-tree'].set_headers_visible(False)
        sugg_col.set_cell_data_func(pic_cell, self.pixcellprop)
        sugg_col.add_attribute(sugg_cell, "text", 1)
        self.foldercolumn = sugg_cell
        sugg_cell.connect("edited", self.f_cell_edited)
        sugg_cell.connect("editing-canceled", self.f_cell_edited)
        content['extc'].set_model(content['extc_list'])

        for extc in content['settings']['extc']:
            content['extc_list'].append([extc[0], extc[1]])
        renderer = Gtk.CellRendererText()
        renderer.set_property("editable", True)
        renderer.connect("edited", self.extension_edited)
        column = Gtk.TreeViewColumn("Extension", renderer, text=0)
        content['extc'].append_column(column)
        renderer = Gtk.CellRendererText()
        renderer.set_property("editable", True)
        renderer.connect("edited", self.command_edited)
        column = Gtk.TreeViewColumn("Command", renderer, text=1)
        content['extc'].append_column(column)

        content['folder-tree'].show()
        m = []
        for i in menu_items:
            if i == "<hr>":
                self.menu.append(Gtk.SeparatorMenuItem())
                continue
            mitem = Gtk.MenuItem(label=i)
            self.menu.append(mitem)
            m.append(mitem)
            self.menu.show_all()
            mitem.connect("activate", self.on_n_menu)
        f = []
        for i in folder_menu:
            if i == "<hr>":
                content['folder-menu'].append(Gtk.SeparatorMenuItem())
                #del folder_menu[folder_menu.index(i)-1]
                continue
            mitem = Gtk.MenuItem(label=i)
            content['folder-menu'].append(mitem)
            f.append(mitem)
            mitem.connect("activate", self.foldermenu)
        for i, _ in enumerate(m, 0):
            content['menu_items_dict'][i] = m[i]
        for i, _ in enumerate(f, 0):
            content["folder_menu_items_dict"][i] = f[i]

        self.foldercell = False
        content['folder-menu'].show_all()
        liststore = content['s-list']
        list_view = content['s-view']
        sugg_cell = Gtk.CellRendererText()
        sugg_col = Gtk.TreeViewColumn(' Sugggestion', sugg_cell, text=0)
        list_view.set_model(liststore)
        list_view.append_column(sugg_col)
        scheme = GtkSource.StyleSchemeManager()
        scheme.append_search_path(f"{DIREC}/PyEdit/Data")
        self.scheme = scheme.get_scheme("pyedit")
        # Create run folder treeview

    def on_maximize_toggle(self, *args):
        pass

    def extension_edited(self, w, path, text):
        if text != "":
            num = content['extc_list'].iter_n_children()
            mime = [content['extc_list'][m][0] for m in range(num)]
            p = int(path)
            if text in mime:
                model = content['extc'].get_model()
                it = model.get_iter_from_string(str(p))
                path = model.get_path(it)
                c = content['extc'].get_column(1)
                content['extc'].set_cursor(path, c, True)
                return
            content['extc_list'][path][0] = text
            content['settings']["extc"][p][0] = text
            c = content['extc'].get_column(1)
            model = content['extc'].get_model()
            it = model.get_iter_from_string(str(p))
            path = model.get_path(it)
            content['extc'].set_cursor(path, c, True)

    def command_edited(self, w, path, text):
        p = int(path)
        if text != "":
            content['extc_list'][path][1] = text
            content['settings']["extc"][p][1] = text
        else:
            model = content['extc'].get_model()
            it = model.get_iter_from_string(str(p))
            path = model.get_path(it)
            content['extc_list'].remove(it)
            del content['settings']["extc"][p]

    def on_new_extc(self, *btn):
        store = content['extc']
        last = content['extc_list'].iter_n_children()-1
        it = content['extc_list'].append(["", ''])
        content['settings']['extc'].append(["", ""])
        model = store.get_model()
        store.get_selection().select_path(model.get_path(it))
        curcur = store.get_cursor()
        store.grab_focus()
        store.set_cursor(model.get_path(it))
        curcur = store.get_cursor()
        store.set_cursor(curcur[0], curcur[1], True)

    def load_show(self, *args):
        fdat = None
        try:
            with open(f"{CACHE}/settings.json", 'r') as f:
                fdat = f.read()
                content['settings'] = loads(fdat)
                try:
                    if len(content['settings']['opened']) != 0:
                        for i in content['settings']['opened']:
                            new_page(content, file=i)
                    else:
                        self.on_new_cb()
                except Exception as e:
                    self.on_new_cb()
                if content['settings']['folder-open'] is not None and\
                        os.path.isdir(content['settings']['folder-open']):
                    self._open_folder(content['settings']['folder-open'])
                    self.terminal.spawn_async(Vte.PtyFlags.DEFAULT,
                                              content['settings']['folder-open'],
                                              ["/bin/bash"],
                                              None,
                                              GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                              None, None, -1,
                                              None, None
                                              )
        except Exception as e:
            print(e)
            with open(f"{CACHE}/settings.json", "w") as f:
                t = str(content["settings"])
                f.write(t)
                content["settings"] = loads(t)
                self.on_new_cb()
                print("[INFO] New dir created, empty file opened")
                self.terminal.spawn_async(Vte.PtyFlags.DEFAULT,
                                          None,
                                          ["/bin/bash"],
                                          None,
                                          GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                          None, None, -1,
                                          None, None)

    async def load_quit(self, *args):
        def_lab = 'Save changes to file "{}" before closing'
        lab = content["close-popup"]\
            .get_children()[0]\
            .get_children()[0]\
            .get_children()[1]\
            .get_children()[0]
        modified = [x.get_modified() for x in content['temp']['text_buffers']]
        if modified.count(True) > 1:
            content["save-close-btn"].set_label("Save all")
            lab.set_text(def_lab.replace('to file \"{}\"', "to all files"))
        elif modified.count(True) == 1:
            ind = modified.index(True)
            fn = content["temp"]['files_opened'][ind].split("/")[-1]
            lab.set_text(def_lab.format(fn).replace('to file \"', "to \""))
        if True in modified:
            response = content['close-popup'].run()
            content['close-popup'].hide()
            if response == 0:
                pass
            elif response == 1:
                return True
            elif response == 2:
                self.save_all()
        with open(CACHE + "/settings.json", 'w') as f:
            content['settings']['opened'] = [
                i for i in content['temp']['files_opened'] if os.path.isfile(i)]
            _cache_folder = CACHE + "/__cache__.json"
            _c_obj = {}
            for i in content['temp']['files_opened']:
                ind = content['temp']['files_opened'].index(i)
                if not os.path.isfile(i):
                    j = content['temp']['text_views'][ind]
                    _c_obj[i] = j.get_buffer().get_text(
                        j.get_buffer().get_start_iter(),
                        j.get_buffer().get_end_iter(), True)
            with open(_cache_folder, 'w') as o:
                o.write(dumps(_c_obj, indent=2))
            f.write(dumps(content['settings'], indent=2))
        Gtk.main_quit()
        return False

    def __init__(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.loader())
        overlay = builder.get_object("N-overlay")
        find_box = builder.get_object("find-box")
        overlay.add_overlay(find_box)
        overlay.set_overlay_pass_through(find_box, True)
        self.cancel_search()
        self.window = content["window"]
        self.search_content = ()

    def run_file(self, *args):
        c = content['notebook'].get_current_page()
        f = content['temp']["files_opened"][c]
        interp = content['settings']['interpreter']
        if not is_app(interp):
            interp = "python3.7"
        content["t-rev"].set_reveal_child(True)
        content["t-notebook"].set_current_page(0)
        mime = "."+f.split("/")[-1].split(".")[-1]
        fc = []
        for i in f.split("/"):
            if re.search(r"\s+", i) is not None:
                fc.append(f"\'{i}\'")
            else:
                fc.append(i)
        f = "/".join(fc)
        d = "/".join(fc[:-1])
        comm = ""
        for extc in content['settings']["extc"]:
            if mime == extc[0]:
                comm = extc[1]
                comm = comm.replace("$", "")
                if "{dir}" in comm:
                    comm = comm.format(dir=d, filename=f)
                else:
                    comm = comm.format(filename=f)
        self.terminal.feed_child(bytes(comm+"\n", "utf-8"))
        self._open_folder(folder_open)

    def foldermenu(self, *args):
        fun_dict = [self.new_file, self.new_folder, self.open_folder, None,
                    self.copy_path, self.copy_relative_path, None, self.rename, self.delete]
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
            stree = None
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
                    stree = None
                else:
                    stree = stree[:stree.rindex(":")]

            if stree is not None:
                stree = model.get_iter_from_string(stree)
        else:
            stree = None

        self.foldercolumn.set_property("editable", True)
        it = content['treestore'].append(stree, ["", ''])
        if stree is not None:
            store.expand_row(model.get_path(stree), True)
        last = content['treestore'].iter_n_children()-1
        store.get_selection().select_path(model.get_path(it))
        curcur = store.get_cursor()

        store.grab_focus()
        store.set_cursor(model.get_path(it))
        curcur = store.get_cursor()
        store.set_cursor(curcur[0], curcur[1], True)

    def new_folder(self):
        store = content['folder-tree']
        curcur = store.get_cursor()
        sellection = store.get_selection().get_selected_rows()
        model, pathlist = sellection
        val = ''
        if len(pathlist) > 0:
            stree = None
            for p in pathlist:
                tree = model.get_iter(p)
                val = model.get_value(tree, 1)
                stree = model.get_string_from_iter(tree)
            if content["treestore"][stree][0] == "folder":
                pass
            elif len(stree) == 1:
                stree = None
            else:
                stree = stree[:stree.rindex(":")]

            if stree is not None:
                stree = model.get_iter_from_string(stree)
        else:
            stree = None

        self.foldercolumn.set_property("editable", True)
        it = content['treestore'].append(stree, ["folder", ''])
        if stree is not None:
            store.expand_row(model.get_path(stree), True)
        last = content['treestore'].iter_n_children()-1
        store.get_selection().select_path(model.get_path(it))
        curcur = store.get_cursor()
        store.grab_focus()
        store.set_cursor(model.get_path(it))
        curcur = store.get_cursor()
        store.set_cursor(curcur[0], curcur[1], True)

    def rename(self, *args):
        store = content['folder-tree']
        curcur = store.get_cursor()
        sellection = store.get_selection().get_selected_rows()
        model, pathlist = sellection
        temp = None
        for p in pathlist:
            temp = p
            tree = model.get_iter(p)
            val = model.get_value(tree, 1)
        self.foldercolumn.set_property("editable", True)
        store.set_cursor(temp, curcur[1], True)

    def delete(self, *args):
        store = content['folder-tree']
        sellection = store.get_selection().get_selected_rows()
        model, pathlist = sellection
        val = ''
        tree = None
        for p in pathlist:
            tree_ = model.get_iter(p)
            tree = tree_

        iters = store.get_cursor()[0].to_string().split(":")

        name = ""
        it_p = ""
        for i, x in enumerate(iters, 0):
            if i != 0:
                it_p = it_p + ":" + iters[i]

            else:
                it_p = x
            it = content['folder-tree'].get_model().get_iter(it_p)
            name = name + "/" + \
                content['folder-tree'].get_model().get_value(it, 1)

        fld = folder_open+name
        lab = content['d-popup'].get_children()[0]\
            .get_children()[0]\
            .get_children()[1]\
            .get_children()[0]
        lab.set_markup(delete_popup_text.format(name[1:]))

        response = content['d-popup'].run()
        content['d-popup'].hide()
        if response == Gtk.ResponseType.YES:

            content['folder-tree'].set_cursor(iters, None, False)
            tree = content['folder-tree'].get_model().get_iter(store.get_cursor()[0])
            content['treestore'].remove(tree)

            t = deltime.now().timetuple()
            trdir = "/home/{}/.local/share/Trash/files".format(USRNAME)
            trdatdir = "/home/{}/.local/share/Trash/info/".format(USRNAME)
            info = """[Trash Info]\nPath={}\nDeletionDate={}
            """
            time = "{0}-{1}-{2}T{hr}:{min}:{sec}".format(
                t[0], t[1], t[2], hr=t[3], min=t[4], sec=t[5])
            info = info.format(fld, time)
            with open(trdatdir+fld.split("/")[-1]+".trashinfo", "w") as ddat:
                ddat.write(info)
            try:
                move(fld, trdir)
            except shutil.Error:
                try:
                    os.remove(fld)
                except IsADirectoryError:
                    os.rmdir(fld)

            if fld in content['temp']['files_opened']:
                content['temp']['tab-label'][content['temp']['files_opened'].index(fld)].set_label(
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
        for i, x in enumerate(iters, 0):
            if i != 0:
                it_p = it_p + ":" + iters[i]

            else:
                it_p = x
            it = content['folder-tree'].get_model().get_iter(it_p)
            name = name + "/" + \
                content['folder-tree'].get_model().get_value(it, 1)

        curr = content['notebook'].get_current_page()
        tv = content['temp']['text_views'][curr]
        clipboard = tv.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(folder_open+name, -1)

    def copy_relative_path(self, *args):
        store = content['folder-tree']
        sellection = store.get_selection().get_selected_rows()
        model, pathlist = sellection
        for p in pathlist:
            tree_ = model.get_iter(p)
            #val = model.get_value(tree_, 1)
            tree = tree_
        curr = content['notebook'].get_current_page()

        iters = store.get_cursor()[0].to_string().split(":")

        name = ""
        it_p = ""
        for i, x in enumerate(iters, 0):
            if i != 0:
                it_p = it_p + ":" + iters[i]

            else:
                it_p = x
            it = content['folder-tree'].get_model().get_iter(it_p)
            name = name + "/" + \
                content['folder-tree'].get_model().get_value(it, 1)
        curr = content['notebook'].get_current_page()
        tv = content['temp']['text_views'][curr]
        clipboard = tv.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(f".{name}", -1)

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
            res = self.file_save.run()
            self.file_save.hide()
            print("---")
            if self.file_save.get_uri() is not None and res != -6:
                file_name = self.file_save.get_filename()
                save_as(file_name, current, content)
                content['notebook'].remove_page(
                    content['notebook'].get_current_page())
                new_page(content, file_name)
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
        res = self.file_save.run()
        self.file_save.hide()
        if self.file_save.get_uri() is not None and res != -6:
            file_name = self.file_save.get_filename()
            save_as(file_name, current, content)
            content['notebook'].remove_page(
                content['notebook'].get_current_page())
            new_page(content, file_name)
        GLib.source_remove(_t)
        content["prog-rev"].set_reveal_child(False)
        content['p_bar'].set_fraction(0.0)
        self._open_folder(folder_open)

    def on_about_cb(self, btn, *args):
        content['about'].run()
        content['about'].hide()

    def on_menu(self, btn, *args):
        content['menu-popup'].popup()
        return True

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
        fb = builder.get_object("find-box")
        for i in content['temp'].keys():
            del content['temp'][i][args[-1]]
        if content['notebook'].get_n_pages() < 2:
            content['notebook'].set_show_tabs(False)
            fb.set_margin_top(0)
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

        fb = builder.get_object("find-box")
        if args[-1] == 0:
            fb.set_margin_top(0)
            content['notebook'].set_show_tabs(False)
        else:
            fb.set_margin_top(40)
            content['notebook'].set_show_tabs(True)
        # Create file box and put in filesopened
        b1 = Gtk.VBox()
        b2 = Gtk.Box()
        img = Gtk.Image()
        lab = Gtk.Label()
        listbox = content["f-o-list"]
        file = content['temp']['files_opened'][args[-1]]
        if file is not None:
            filen = content['temp']['files_opened'][args[-1]].split("/")[-1]
            val = str(Gio.content_type_guess(filen, data=None)[0])
            mimeico = Gtk.IconTheme().get_default().choose_icon(
                Gio.content_type_get_icon(val).get_names(), 16, 0)
            if mimeico is not None:
                img.set_from_gicon(mimeico.load_icon(), Gtk.IconSize.MENU)
            else:
                Gio.content_type_get_icon(val)
            lab.set_text(filen)
            b2.pack_start(img, False, False, 0)
            b2.set_spacing(5)
            b2.add(lab)
            b2.set_tooltip_text(file)
            b1.add(b2)
            b2.show_all()
            b1.show_all()
            listbox.add(b1)
            listbox.show()
            try:
                args[1].get_children()[0].get_buffer(
                ).set_style_scheme(self.scheme)
                args[1].get_children()[0].get_buffer().create_mark("search",
                                                                   args[1].get_children()[0].get_buffer().get_start_iter(), True)
            except Exception as e:
                pass

    def f_list_row_selected(self, listbox, listboxrow, *args):
        l_of_children = listboxrow.get_children()[0].get_children()[
            0].get_children()[1].get_text()
        f = None
        for i in content['temp']['files_opened']:
            k = False
            for j in i.split("/"):
                if j == l_of_children:
                    k = True
                    f = content['temp']['files_opened'].index(i)
                    break
            if k:
                break
        content['notebook'].set_current_page(f)

    def page_changed(self, notebook, page, num, *args):
        if num != -1:
            fn = content["temp"]['files_opened'][num].split("/")[-1]
            content['header_bar'].set_title(f"{fn} - PyEdit")
        try:
            buf = page.get_children()[0].get_buffer()
            buf.create_mark("search", buf.get_start_iter(), True)
            buf.create_mark("line", buf.get_start_iter(), True)
        except Exception:
            pass

    def reordered_cb(self, *args):
        prev_page = content['notebook'].get_current_page()-1
        to_page = args[-1]
        for i in content['temp'].keys():
            temp = content['temp'][i][prev_page]
            del content['temp'][i][prev_page]
            content['temp'][i].insert(to_page, temp)
        fc = content['f-o-list'].get_children()
        cont = fc[prev_page]
        tc = fc[prev_page].get_children()[0]
        cont.remove(tc)
        content['f-o-list'].remove(cont)
        content['f-o-list'].insert(tc, to_page)
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
                # if sp1[-1] == it1.get_char():
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
        content['temp']['text_views'][content['notebook'].get_current_page()
                                      ].grab_focus()
        content['s-popup'].hide()

    def s_focus_out(self, *args):
        content['s-popup'].hide()
        content['temp']['text_views'][content['notebook'].get_current_page()
                                      ].grab_focus()

    def s_key_press(self, widget, event, *user_data):
        """Connect or catch only arrow keys if any other, send 
        focus to main textview widget"""
        key = Gdk.keyval_name(event.keyval)

        if key not in ['Down', 'Up', 'Return']:
            tv = content['temp']['text_views'][content['notebook'].get_current_page()]
            tv.grab_focus()
            content['s-popup'].hide()
            #e = Gdk.Event()
            #e.type = Gdk.EventType.KEY_RELEASE
            #e.keyval = event.keyval
            #v.emit("key_press_event", e)

            return True

    def quit(self, window, *args):
        loop = asyncio.get_event_loop()
        ret = loop.run_until_complete(self.load_quit())
        return ret

    def show(self, window, *args):
        self.load_show()
        GLib.timeout_add_seconds(1, self._set_terms)
        self.load_settings()
        if content['settings']['maximized']:
            self.window.maximize()
        num = content['extc_list'].iter_n_children()
        mime = [content['extc_list'][m][0] for m in range(num)]
        comm = [content['extc_list'][c][1] for c in range(num)]
        for ind, extc in enumerate(content['settings']['extc']):
            if extc[0] not in mime:
                content['extc_list'].append([extc[0], extc[1]])
        return False

    def _set_terms(self,  *args):
        self.ipy.feed_child(bytes("ipython\n", "utf-8"))
        self.python3_t.feed_child(bytes("python3\n", "utf-8"))

    def win_key_released(self, window, event, *args):
        key = Gdk.keyval_name(event.keyval)
        ctrl = (event.state & Gdk.ModifierType.CONTROL_MASK)
        alt = (event.state & Gdk.ModifierType.MOD1_MASK)
        if ctrl and key == "s":
            self.save_cb()
        elif ctrl and key == "o":
            self.on_open_cb()
        elif ctrl and key == "n":
            self.on_new_cb()
        elif ctrl and key == "f":
            self.on_find_cb()
        elif ctrl and key == "r":
            self.run_file()
        elif ctrl and key == "F2":
            self.replace_all_usr()

    async def _save_all(self, *args):
        for i in range(0, len(content['temp']['files_opened'])):
            if content['temp']['mime-types'][i] != "Image":
                if content['temp']['text_views'][i].get_buffer().get_modified():
                    if os.path.isfile(content['temp']['files_opened'][i]):
                        save(i, content, f=False)
                    elif len(args) > 1:
                        self.save_as(current=i)

    def save_all(self, *args):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._save_all(*args))

    def _format_doc(self, *curr):
        curr = content['notebook'].get_current_page()
        st = content['temp']['text_buffers'][curr].get_start_iter()
        en = content['temp']['text_buffers'][curr].get_end_iter()
        text = content['temp']['text_buffers'][curr].get_text(st, en, False)
        text = fix_code(text)
        content['temp']['text_buffers'][curr].set_text(text)

    def on_find_and_replace(self, *args):
        obj1 = builder.get_object("find-box")
        builder.get_object("find-box").show_all()
        content['search-bar'].grab_focus()
        obj1.show()
        self.on_toggle_replace_bar_cb()
        pass

    def load_settings(self, *args):
        if content['settings']['auto-save'] and content['settings']['auto-save-delay'] != 0:
            self.auto_save()
        content['buttons']["auto-save-btn"].set_active(
            content['settings']['auto-save'])
        content["buttons"]["auto-save-box"].set_sensitive(
            content['settings']['auto-save'])
        content['buttons']["auto-save-delay"].set_value(
            content['settings']["auto-save-delay"])
        content['buttons']["format-on_save-btn"].set_active(
            content['settings']["format_on_save"])
        content['buttons']["save-timer"].set_active_id(
            content["settings"]['save-delay'])
        content['buttons']['tab-btn'].set_value(
            content['settings']['tab-length'])
        content['buttons']['font-btn'].set_font(content['settings']['font'])
        content['buttons']["font-size-btn"].set_value(
            content['settings']['font-size'])
        builder.get_object(
            "sugg-style").set_active_id(content['settings']['sugg-style'])
        builder.get_object(
            "c-b-btn").set_active(content['settings']['create_b_file'])
        builder.get_object(
            "int-entry").set_text(content['settings']['interpreter'])

    def rev_file_bar(self, *args):
        rev = not content['f-bar-rev'].get_reveal_child()
        content['f-bar-rev'].set_reveal_child(rev)
        if not rev:
            builder.get_object("rev-btn").set_image(self.open_rev)
        else:
            builder.get_object("rev-btn").set_image(self.close_rev)

    def _open_folder(self, folder, *args):
        if folder is not None:
            global folder_open
            folder_open = folder
            ff = folder
            folder = os.walk(folder)
            parent = {}
            treestore = content['treestore']
            treestore.clear()
            content['folder-tree'].set_headers_visible(True)
            content['settings']['folder-open'] = ff
            content['folder-tree'].get_column(0).set_title(ff.split("/")[-1])
            for (path, dirs, files) in folder:
                treestore = content['treestore']
                for sbdir in dirs:
                    parent[os.path.join(path, sbdir)] = treestore.append(parent.get(path, None), ["folder",
                                                                                                  sbdir])
                for item in files:
                    mod = content['folder-tree'].get_model()
                    mimeico = Gio.content_type_guess(item, data=None)[0]
                    treestore.append(parent.get(path, None), [mimeico, item])

    def pixcellprop(self, col, cell, mod, it, *args):
        try:
            val = mod.get_value(it, 0).replace("/", "-")
            icon = get_f_img(val, mod, it)
            cell.set_property("pixbuf", icon)
        except Exception as e:
            return

    def f_cell_edited(self, *args):
        args[0].set_property("editable", False)
        if len(args) < 2:
            return
        if isinstance(args[1], bool):
            return
        isfile = False
        rn = False
        iters = args[1].split(":")
        name = ""
        it_p = ""
        for i, x in enumerate(iters, 0):
            if i != 0:
                it_p = it_p + ":" + iters[i]

            else:
                it_p = x
            it = content['folder-tree'].get_model().get_iter(it_p)
            name = name + "/" + \
                content['folder-tree'].get_model().get_value(it, 1)
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
            for i, x in enumerate(iters, 0):
                if i != 0:
                    it_p = it_p + ":" + iters[i]

                else:
                    it_p = x
                it = content['folder-tree'].get_model().get_iter(it_p)
                name = name + "/" + \
                    content['folder-tree'].get_model().get_value(it, 1)
            name2 = name
            try:
                os.mkdir(folder_open+name2)
            except FileExistsError as e:
                content['f-label'].set_text(e)

        elif content["treestore"][args[1]][1] != args[2]:
            mimeico = Gio.content_type_guess(args[2], data=None)[
                0].replace('/', "-")
            content["treestore"][args[1]][0] = mimeico
            content["treestore"][args[1]][1] = args[2]
            iters = args[1].split(":")
            name = ""
            it_p = ""
            for i, x in enumerate(iters, 0):
                if i != 0:
                    it_p = it_p + ":" + iters[i]

                else:
                    it_p = x
                it = content['folder-tree'].get_model().get_iter(it_p)
                name = name + "/" + \
                    content['folder-tree'].get_model().get_value(it, 1)
            name2 = name
            try:
                content['temp']["files_opened"][content['temp']['files_opened'].index(
                    folder_open+name1)] = folder_open+name2
            except ValueError:
                pass
            os.rename(folder_open+name1, folder_open+name2)

        elif content['treestore'][args[1]][1] == args[2]:
            pass

        else:
            it = content['folder-tree'].get_model().get_iter(args[1])
            content['treestore'].remove(it)

        self.foldercolumn = args[0]
        iters = args[1].split(":")
        name = ""
        it_p = ""
        for i, x in enumerate(iters, 0):
            if i != 0:
                it_p = it_p + ":" + iters[i]

            else:
                it_p = x
            it = content['folder-tree'].get_model().get_iter(it_p)
            name = name + "/" + \
                content['folder-tree'].get_model().get_value(it, 1)
        if isfile:
            if os.path.isfile(folder_open+name):
                res = content['f-exists-p'].run()
                content['f-exists-p'].hide()
                if res != Gtk.ResponseType.CANCEL:
                    with open(folder_open+name, "w"):
                        pass
            else:
                with open(folder_open+name, "w"):
                    pass

        self._open_folder(folder_open)

    def open_folder(self, *args):
        global folder_open
        fil = self.f_chooser.run()
        self.f_chooser.hide()
        if fil == Gtk.ResponseType.OK:
            fil = self.f_chooser.get_filename()
            folder_open = fil
            self._open_folder(fil)
            content['f-bar-rev'].set_reveal_child(True)
            self.terminal.spawn_async(
                Vte.PtyFlags.DEFAULT,
                fil,
                ["/bin/bash"],
                None,
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None, None, -1,
                None, None
            )

    def create_folder(self, *args):
        fpopup = content['create-folder']
        res = fpopup.run()
        fpopup.hide()

    def on_copy(self, *args):
        c = content['notebook'].get_current_page()
        tb = content['temp']["text_buffers"][c]
        select = tb.get_has_selection()
        if select:
            it1, it2 = tb.get_selection_bounds()
            text = tb.get_text(it1, it2, True)
            tv = content['temp']['text_views'][c]
            clip = tv.get_clipboard(Gdk.SELECTION_CLIPBOARD)
            clip.set_text(text, len(text))

    def on_paste(self, *args):
        c = content['notebook'].get_current_page()
        tb = content['temp']["text_buffers"][c]
        tv = content['temp']['text_views'][c]
        clip = tv.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        tt = clip.wait_for_text()
        tb.insert_at_cursor(tt)

    def on_cut(self, *args):
        c = content['notebook'].get_current_page()
        tb = content['temp']["text_buffers"][c]
        select = tb.get_has_selection()
        if select:
            it1, it2 = tb.get_selection_bounds()
            text = tb.get_text(it1, it2, True)
            tb.delete(it1, it2)
            tv = content['temp']['text_views'][c]
            clip = tv.get_clipboard(Gdk.SELECTION_CLIPBOARD)
            clip.set_text(text, len(text))

    def on_n_menu(self, *args):
        comm = [self.on_new_cb, self.on_open_cb, self.new_file, self.create_folder,
                self.open_folder, None, self.on_copy, self.on_cut, self.on_paste, None, self.save_cb, self.run_file, self._format_doc]
        cdict = {}
        for m in menu_items:
            if m != "<hr>":
                cdict[m] = comm[menu_items.index(m)]
        if cdict[args[0].get_label()] == comm[2]:
            cdict[args[0].get_label()](b=True)
            return
        cdict[args[0].get_label()](args[0])

    def folder_row(self, *args):
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
        for i, x in enumerate(iters, 0):
            if i != 0:
                it_p = it_p + ":" + iters[i]

            else:
                it_p = x
            it = content['folder-tree'].get_model().get_iter(it_p)
            name = name + "/" + \
                content['folder-tree'].get_model().get_value(it, 1)

        curr = content['notebook'].get_current_page()
        tv = content['temp']['text_views'][curr]
        fld = folder_open+name
        if os.path.isfile(fld):
            new_page(content, fld)

    def folder_area(self, *args):
        if args[1].button == 3:
            for j, i in enumerate(content['folder-menu'].get_children(), 0):
                if folder_open is None:
                    if j == 2:
                        continue
                    i.set_sensitive(False)
                else:
                    i.set_sensitive(True)
            content['folder-menu'].popup(None, None,
                                         None, None, args[1].button, args[1].time)
            return True

    def tips_tricks(self, *args):
        cur = ["notebook"].get_current_page()

    def problems_btn(self, *btn):
        content['t-rev'].set_reveal_child(
            not content['t-rev'].get_reveal_child())
        content['t-notebook'].set_current_page(1)

    def s_create_backup_file(self, *btn):
        content['settings']["create_b_file"] = btn[0].get_active()

    def on_settings_cb(self, *btn):
        content['pref'].show()

    def pref_closed_cb(Self, *args):
        content['pref'].hide()
        return True

    def win_state_changed(self, *args):
        if args[1].new_window_state & Gdk.WindowState.MAXIMIZED != 0:
            content['settings']['maximized'] = True
        else:
            content['settings']['maximized'] = False
        if folder_open is not None:
            self._open_folder(folder_open)

    def on_show_interpreter(self, *args):
        content['t-rev'].set_reveal_child(
            not content['t-rev'].get_reveal_child())
        content['t-notebook'].set_current_page(2)

    def on_terminal_cb(Self, *arg):
        content['t-rev'].set_reveal_child(
            not content['t-rev'].get_reveal_child())
        content['t-notebook'].set_current_page(0)

    def on_reload(self, btn=None, *args):
        lang = GtkSource.LanguageManager()
        for index, file in enumerate(content["temp"]["files_opened"]):
            buff = GtkSource.Buffer()
            mime = file.split(".")[-1].split("~")[0]
            tv = content['temp']['text_views'][index]
            if os.path.isfile(file):
                with open(file, "r") as ff:
                    dat = ff.read()
                    buff.set_language(lang.get_language(mime))
                    buff.set_text(dat)
                    tv.set_highlight_current_line(True)
                    buff.set_style_scheme(self.scheme)
                    tv.set_buffer(buff)
                    content['temp']["text_buffers"][index] = buff
                    buff.create_mark("line", buff.get_start_iter(), True)
                    buff.create_mark("search", buff.get_start_iter(), True)
        self.upd_settings()
        pass

    def upd_settings(self, *args):
        set_content(content)

    async def _auto_save(self, *args):
        global AUTOSAVE_ID
        tym = content["settings"]['auto-save-delay']
        if AUTOSAVE_ID is not None:
            GLib.source_remove(AUTOSAVE_ID)

        def _(*args):
            self.save_all()
            if content['settings']['auto-save']:
                return True
            else:
                return False
        if content['settings']['auto-save']:
            if content['settings']['save-delay'] == "minutes":
                tym = content['settings']["auto-save-delay"] * 60
            elif content['settings']['save-delay'] == "milliseconds":
                tym = content['settings']["auto-save-delay"] // (60*60)
        if content['settings']['auto-save-delay'] != 0:
            AUTOSAVE_ID = GLib.timeout_add_seconds(tym, _)

    def auto_save(self, *args):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._auto_save())

    def on_toggle_replace_bar_cb(self, *args):
        obj1 = builder.get_object("t-r-1")
        if not obj1.get_visible():
            builder.get_object("t-r-2").show()
            obj1.show()
        else:
            builder.get_object("t-r-2").hide()
            obj1.hide()

    def on_find_cb(self, *args):
        obj1 = builder.get_object("find-box")
        cur = content['notebook'].get_current_page()
        buf = content['temp']['text_buffers'][cur]
        builder.get_object("find-box").show_all()
        content['search-bar'].grab_focus()
        if buf.get_has_selection():
            it = buf.get_selection_bounds()
            ft = buf.get_text(it[0], it[1], False)
            content['search-bar'].set_text(ft)
        obj1.show()

    def replace_canceled(self, *args):
        self.on_toggle_replace_bar_cb()

    def on_replace_activated(self, *args):
        global USR_REPLACE
        f_text = builder.get_object("search-bar").get_text()
        cur = content['notebook'].get_current_page()
        buf = content['temp']['text_buffers'][cur]
        if f_text != "":
            r_text = builder.get_object("t-r-1").get_text()
            self.search_and_mark(f_text)
            if USR_REPLACE:
                while 1:
                    if not self._replace_text(buf, r_text):
                        break
                USR_REPLACE = False
            else:
                return self._replace_text(buf, r_text)

    async def __search_and_mark(self, buff, start, end, text, cur, forward=True, apply=True):
        if buff.get_tag_table().lookup("search") is None:
            buff.create_tag("search", background="#7de497")
        if forward is True:
            match = start.forward_search(text, 0, end)
        else:
            match = start.backward_search(text, 0, end)
        buff.remove_tag_by_name(
            "search", buff.get_start_iter(), buff.get_end_iter())

        if match is not None:
            m_a, m_b = match
            if apply:
                buff.apply_tag_by_name("search", m_a, m_b)
            mark = buff.get_mark("search")
            buff.move_mark(mark, m_b)
            content['temp']['text_views'][cur].scroll_to_mark(
                mark, 0.4, True, 0.3, 0.3)
            return m_b, m_a
        else:
            bb = end.backward_search(text, 0)
            if bb is not None:
                b1, b2 = bb
                return b1, b2
            return None, None

    def _replace_text(self, buf, text, forward=True):
        b = False
        if not forward:
            self.on_prev_match()
        m_a, _, __ = self.search_content
        if m_a is None:
            return False
        buf.insert(m_a, text)
        self.on_next_match(b)
        self.on_prev_match(b)
        m_a, m_b, __ = self.search_content
        if m_a is None:
            return False
        buf.delete(m_a, m_b)
        self.on_next_match()
        return True

    def _replace_all(self, *args):
        text = builder.get_object("search-bar").get_text()
        if text == "":
            return
        self.search_and_mark(text)
        while 1:
            if not self.on_replace_activated():
                break

    def on_forward_replace(self, *args):
        self.on_replace_activated()

    def on_replace_all(self, *args):
        self._replace_all()

    def replace_all_usr(self, *args):
        global USR_REPLACE
        cur = content['notebook'].get_current_page()
        buf = content['temp']['text_buffers'][cur]
        s = buf.get_has_selection()
        if s:
            it = buf.get_selection_bounds()
            ft = buf.get_text(it[0], it[1], False)
            self.on_find_and_replace()
            builder.get_object("search-bar").set_text(ft)
            builder.get_object("t-r-1").grab_focus()
            USR_REPLACE = True

    def on_backward_replace(self, *args):
        f_text = builder.get_object("search-bar").get_text()
        cur = content['notebook'].get_current_page()
        buf = content['temp']['text_buffers'][cur]
        if f_text != "":
            r_text = builder.get_object("t-r-1").get_text()
            self._replace_text(buf, r_text, False)

    def search_and_mark(self, text, start=None, end=None, forward=True, apply=True):
        cur = content['notebook'].get_current_page()
        buff = content['temp']['text_buffers'][cur]
        if start is None:
            start = buff.get_start_iter()
        if end is None:
            end = buff.get_end_iter()
        loop = asyncio.get_event_loop()
        s_c = loop.run_until_complete(self.__search_and_mark(
            buff, start, end, text, cur, forward, apply))
        if s_c is not None:
            self.search_content = (s_c[0], s_c[1], text)

    def on_search_bar_active(self, *args):
        text = args[0].get_text()
        self.search_and_mark(text)

    def on_prev_match(self, *args):
        cur = content['notebook'].get_current_page()
        buff = content['temp']['text_buffers'][cur]
        if len(self.search_content) > 0:
            _, last, text = self.search_content
            end = buff.get_start_iter()
            if len(args) > 0 and isinstance(args[0], bool):
                self.search_and_mark(text, last, end, False, apply=args[0])
            else:
                self.search_and_mark(text, last, end, False)

    def on_next_match(self, *args):
        cur = content['notebook'].get_current_page()
        buff = content['temp']['text_buffers'][cur]
        if len(self.search_content) > 0:
            last, _, text = self.search_content
            end = buff.get_end_iter()
            if len(args) > 0 and isinstance(args[0], bool):
                self.search_and_mark(
                    text, last, end, forward=True, apply=args[0])
            else:
                self.search_and_mark(text, last, end)

    def cancel_search(self, *args):
        obj1 = builder.get_object("search-bar")
        if obj1.get_visible():
            try:
                cur = content['notebook'].get_current_page()
                buff = content['temp']['text_buffers'][cur]
                buff.remove_tag_by_name(
                    "search", buff.get_start_iter(), buff.get_end_iter())
            except IndexError:
                pass
            builder.get_object("find-box").hide()

    def go_to_line_cb(self, *btn):
        content['line-entry'].show()
        content['line-entry'].grab_focus()

    def on_goto_line(self, *args):
        for i in args[0].get_text():
            if i.isalpha():
                return

        lin = args[0].get_text()
        cur = content['notebook'].get_current_page()
        buff = content['temp']['text_buffers'][cur]
        mark = buff.get_mark("line")
        mark.set_visible(True)
        #mark = buff.get_insert()
        it = buff.get_iter_at_mark(mark)
        ll = ''
        for i in lin:
            if i.isdigit():
                ll += i
            else:
                return
        if ll != '':
            ll = int(ll)-1
            it.set_line(ll)
            buff.move_mark(mark, it)
            content['temp']['text_views'][cur].scroll_to_mark(
                mark, 0.4, True, 0.3, 0.3)
            GLib.timeout_add(1000, self._hide_mark, mark)

    def _hide_mark(self, mark):
        mark.set_visible(False)
        return False

    def _feed_open_file(self, d):
        new_page(content, d)
        if len(content['temp']['files_opened']) == 2 and content['temp']['files_opened'][0].find("untitled") != -1:
            content['notebook'].remove_page(0)

    def _feed_open_folder(self, f):
        self._open_folder(f)
        content['f-bar-rev'].set_reveal_child(True)
        self.terminal.spawn_async(Vte.PtyFlags.DEFAULT,
                                  os.environ["HOME"],
                                  ["/bin/bash"],
                                  None,
                                  GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                  None, None, -1,
                                  None, None
                                  )
        self.window.show_all()

    #"Settings Handlers"
    def font_changed_cb(self, *args):
        fnt = str(args[0].get_font())
        content['settings']['font'] = fnt
        change_font(content, fnt)

    def on_auto_save_toggled(self, *btn):
        content['buttons']['auto-save-box'].set_sensitive(btn[0].get_active())
        content['settings']['auto-save'] = btn[0].get_active()
        if content['settings']['auto-save']:
            self.auto_save()

    def on_save_delay_changed(self, *args):
        content['settings']['auto-save-delay'] = args[0].get_value_as_int()
        if content['settings']['auto-save']:
            self.auto_save()

    def on_save_time_changed(self, *combo):
        content['settings']["save-delay"] = combo[0].get_active_id()
        if content['settings']['auto-save']:
            self.auto_save()

    def on_f_on_save(self, *args):
        content['settings']['format_on_save'] = args[0].get_active()

    def tab_length_changed_cb(self, *args):
        content['settings']['tab-length'] = args[0].get_value_as_int()

    def font_value_changed_cb(self, *args):
        content['settings']["font-size"] = args[0].get_value_as_int()
        ff = [list(re.split(r"\d\d?", content['settings']['font']))[0], "11"]
        ff[1] = str(args[0].get_value_as_int())
        fnt = "".join(ff)
        content['settings']['font'] = fnt
        content['buttons']["font-btn"].set_font(content['settings']['font'])
        change_font(content, fnt)

    def on_suggest_style_cb(self, *args):
        content['settings']['sugg-style'] = args[0].get_active_id()

    def on_interpreter_changed(self, *args):
        try:
            a_iter = args[0].get_active_text()
        except AttributeError:
            a_iter = args[0].get_text()
        if (is_app(a_iter) and str(args[0]).find("<Gtk.ComboBoxText") == -1) or a_iter == "python3.7":
            content['settings']['interpreter'] = a_iter
            print(a_iter)


def parse_arg(s: str):
    import os.path as pp
    import os
    cd = os.getcwd()
    s = s.split("./")[-1]
    if pp.exists(s):
        if pp.isfile(s):
            return 0
        elif pp.isdir(s):
            return 1
    else:
        return -1


def load_args():
    import sys
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return False


if __name__ == '__main__':
    loader = load_args()
    win = content['window']
    handler = Handler()
    builder.connect_signals(handler)
    win.show_all()

    if loader is not False:
        if parse_arg(loader) == 0:
            handler._feed_open_file(loader)
        elif parse_arg(loader) == 1:
            handler._feed_open_folder(loader)
    Gtk.main()
