from Data import *
import re
current_tag = None
class Syntax:
    def __init__(self,current):
        self.current = current
        'Provides colors for syntax'
        global Data
        page = current-1
        self.start = Data['text_buffer'][page].get_start_iter()
        self.end = Data['text_buffer'][page].get_end_iter()
        tt = Data['text_buffer'][page].get_tag_table()
        tt.foreach(lambda x: Data['text_buffer']
                       [page].remove_tag(x, self.start, self.end))
        for i in operators:  # 0
            self.syntax_oper(i, self.start)
        for i in keyword2:  # 1
            self.syntax_key2(i, self.start, Syntax_Colors['syntax_key2'])
        for i in keyword:  # 2
            self.syntax_key(i, self.start, Syntax_Colors['syntax_key'])
        for i in numbers:  # 3
            self.syntax_num(i, self.start, Syntax_Colors['syntax_num'])
        for i in quote:  # 4
               self.quote(i, self.start)
        self.comment(self.start)

    def syntax_key(self, text, start, color):
        global current_tag
        current = self.current
        page = current-1
        end = Data['text_buffer'][page].get_end_iter()
        if Data['text_buffer'][page].get_tag_table().lookup('syntax_key') == None:
            current_tag = Data['text_buffer'][page].create_tag(
                'syntax_key', foreground=color)
            current_tag.set_priority(2)
        current_tag.set_property('foreground', color)
        match = start.forward_search(text, 0, end)
        test_for_key = start.forward_search(text, 0, end)
        if match is not None:
            match_start, match_end = match
            t_s, t_e = test_for_key
            t_s.backward_char()
            b = t_s.get_char()
            a = t_e.get_char()
            Data['text_buffer'][page].apply_tag_by_name(
                'syntax_key', match_start, match_end)
            if not b == text[0]:
                if a and re.match(r"[A-Za-z_]", a) is not None:
                    Data['text_buffer'][page].remove_tag_by_name(
                        'syntax_key', match_start, match_end)
                if b and re.match(r'[A-Za-z]', b) is not None:
                    Data['text_buffer'][page].remove_tag_by_name(
                        'syntax_key', match_start, match_end)
            elif b == text[0]:
                if a and re.match(r"[A-Za-z_]", a) is not None:
                    Data['text_buffer'][page].remove_tag_by_name(
                        'syntax_key', match_start, match_end)
            self.syntax_key(text, match_end, color)

    def syntax_num(self, text, start, color):
        global current_tag
        current = self.current
        page = current-1
        end = Data['text_buffer'][page].get_end_iter()
        if Data['text_buffer'][page].get_tag_table().lookup('syntax_n') == None:
            current_tag = Data['text_buffer'][page].create_tag(
                'syntax_n', foreground=color)
            current_tag.set_priority(3)
        current_tag.set_property('foreground', color)
        match = start.forward_search(text, 0, end)
        test_for_key = start.forward_search(text, 0, end)
        if match is not None:
            match_start, match_end = match
            t_s, t_e = test_for_key
            t_s.backward_char()
            b = t_s.get_char()
            a = t_e.get_char()
            Data['text_buffer'][page].apply_tag_by_name(
                'syntax_n', match_start, match_end)
            if a and re.match(r"[A-Za-z_]", a) is not None:
                Data['text_buffer'][page].remove_tag_by_name(
                    'syntax_n', match_start, match_end)
            if b and re.match(r'[A-Za-z_]', b) is not None:
                Data['text_buffer'][page].remove_tag_by_name(
                    'syntax_n', match_start, match_end)
            self.syntax_num(text, match_end, color)

    def syntax_key2(self, text, start, color):
        global current_tag
        current = self.current
        page = current-1
        end = Data['text_buffer'][page].get_end_iter()
        if Data['text_buffer'][page].get_tag_table().lookup('syntax_k2') == None:
            current_tag = Data['text_buffer'][page].create_tag(
                'syntax_k2', foreground=color)
            current_tag.set_priority(1)
        current_tag.set_property('foreground', color)
        match = start.forward_search(text, 0, end)
        test_for_key = start.forward_search(text, 0, end)
        if match is not None:
            match_start, match_end = match
            t_s, t_e = test_for_key
            t_s.backward_char()
            b = t_s.get_char()
            a = t_e.get_char()
            Data['text_buffer'][page].apply_tag_by_name(
                'syntax_k2', match_start, match_end)
            if not b == text[0]:
                if re.match(r"[A-Za-z_]", a) is not None:
                    Data['text_buffer'][page].remove_tag_by_name(
                        'syntax_k2', match_start, match_end)
                if re.match(r'[A-Za-z_]', b) is not None:
                    Data['text_buffer'][page].remove_tag_by_name(
                        'syntax_k2', match_start, match_end)
            elif b == text[0]:
                if a and re.match(r"[A-Za-z_]", a) is not None:
                    Data['text_buffer'][page].remove_tag_by_name(
                        'syntax_k2', match_start, match_end)
            self.syntax_key2(text, match_end, color)

    def syntax_oper(self, text, start):
        global current_tag
        current = self.current
        page = current-1
        color = Syntax_Colors['syntax_oper']
        end = Data['text_buffer'][page].get_end_iter()
        if Data['text_buffer'][page].get_tag_table().lookup('syntax_oper') == None:
            current_tag = Data['text_buffer'][page].create_tag(
                'syntax_oper', foreground=color)
            current_tag.set_priority(0)
        current_tag.set_property('foreground', color)
        match = start.forward_search(text, 0, end)
        if match is not None:
            match_start, match_end = match
            Data['text_buffer'][page].apply_tag_by_name(
                'syntax_oper', match_start, match_end)
            self.syntax_oper(text, match_end)

    def quote(self, text, start):
        #TODO: Does not perform well with reg_exp
        global current_tag
        current = self.current
        page = current-1
        _tog_q = {
            '\'':'\"',
            '\"':'\'',
            '\"\"\"':'\"',
        }
        color = Syntax_Colors['syntax_quote']
        end = Data['text_buffer'][page].get_end_iter()
        st = Data['text_buffer'][page].get_start_iter()
        if Data['text_buffer'][page].get_tag_table().lookup('q_t') == None:
            current_tag = Data['text_buffer'][page].create_tag(
                'q_t', foreground=color)
            current_tag.set_priority(4)
        current_tag.set_property('foreground', color)
        match = start.forward_search(text, 0, end)
        if match is not None:
            match_start, match_end = match
            sm = match_end.forward_search(text, 0, end)
            _cse = match_start.backward_search('#', 0, st)
            _cse2 = match_start.backward_search(_tog_q[text], 0, st)
            if _cse is not None:
                _c_s, _c_e = _cse
                if match_start.get_line() == _c_e.get_line():
                    match_end.forward_lines(2)
                    self.quote(text, match_end)
                elif _cse2 is not None:
                    _c_s2, _c_e2 = _cse
                    if match_start.get_line() == _c_e.get_line():
                        match_end.forward_lines(2)
                        self.quote(text, match_end)
                    elif sm is not None:
                        sm_s, sm_e = sm
                        sm_s.forward_char()
                        Data['text_buffer'][page].apply_tag_by_name(
                            'q_t', match_start, sm_s)
                        self.quote(text, sm_e)
                elif sm is not None:
                    sm_s, sm_e = sm
                    sm_s.forward_char()
                    Data['text_buffer'][page].apply_tag_by_name(
                        'q_t', sm_s,match_start)
                    self.quote(text, sm_s)
            elif sm is not None:
                sm_s, sm_e = sm
                sm_s.forward_char()
                Data['text_buffer'][page].apply_tag_by_name(
                    'q_t', match_start, sm_s)
                self.quote(text, sm_e)

    def comment(self, start):
        global current_tag
        current = self.current
        page = current-1
        color = Syntax_Colors['comment']
        end = Data['text_buffer'][page].get_end_iter()
        if Data['text_buffer'][page].get_tag_table().lookup('comment') == None:
            current_tag = Data['text_buffer'][page].create_tag(
                'comment', foreground=color)
            current_tag.set_priority(5)
        current_tag.set_property('foreground', color)
        match = start.forward_search('#', 0, end)
        matchb = start.forward_search('#', 0, end)
        if match is not None:
            match_start, match_end = match
            if matchb is not None:
                m_s_a, m_s_b = matchb
                m_s_a.forward_to_line_end()
                Data['text_buffer'][page].apply_tag_by_name(
                    'comment', match_start, m_s_a)
                self.comment(m_s_a)