from Data import *
from gi.repository import Pango
from Syntax import Syntax
Key = 0

class Notebook:
    "Notebook class for PyEdit"
    def __init__(self,window,*args):
        win = window()
        self.notebook = win.notebook
        self.notebook_key_press = win.notebook_key_press
        self.indent = win.indent
        self.cursor = win.cursor
        self.close_tab = win.close_tab
        self.delete_range = win.delete_range

    def new_page(self, Label='', file_name='', text_buffer=None, *args):
        """
        Create new page for the Notebok class
        """
        tv = Gtk.TextView()
        view_port1 = Gtk.Viewport()
        paned = Gtk.HPaned()
        line_box = Gtk.VBox()
        line_box.set_name('num')
        line = Gtk.Label(label=' 1')
        line_box.pack_start(line, False, False, 0)
        line.set_justify(Gtk.Justification.RIGHT)
        tab = Gtk.HBox()
        close_img = Gtk.Image()

        if file_name != '':
            fn = file_name.split('/')[-1]
            tab_label = Gtk.Label(label=fn)
        elif Label != '':
            tab_label = Gtk.Label(label=Label)
        else:
            return

        close_btn = Gtk.Button()

        ################# Set textview properties #####################
        tv.set_editable(True)
        tv.set_top_margin(10)
        tv.set_cursor_visible(True)
        tv.set_accepts_tab(True)
        tv.set_overwrite(False)
        tv.set_left_margin(5)
        ######## connect events
        tv.connect('key_release_event', self.notebook_key_press)
        tv.connect('key_release_event', self.indent)
        tv.connect('button_press_event', self.cursor)

        ################## create textbuffer for files ##############

        tb = Gtk.TextBuffer()
        if file_name != '':
            data = open(file_name, 'r')
            tb.set_text(data.read())
            tv.set_buffer(tb)
            Data['files_opened'].append(file_name)
            data.close()
        else:
            tv.set_buffer(tb)
            Data['files_opened'].append(Label)
        tb.connect('delete-range',self.delete_range)
        tb.connect('delete-range',self.del_ran)
        tb.connect_after('delete-range',self.__del)
        tb.connect('modified-changed',self.text_modified)
        tb.set_modified(False)
        #tv.connect('key_press_event', self.notebook_key_press)
       
        ################# close btn and img ##############
        close_img.set_from_icon_name("application-exit", Gtk.IconSize.MENU)
        close_btn.set_image(close_img)
        close_btn.connect('clicked', self.close_tab)
        close_btn.set_relief(Gtk.ReliefStyle.NONE)

        ######### create temporary refference
        Data['close_btn'].append(close_btn)
        Data['text_buffer'].append(tb)
        Data['text_view'].append(tv)
        Data['file_label'].append(tab_label)
        Data['line_lab'].append(line)
        Data['modified'].append(False)

        ############# Create the tab to hold label and button
        tab.pack_start(tab_label, expand=True, fill=True, padding=0)
        tab.pack_end(close_btn, expand=False, fill=True, padding=0)
        tab.show_all()

        ################scrolled win###################
        ####### scrolled 1 holds textview  `tv`
        tv_s = Gtk.ScrolledWindow()
        tv_s.set_hexpand(True)
        tv_s.set_vexpand(True)
        tv_s.add(tv)
        ###### paned holds `tv_s` and `line_box`
        paned.add2(tv_s)
        paned.add1(line_box)
        paned.show_all()
        ###### scrolled 2 holds `view_port1`
        sc = Gtk.ScrolledWindow()
        sc.set_hexpand(True)
        sc.set_vexpand(True)
        view_port1.add(paned)
        sc.add(view_port1)

        ################ notebook   #######################
        ###### Add page and show all
        self.notebook.append_page(sc, tab)
        tab.set_hexpand(True)
        self.notebook.child_set_property(tab,'tab-expand',True)
        self.notebook.child_set_property(tab,'tab-fill',True)
        self.notebook.set_current_page(-1)
        self.notebook.show_all()
        Syntax(0)

    def del_ran(self,*_):
        global Key
        chars = ['\'','\"','{','[','(','`']
        chars_ = ['\'',"\"",'}',']',')','`']
        it2 = _[2]
        if it2.get_char() in chars_ and _[1].get_char() in chars:
            Key = 1
    def __del(self,*_):
        global Key
        if Key == 1:
            _[1].forward_char()
            _[0].delete(_[1],_[2])
            Key = 0
    def text_modified(self,buf,*_):
        for i in Data['text_buffer']:
            if i == buf:
                index = Data['text_buffer'].index(i)
                Data['modified'][index]=True
