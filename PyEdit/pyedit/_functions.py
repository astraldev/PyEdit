
import re
import jedi
from jedi.api import Script
import gi
import subprocess
gi.require_version("GtkSource", "4")
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Pango

SPACES = 0
store = 1
jedi.inference.recursion.recursion_limit = 3
jedi.inference.recursion.total_function_execution_limit = 150
jedi.inference.recursion.per_function_execution_limit = 6
jedi.inference.recursion.per_function_recursion_limit = 6

def auto_close(key:str, buff, select:bool, settings:dict=None) ->None:
    global SPACES
    SPACES = 0
    c1 = ['\'', '\"', '{', '[', '(']
    c2 = ['\'', '\"', '}', ']', ')']

    c1b = brack = ['{', '[', '(']
    brack_c = c2[2:]
    tab_l = settings['tab-length'] if settings is not None else 4
    if key == 'apostrophe':
        if select:
            iters = buff.get_selection_bounds()
            buff.insert(iters[1], '\'')
            cur = buff.get_insert()
            it = buff.get_iter_at_mark(cur)
            buff.insert(it, '\'')
            iters = buff.get_selection_bounds()
            buff.place_cursor(iters[1])
            return True
        else:
            buff.insert_at_cursor("\'")
            cur = buff.get_insert()
            it = buff.get_iter_at_mark(cur)
            it.backward_char()
            buff.place_cursor(it)
    if key == 'quotedbl':
        if select:
            iters = buff.get_selection_bounds()
            buff.insert(iters[1], '\"')
            cur = buff.get_insert()
            it = buff.get_iter_at_mark(cur)
            buff.insert(it, '\"')
            iters = buff.get_selection_bounds()
            buff.place_cursor(iters[1])
            return True
        else:
            buff.insert_at_cursor("\"")
            cur = buff.get_insert()
            it = buff.get_iter_at_mark(cur)
            it.backward_char()
            buff.place_cursor(it)
    if key == 'bracketleft':
        if select:
            iters = buff.get_selection_bounds()
            buff.insert(iters[1], ']')

            iters = buff.get_selection_bounds()
            buff.insert(iters[0], '[')

            return True
        else:
            buff.insert_at_cursor("]")
            cur = buff.get_insert()
            it = buff.get_iter_at_mark(cur)
            it.backward_char()
            buff.place_cursor(it)
    if key == 'braceleft':
        if select:
            iters = buff.get_selection_bounds()
            buff.insert(iters[1], '}')

            iters = buff.get_selection_bounds()
            buff.insert(iters[0], '{')

            return True
        else:
            buff.insert_at_cursor("}")
            cur = buff.get_insert()
            it = buff.get_iter_at_mark(cur)
            it.backward_char()
            buff.place_cursor(it)
    if key == 'parenleft':
        if select:
            iters = buff.get_selection_bounds()
            buff.insert(iters[1], ')')

            iters = buff.get_selection_bounds()
            buff.insert(iters[0], '(')
            
            return True
        else:
            buff.insert_at_cursor(")")
            cur = buff.get_insert()
            it = buff.get_iter_at_mark(cur)
            it.backward_char()
            buff.place_cursor(it)
    elif key == 'BackSpace':
        cur = buff.get_insert()
        it = buff.get_iter_at_mark(cur)
        it2 = buff.get_iter_at_mark(cur)
        it.backward_char()
        if it.get_char() in c1 and it2.get_char() in c2\
                and c1.index(it.get_char()) == c2.index(it2.get_char()) and not select:
            it2.forward_char()            
            buff.delete(it, it2)
            return True
        elif not select:
            cur = buff.get_insert()
            l = buff.get_iter_at_mark(cur)
            l.backward_line()
            chars = buff.get_iter_at_mark(
                cur).get_slice(l)
            chars = str(chars).split('\n')[-1]
            ind = buff.get_iter_at_mark(cur).get_line_index()
            spaces = 0
            add_in = True
            for i in range(0, len(chars)):
                if chars[i] == '\n':
                    break
                elif chars[i].isspace():
                    spaces += 1
                else:
                    break
                pass
            _x = spaces//tab_l
            if ind in range(spaces+1):
                if _x > 0 :
                    _x = 1
                for i in range(_x*tab_l-1):
                    it.backward_char()
                buff.delete(it, it2)
                return True
    elif key == 'Return':
        cur = buff.get_insert()
        l = buff.get_iter_at_mark(cur)
        l.backward_line()
        chars = buff.get_iter_at_mark(
            cur).get_slice(l)

        chars = str(chars).split('\n')[-1]
        spaces = 0
        add_in = True
        for i in range(0, len(chars)):
            if chars[i] == '\n':
                break
            elif chars[i].isspace():
                spaces += 1
            else:    # re.search(r"[.]", chars) is not None:
                break
            pass
        cur = buff.get_insert()
        l = buff.get_iter_at_mark(cur)
        l.backward_char()
        if chars.find(":") != -1:
            index_of_colon = chars.find(":")
            for i in range(index_of_colon+1, len(chars)):
                if i == index_of_colon+1 and chars[i] == ":":
                    break
                if chars[i] == "#":
                    add_in = True
                    break
                elif re.search(r'\S', chars[i]) and chars[i] != '#':
                    add_in = False
                    break
            if add_in:
                spaces += tab_l
        if l.get_char() in brack:
            spaces += tab_l
        if l.get_char() in c1b:
            buff.insert_at_cursor("\n"+" "*(spaces)+"\n"+" "*(spaces-tab_l))
            cur = buff.get_insert()
            l = buff.get_iter_at_mark(cur)
            l.backward_line()
            l.forward_to_line_end()
            buff.place_cursor(l)
        else:
            buff.insert_at_cursor('\n'+" "*spaces)
        return True
    elif key == 'Tab':
        text = buff.get_insert()
        start_it = buff.get_start_iter()
        text = buff.get_text(start_it, buff.get_iter_at_mark(text), False)
        tab = True
        for i in text.rsplit("\n")[-1]:
            if not i.isspace():
                tab = False
                break
            else:
                tab = True
        if tab:
            buff.insert_at_cursor(" "*tab_l)
            return True

        tab_suggest(buff)
        return True

def get_space():
    global SPACES
    _ = SPACES
    SPACES = 0
    return _

def get_store():
    global store
    s = store
    store = 0
    if s == 0:
        return None
    elif isinstance(s, list):
        return s
    else:
        return None

def tab_suggest(buff: Gtk.TextBuffer, listore=None):
    global store
    text = str(buff.get_text(buff.get_start_iter(), buff.get_iter_at_mark(buff.get_insert()), False))
    completions = None
    for _ in range(5):
        try:
            completions = Script(text).complete()
            break
        except:
            return
    if len(completions) == 1:
        com = str(completions[0].name)
        text = buff.get_insert()
        start_it = buff.get_start_iter()
        text = str(buff.get_text(start_it, buff.get_iter_at_mark(text), False))
        sp1 = text.split(' ')[-1].split('.')
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
        store = 0
    elif completions is not None and len(completions) > 0:
        store = [x.name for x in completions if x]

def fill_store(buff):
    global store
    text = str(buff.get_text(buff.get_start_iter(), buff.get_iter_at_mark(buff.get_insert()), False))
    completions = None
    for _ in range(5):
        try:
            completions = Script(text).complete()
            break
        except:
            return
    if completions is not None and len(completions) > 0:
        store = [x.name for x in completions if x]
        return store

def syntax_error(buff):
    start = buff.get_start_iter()
    end = buff.get_end_iter()
    text = buff.get_text(start, end, True)
    
    if buff.get_tag_table().lookup("err_t") is None:
        buff.create_tag("err_t", underline="error")
    buff.remove_tag_by_name("err_t",start, end)

    errors = Script(text).get_syntax_errors()
    for e in errors:
        start = buff.get_start_iter()
        end = buff.get_end_iter()
        lin = e.line-1
        col = e.column-1
        lin2 = e.until_line-1
        col2 = e.until_column-1
        if lin < 1:
            lin = 0
        if col < 1:
            col = 0
        if lin2 < 1:
            lin2 = 0
        if col2 < 1:
            col2 = 0
        start.set_line(lin)
        end.set_line(lin2)
        start.set_line_offset(col)
        end.set_line_offset(col2)
        buff.apply_tag_by_name("err_t", start, end)

def _create_temp(d, name):
    with open(d+name, "w") as f:
        pass

def write_to_temp(f,dat):
    with open(f, "w") as f:
        f.write(dat)

def check_syntax(name):
    out = subprocess.check_output(["pylint", name])
    print(out)