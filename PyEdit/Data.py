import json
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
from jedi.api import Script
#this file was edited
__version__ = 1.0
Data = {
    'files_opened': [],
    'file_label': [],
    'text_buffer': [],
    'text_view': [],
    'line_lab': [],
    'close_btn': [],
    'modified':[]
}
files_opened = []
with open('settings.json', 'r') as s:
    try:
        json_dat = json.load(s)
        Syntax_Colors = json_dat['color']
        settings = json_dat["setting"]
        files_opened = json_dat['files_opened']
    except:
        Syntax_Colors = {
            "syntax_key": "rgba(171, 118, 167, 1)",
            "syntax_key2": "rgba(70, 120, 189, 1)",
            "syntax_oper": "rgb(195,195,195)",
            "syntax_quote": "rgba(187, 132, 110, 1)",
            "syntax_num": "rgba(153, 172, 153, 1)",
            "comment": "rgba(80, 122, 66, 0.977)",
            "search": "rgba(125, 125, 125, 0.877)"
        }
        settings = {
            'font': 'sans 12',
            'justification': 'none',
            'closing_quote': 'on',
            'closing_bracket': 'on',
            'auto_save_delay':0,
            'auto_save':'off',
            "auto_save_timing":"seconds"
        }

words = []
keyword = ['as', 'break', 'if', 'elif', 'else',
           'except', 'finally', 'for', 'from', 'import', 'pass', 'raise',
           'return', 'try', 'while', 'with']
keyword2 = [
    'None', 'is', 'not',
    'global', 'def', 'True',
    'False', 'in', 'class',
    'print', 'or', 'and',
    'self','yield','lambda'
]
operators = ['=', '<', '>', '+', '-', '!', '/', '*','%']
quote = ['\'', '\"','\"\"\"']
numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

