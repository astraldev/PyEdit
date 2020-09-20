import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf

class About:
    "About PyEdit"
    def __init__(self,window):
        self.window = window().window
        self.about = Gtk.AboutDialog(parent=self.window)
        self.about.set_program_name('PyEdit')
        self.about.set_version('1.2')
        self.about.set_program_name('PyEdit')
        img = Pixbuf.new_from_file('./PyEdit150x108.png')
        self.about.set_logo(img) #PyEdit150x108.ico
        self.about.add_buttons(Gtk.STOCK_CANCEL,
                               Gtk.ResponseType.CANCEL,
                               Gtk.STOCK_OK,
                               Gtk.ResponseType.OK)
        self.about.set_license_type(Gtk.License.GPL_3_0)
        self.about.set_authors(['Ekure Nyong'])
        self.about.set_comments('A very small text editor for python Files')

    def show_about(self):
        response = self.about.run()
        self.about.destroy()
        