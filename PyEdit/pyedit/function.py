from ._functions import *
from gi.repository import GLib

def load(tb):
    GLib.idle_add(syntax_error, tb)

