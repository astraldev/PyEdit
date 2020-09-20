import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
from Data import *
from Syntax import Syntax
from Notebook import Notebook
class FileOpener:
    def __init__(self,notebook,window,*args):
        self.notebook = notebook
        self.opener = Gtk.FileChooserDialog(window,title='Please choose a file')
        self.opener.add_buttons(Gtk.STOCK_CANCEL,
                                Gtk.ResponseType.CANCEL,
                                Gtk.STOCK_OPEN,
                                Gtk.ResponseType.OK
                                )##work on notebook for open
        win = window()
        self.opener.set_transient_for(win.window)
                    
        filt = Gtk.FileFilter()
        filt.set_name('Python Files')
        filt.add_mime_type("text/x-python")
        self.opener.add_filter(filt)
        response = self.opener.run()
        if response == Gtk.ResponseType.OK:
            self.file = self.opener.get_filename()
        else:
            self.opener.destroy()
            return
        self.opener.destroy()
        if self.file in Data['files_opened']:
            index = int(1+ Data['files_opened'].index(self.file))
            win.notebook.set_current_page(index)
            return
        self.__open(self.file)

    def __open(self, filename):
        self.notebook().new_page(file_name=self.file)

