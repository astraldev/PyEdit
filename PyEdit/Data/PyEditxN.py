import os
from markdown import markdown as md
from jedi.api import Script
from Data.function import load, auto_close, get_space, get_store, tab_suggest
from autopep8 import docstring_summary, fix_code
import gi
from gi.repository import Gtk, GLib, Gdk, Pango, WebKit2, GtkSource, Gio, GdkPixbuf
content_ = None
close_buttons = []
tab_labels = []

def load_line(buf, linelab, *args):
    pass

def new_page(content, file="",fc=None):
    global content_
    content_ = content
    notebook = content['notebook']
    if file in content['temp']['files_opened']:
        notebook.set_current_page(content['temp']['files_opened'].index(file))
        return
    text_view = GtkSource.View()
    text_buffer = GtkSource.Buffer()
    lang = GtkSource.LanguageManager()
    if file != "":
        mime = Gio.content_type_guess(file,data=None)[0]
        if str(mime).find("python") != -1:
            text_buffer.set_language(lang.get_language("python"))
            content['temp']['mime-types'].append("python")
        else:
            content['temp']['mime-types'].append(None)
    else:
        text_buffer.set_language(lang.get_language("python"))
        content['temp']['mime-types'].append("untitled_file")

    text_view.set_highlight_current_line(True)
    close_tab = Gtk.HBox()
    close_btn = Gtk.Button()
    close_img = Gtk.Image()
    close_lab = Gtk.Label()
    close_buttons.append(close_btn)
    tab_labels.append(close_lab)

    if file == '':
        pg = notebook.get_n_pages()
        close_lab.set_text(f"*untitled {pg}")
        file = f"*untitled {pg}"
    elif fc is None:
        file_s = os.access(file, os.W_OK)
        name = file.split('/')[-1]
        
        with open(file, 'r') as f:
            file_dat = f.read()
            text_buffer.set_text(file_dat)
            if file_s is False:
                text_view.set_editable(False)
                name += ' - [Read-only]'

        close_lab.set_text(name)

    close_img.set_from_icon_name("application-exit", Gtk.IconSize.MENU)
    close_btn.set_image(close_img)
    close_btn.connect('clicked', close_tab_cb)

    close_tab.pack_start(close_lab, True, True, 0)
    close_tab.pack_end(close_btn, False, True, 0)
    close_btn.set_relief(Gtk.ReliefStyle.NONE)
    close_tab.set_hexpand(True)

    content['notebook'].child_set_property(close_tab, 'tab-expand', True)
    content['notebook'].child_set_property(close_tab, 'tab-fill', True)
    close_tab.show_all()
    text_view.set_buffer(text_buffer)
    text_buffer.set_modified(False)
    if fc is not None:
        notebook.append_page(fc, close_tab)
        content["temp"]['text_views'].append(None)
        content['temp']['files_opened'].append(None)
        content['temp']['modified'].append(None)
        content['temp']['tab-label'].append(None)
        notebook.set_tab_reorderable(sc, True)
        notebook.show_all()
        notebook.set_current_page(-1)
        return
    else:
        content["temp"]['text_views'].append(text_view)
        content['temp']['files_opened'].append(file)
        content['temp']['modified'].append(False)
        content['temp']['tab-label'].append(close_lab)

    font = Pango.FontDescription(content['settings']['font'])

    text_view.connect('key_release_event', enter,)
    text_view.connect('key_press_event', indent)
    text_view.connect("button_press_event",cursor)
    text_view.connect('motion-notify-event', show_doc)
    text_buffer.connect('modified-changed', on_modified, content)
    content["temp"]['text_buffers'].append(text_buffer)

    text_view.set_top_margin(10)
    text_view.set_left_margin(5)
    text_view.set_bottom_margin(20)
    text_view.modify_font(font)

    #paned.add1(_line_box)
    sc = Gtk.ScrolledWindow()
    sc.set_hexpand(True)
    sc.set_vexpand(True)
    text_view.set_show_line_numbers(True)
    sc.add(text_view)
    notebook.append_page(sc, close_tab)
    notebook.set_tab_reorderable(sc, True)
    line_col(text_buffer)
    notebook.show_all()
    notebook.set_current_page(-1)

def close_tab_cb(button, *args):
    "For closing Tabs"
    lab = content_["close-popup"]\
        .get_children()[0]\
        .get_children()[0]\
        .get_children()[1]\
        .get_children()[0]

    for ind, btn in enumerate(close_buttons, 0):
        if btn == button:
            if content_ is not None:
                fn = content_['temp']['files_opened'][ind].split('/')[-1]
                if content_['temp']['modified'][ind] == False:
                    content_['notebook'].remove_page(ind)
                    del close_buttons[ind]
                    del tab_labels[ind]
                else:
                    lab.set_text(
                        'Save changes to "{}" before closing'.format(fn))
                    res = content_['close-popup'].run()
                    content_['close-popup'].hide()
                    if res == 2:
                        if not os.path.isfile (content_["temp"]['files_opened'][ind]):
                            content_['file-chooser2'].run()
                            content_['file-chooser2'].hide()
                            if content_['file-chooser2'].get_filename() is not None:
                                save_as(
                                    content_['file-chooser2'].get_filename(), ind, content_)
                            else:
                                pass
                        else:
                            save(ind, content_)
                        content_['notebook'].remove_page(ind)
                        del close_buttons[ind]
                        del tab_labels[ind]
                    elif res == 1:
                        return
                    elif res == 0:
                        content_['notebook'].remove_page(ind)
                        del close_buttons[ind]
                        del tab_labels[ind]
                
                break

def indent(textview, event, *args):
    key = Gdk.keyval_name(event.keyval)
    buff = textview.get_buffer()
    select = buff.get_has_selection()
    ret = auto_close(key, buff, select)
    ctrl = (event.state & Gdk.ModifierType.CONTROL_MASK)
    store = None
    store = get_store()
    ind = content_['notebook'].get_current_page()
    if content_['temp']['mime-types'][ind] == 'python':
        load(buff)
    if ctrl and event.keyval == Gdk.KEY_space:
        if content_['temp']['mime-types'][ind] == 'python':
            tab_suggest(buff)
            set_up_suggest(get_store(),textview)
    if key == "BackSpace":
        return ret
    if isinstance(store, list):
        set_up_suggest(store, textview)
    return ret

def set_up_suggest(store, textview):
    content_['s-list'].clear()
    for i in store:
        content_['s-list'].append([i])
    move_sugg(textview, content_['s-popup'])
    content_['s-view'].show_all()
    content_['s-popup'].present()
    content_['s-popup'].grab_focus()
    content_['s-view'].grab_focus()
    content_['s-popup'].present()

def cursor(tv,*args):
    if args[0].button == 3:
        content_["n-menu"].popup(None,None,None,None,args[0].button,args[0].time)
        return True

def enter(textv, e, *args):
    textv = textv.get_buffer()
    key = Gdk.keyval_name(e.keyval)
    if content_ is not None:
        line_col(textv)
    ind = content_['notebook'].get_current_page()
    if content_['temp']['mime-types'][ind] == 'python':
        load(textv)

def modify(val_index, val2_index):
    temp = close_buttons[val2_index]
    close_buttons[val2_index] = close_buttons[val_index]
    close_buttons[val_index] = temp

def save(current_index, content):
    file = content['temp']['files_opened'][current_index]
    buff = content['temp']['text_buffers'][current_index]
    start_it = buff.get_start_iter()
    end_it = buff.get_end_iter()
    text = buff.get_text(start_it, end_it, True)
    content['temp']['tab-label'][current_index].set_text(file.split('/')[-1])
    content['temp']['files_opened'][current_index] = file
    if content['settings']['format_on_save']:
        text = fix_code(text,encoding='utf-8')
    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)
    #buff.set_text(text)
    content['temp']['modified'][current_index] = False
    content['header_bar'].set_title(file.split('/')[-1])

def save_as(file_name, current_index, content):
    file = content['temp']['files_opened'][current_index]
    buff = content['temp']['text_buffers'][current_index]
    start_it = buff.get_start_iter()
    end_it = buff.get_end_iter()
    text = buff.get_text(start_it, end_it, True)
    content['temp']['tab-label'][current_index].set_text(file_name.split('/')[-1])
    content['temp']['files_opened'][current_index] = file_name
    file_name = file_name.split('file://')[-1]
    if os.path.isfile(file):
        os.rename(file,file_name)
    else:
        with open(file_name, "w") as f:
            f.write(text)
            pass
    content['temp']['modified'][current_index] = False
    content['header_bar'].set_title(file_name.split('/')[-1])
    content['temp']['tab-label'][current_index].show_all()
    

def move_sugg(textview, window):
    textbuff = textview.get_buffer()
    cur = textbuff.get_insert()
    l = textbuff.get_iter_at_mark(cur)
    loc = textview.get_cursor_locations(l)[0]
    winc = textview.buffer_to_window_coords(
        Gtk.TextWindowType.TEXT, loc.x, loc.y)
    orig = textview.get_window(Gtk.TextWindowType.TEXT).get_origin()
    winc_1 = winc[1]
    if winc[1] > 500:
        winc_1 = winc[1] - window.get_size()[1] - loc.height
    window.move(orig[1]+winc[0], orig[2]+winc_1+loc.height)


mv_sec = None
def show_doc(tv, e, *args):
    global mv_sec
    if mv_sec is not None:
        GLib.source_remove(mv_sec)
    mv_sec = GLib.timeout_add_seconds(
        2, waited, tv, e.x, e.y, (e.x_root, e.y_root))

def _get_doc(word: str, buff, line_col: tuple):
    full_text = str(buff.get_text(
        buff.get_start_iter(), buff.get_end_iter(), True))
    fast = bool(len(full_text) > 500)
    sc = Script(full_text).infer(line_col[0]+1, line_col[1])
    return sc

def waited(tv, *args):
    global mv_sec, content_
    mv_sec = None
    content_['doc-win'].hide()
    if tv.is_focus():
        winc = tv.window_to_buffer_coords(
            Gtk.TextWindowType.TEXT, args[0], args[1])
        it = tv.get_iter_at_location(winc[0], winc[1])[1]
        it2 = tv.get_iter_at_location(winc[0], winc[1])[1]
        if tv.get_iter_at_location(winc[0], winc[1])[0]:
            while 1:
                if it.get_char().isalpha() or it.get_char().isdigit() or it.get_char() == "_":
                    if not it.forward_char():
                        break
                elif it.get_char().isspace():
                    break
                else:
                    if not it.forward_char():
                        break
            while 1:
                if it2.get_char().isalpha() or it2.get_char().isdigit() or it2.get_char() == "_":
                    if not it2.backward_char():
                        break
                    pass
                elif it2.get_char().isspace():
                    break
                else:
                    if not it2.backward_char():
                        break

            it.backward_char()
            it2.forward_char()
            text = tv.get_buffer().get_text(it, it2, True)
            doc = _get_doc(text, tv.get_buffer(),
                           (it.get_line(), it2.get_line_index()))
            if len(doc) != 0:
                if len(doc[0].docstring(False)) > 0:
                    print(docstring_summary(doc[0].docstring(False)))
                    text = "<head><style>body{background-color: rgb(30,30,30);color: rgb(210,210,210);}code{background-color: rgb(90,90,90);border-radius: 2px;}</style>\
                        </head>\
                        <body> \n" + md(str(doc[0].docstring(True)), extensions=["fenced_code", 'codehilite'])\
                        + "</body>".replace("\n","<br>")
                    content_['webview'].load_html(text)
                    #print(text)
                    content_['doc-win'].move(args[2][0], args[2][1])
                    content_['doc-win'].show()
                    content_['webview'].show_all()
    return False

def on_modified(buff, content):
    ind = content['temp']['text_buffers'].index(buff)
    content['temp']['modified'][ind] = True
    line_col(buff)
    if content_['temp']['mime-types'][ind] == 'python':
        load(buff)

def line_col(textv):
    line_lab = content_['line-lab']
    col_lab = content_['col-lab']
    lin = int(textv.get_iter_at_mark(textv.get_insert()).get_line())+1
    col = int(textv.get_iter_at_mark(textv.get_insert()).get_line_index())
    line_lab.set_text(f'line {lin}')
    col_lab.set_text(f'col {col}')

def change_font(content:dict, font:str):
    global content_
    content_ = content
    font = Pango.FontDescription(str(font))
    for i in content['temp']['text_views']:
        i.modify_font(font)

def get_f_img(file, mod, it):
    val = Gio.content_type_guess(mod.get_value(it,1),data=None)[0].replace("/","-")
    val2 = val.replace("text-x-", "")
    if mod.get_value(it,0) != "folder":
        return Gtk.IconTheme().get_default().load_icon(val, 16, 0)
    else:
        return Gtk.IconTheme().get_default().load_icon("folder", 16, 0)


