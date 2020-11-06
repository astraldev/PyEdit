
import re
from json import load
import jedi
from jedi.api import Script
import jedi.inference as jd_inference
from gi.repository import Gtk, Pango
import parso as par
from pprint import pprint

sy_key2 = sy_key1 = s_quote = sy_num = s_comm = sy_oper = s_clsn = s_decor = s_ecep = s_funp = s_excp = s_funp = s_funname = None

direc = load(open("Data/settings.json"))["color_scheme"]
if direc == "":
    direc = "/home/astraldev/Desktop/projects/PyEditxC++/Data/color.json"


def load_settings():
    global sy_key2, sy_key1, s_quote
    global sy_num, s_comm
    global sy_oper, s_clsn
    global s_decor, s_ecep
    global s_funp, s_excp
    global s_funp, s_funname
    f = dict(load(open(direc)))
    colors = f['colors']
    attributes = f['attributes']
    group = [sy_key2, sy_key1, s_quote, s_comm, s_clsn, sy_oper,
             s_decor,  s_ecep, sy_num,  s_funname, s_funp, s_excp]
    for i, k in enumerate(colors.keys(), 0):
        obj = {}
        obj['foreground'] = colors[k]
        group[i] = obj
    for i, k in enumerate(attributes.keys(), 0):
        k = attributes[k]
        if k is not None:
            if isinstance(k, list):
                for n in range(len(k)):
                    try:
                        c_ = eval("Pango.{}.{}".format(
                            ['weight', "style"][n].title(), k[n].upper().replace(" ", "_")))
                    except Exception as e:
                        print(e)
                        continue
                    group[i][['weight', "style"][n]] = c_
            elif isinstance(k, str):
                try:
                    c_ = eval("Pango.{}.{}".format(
                        'weight'.title(), k[n].upper().replace(" ", "_")))
                    group[i]["weight"]
                except Exception as e:
                    pass

    sy_key2, sy_key1, s_quote, s_comm, s_clsn, sy_oper, s_decor,  s_ecep, sy_num,  s_funname, s_funp, s_excp = group


load_settings()
with open('/home/astraldev/Desktop/projects/PyEditxC++/Data/color.json') as f:
    colors = load(f)['colors']


SPACES = 0
store = 1
jedi.inference.recursion.recursion_limit = 3
jedi.inference.recursion.total_function_execution_limit = 150
jedi.inference.recursion.per_function_execution_limit = 6
jedi.inference.recursion.per_function_recursion_limit = 6

IN_DBLQ = set()
IN_SINQ = set()

def auto_close(key, buff, select):
    global SPACES
    SPACES = 0
    c1 = ['\'', '\"', '{', '[', '(']
    c2 = ['\'', '\"', '}', ']', ')']

    c1b = brack = ['{', '[', '(']
    brack_c = c2[2:]
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
            _x = spaces//4
            if ind in range(spaces+1):
                if _x > 0 :
                    _x = 1
                for i in range(_x*3):
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
                if chars[i] == "#":
                    add_in = True
                    break
                elif re.search(r'\S', chars[i]) and chars[i] != '#':
                    add_in = False
                    break
            if add_in:
                spaces += 4
        elif l.get_char() in brack:
            spaces += 4
        if l.get_char() in c1b:
            buff.insert_at_cursor("\n"+" "*(spaces+4)+"\n"+" "*(spaces-4))
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
    completions = Script(text).complete()
    if len(completions) < 2 and len(completions) > 0:
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
    elif len(completions) > 0:
        store = [x.name for x in completions if x]

async def syntax_error(buff):
    start = buff.get_start_iter()
    end = buff.get_end_iter()
    text = buff.get_text(start, end, True)
    if buff.get_tag_table().lookup("err_t") is None:
        buff.create_tag("err_t", underline="error")
    buff.remove_tag_by_name("err_t",start, end)

    errors = Script(text).get_syntax_errors()
    grammer = par.load_grammar()
    error_code = par.parse(text)
    error_found = grammer.iter_errors(error_code)
    for e in errors:
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

