import curses
import time
import re
import copy
import json
import sys
import argparse

# ==========================================================
# VB1-DOS Clone: Python curses IDE (Colors & New Events)
# ==========================================================

PYTHON_KEYWORDS = {
    "def", "class", "if", "elif", "else", "while", "for", "in", 
    "return", "pass", "import", "from", "and", "or", "not", 
    "True", "False", "None", "try", "except", "with", "as", 
    "global", "nonlocal", "break", "continue", "print", "exec"
}

def tokenize_python(line):
    pattern = re.compile(r'(#.*)|(".*?"|\'.*?\')|([a-zA-Z_]\w*)|([0-9]+(?:\.[0-9]*)?)|(\s+|.)')
    tokens = []
    for match in pattern.finditer(line):
        comment, string, word, number, other = match.groups()
        if comment:
            tokens.append((comment, 'comment'))
        elif string:
            tokens.append((string, 'string'))
        elif word:
            if word in PYTHON_KEYWORDS:
                tokens.append((word, 'keyword'))
            else:
                tokens.append((word, 'text'))
        elif number:
            tokens.append((number, 'number'))
        elif other:
            tokens.append((other, 'text'))
    return tokens

class MenuItem:
    def __init__(self, label, name):
        self.label = label
        self.name = name
        self.name_id = name 
        self.sub = []
        self.code = f"def {name}_clicked():\n    pass\n"

    def to_dict(self):
        return {
            'label': self.label, 
            'name': self.name, 
            'code': self.code, 
            'sub': [s.to_dict() for s in self.sub]
        }

    @classmethod
    def from_dict(cls, data):
        m = cls(data['label'], data['name'])
        m.code = data.get('code', f"def {data['name']}_clicked():\n    pass\n")
        m.sub = [cls.from_dict(s) for s in data.get('sub', [])]
        return m

def flatten_menus(menus, depth=0):
    flat = []
    for m in menus:
        flat.append((m, depth, menus))
        flat.extend(flatten_menus(m.sub, depth+1))
    return flat

class UIControl:
    def __init__(self, x, y, w, h, tool_type, name_id, caption):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.tool_type = tool_type
        self.name_id = name_id
        self.caption = caption
        self.code = "" 
        self.value = False
        self.items = []
        self.list_index = 0
        self.scroll_offset = 0
        self.interval = 1000 
        self.last_tick = 0   
        self.bg_color = 12 

    def to_dict(self):
        return {
            'x': self.x, 'y': self.y, 'w': self.w, 'h': self.h,
            'tool_type': self.tool_type, 'name_id': self.name_id,
            'caption': self.caption, 'code': self.code, 'value': self.value,
            'items': self.items, 'list_index': self.list_index, 
            'scroll_offset': self.scroll_offset, 'interval': self.interval,
            'bg_color': self.bg_color
        }

    @classmethod
    def from_dict(cls, data):
        c = cls(data['x'], data['y'], data['w'], data['h'], 
                data['tool_type'], data['name_id'], data['caption'])
        c.code = data.get('code', '')
        c.value = data.get('value', False)
        c.items = data.get('items', [])
        c.list_index = data.get('list_index', 0)
        c.scroll_offset = data.get('scroll_offset', 0)
        c.interval = data.get('interval', 1000)
        c.bg_color = data.get('bg_color', 12)
        return c

class Window:
    def __init__(self, x, y, w, h, title="untitled", name_id="Form1"):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.title = title
        self.name_id = name_id
        self.controls = []
        self.pinned_topmost = False
        self.resizable = True
        self.menus = []
        self.code = ""

    def to_dict(self):
        return {
            'x': self.x, 'y': self.y, 'w': self.w, 'h': self.h,
            'title': self.title, 'name_id': self.name_id,
            'pinned_topmost': self.pinned_topmost,
            'resizable': self.resizable,
            'menus': [m.to_dict() for m in self.menus],
            'controls': [c.to_dict() for c in self.controls],
            'code': self.code
        }

    @classmethod
    def from_dict(cls, data):
        w = cls(data['x'], data['y'], data['w'], data['h'], data.get('title', 'untitled'), data.get('name_id', 'Form1'))
        w.pinned_topmost = data.get('pinned_topmost', False)
        w.resizable = data.get('resizable', True)
        w.menus = [MenuItem.from_dict(m) for m in data.get('menus', [])]
        w.controls = [UIControl.from_dict(c) for c in data.get('controls', [])]
        w.code = data.get('code', '')
        return w

    def add_control(self, cx, cy, ctype, ctitle):
        if len(self.controls) < 30:
            name_id = f"ctrl{len(self.controls) + 1}"
            if ctype == 3:  
                ctrl = UIControl(cx, cy, 12, 3, ctype, name_id, "Button")
            elif ctype == 13: 
                ctrl = UIControl(cx, cy, 15, 1, ctype, name_id, "")
            elif ctype == 7: 
                ctrl = UIControl(cx, cy, 20, 8, ctype, name_id, "Frame1")
            elif ctype == 1: 
                ctrl = UIControl(cx, cy, 15, 1, ctype, name_id, "Check1")
            elif ctype == 11: 
                ctrl = UIControl(cx, cy, 15, 1, ctype, name_id, "Option1")
            elif ctype == 2:
                ctrl = UIControl(cx, cy, 15, 1, ctype, name_id, "Combo1")
                ctrl.items = ["Item 1", "Item 2", "Item 3"]
            elif ctype == 10:
                ctrl = UIControl(cx, cy, 15, 4, ctype, name_id, "List1")
                ctrl.items = ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"]
            elif ctype == 14:
                ctrl = UIControl(cx, cy, 10, 1, ctype, name_id, "Timer1")
            else:
                ctrl = UIControl(cx, cy, 12, 1, ctype, name_id, ctitle.strip())
            self.controls.append(ctrl)

    def get_parent_frame(self, ctrl):
        best_frame = None
        for c in self.controls:
            if c.tool_type == 7 and c != ctrl:
                if c.x <= ctrl.x and c.y <= ctrl.y and \
                   c.x + c.w >= ctrl.x + ctrl.w and \
                   c.y + c.h >= ctrl.y + ctrl.h:
                    best_frame = c
        return best_frame

    def draw(self, stdscr, colors, active_ctrl=-1, pressed_ctrl=-1, run_mode=False):
        C_BORDER = colors['border']
        C_BG = colors['bg']
        C_BTN_FACE = colors['btn_face']
        C_BTN_HL = colors['btn_hl']
        C_TEXTBOX = colors['textbox']
        C_HANDLE = colors['handle']

        write_at(stdscr, self.x, self.y, "┌" + "─" * (self.w - 2) + "┐", C_BORDER)
        for i in range(1, self.h - 1):
            write_at(stdscr, self.x, self.y + i, "│", C_BORDER)
            write_at(stdscr, self.x + 1, self.y + i, " " * (self.w - 2), C_BG)
            write_at(stdscr, self.x + self.w - 1, self.y + i, "│", C_BORDER)
        write_at(stdscr, self.x, self.y + self.h - 1, "└" + "─" * (self.w - 2) + "┘", C_BORDER)

        title_str = f" {self.title} "
        tx = self.x + (self.w // 2) - (len(title_str) // 2)
        write_at(stdscr, tx, self.y, title_str, C_BORDER)

        def write_clipped(cx, cy, text, attr):
            if cy <= self.y or cy >= self.y + self.h - 1:
                return
            min_x = self.x + 1
            max_x = self.x + self.w - 2
            
            if cx > max_x or cx + len(text) - 1 < min_x:
                return
                
            start_idx = max(0, min_x - cx)
            end_idx = min(len(text), max_x - cx + 1)
            
            actual_x = cx + start_idx
            clipped_text = text[start_idx:end_idx]
            
            if clipped_text:
                write_at(stdscr, actual_x, cy, clipped_text, attr)

        for i, c in enumerate(self.controls):
            if run_mode and c.tool_type == 14:
                continue 

            draw_x = self.x + c.x
            draw_y = self.y + c.y

            if c.tool_type == 3: 
                is_pressed = (i == pressed_ctrl)
                TOP_C = C_BTN_FACE if is_pressed else C_BTN_HL
                BOT_C = C_BTN_HL if is_pressed else C_BTN_FACE

                actual_h = max(3, c.h)
                write_clipped(draw_x, draw_y, "┌" + "─" * (c.w - 2), TOP_C)
                write_clipped(draw_x + c.w - 1, draw_y, "┐", BOT_C)
                
                base_color = curses.color_pair(c.bg_color)
                
                for r in range(1, actual_h - 1):
                    write_clipped(draw_x, draw_y + r, "│", TOP_C)
                    if r == actual_h // 2:
                        pad = (c.w - 2 - len(c.caption)) // 2
                        if is_pressed: pad += 1 
                        text = (" " * pad + c.caption + " " * (c.w - 2))[:c.w - 2]
                        write_clipped(draw_x + 1, draw_y + r, text, base_color)
                    else:
                        write_clipped(draw_x + 1, draw_y + r, " " * (c.w - 2), base_color)
                    write_clipped(draw_x + c.w - 1, draw_y + r, "│", BOT_C)
                
                write_clipped(draw_x, draw_y + actual_h - 1, "└", TOP_C)
                write_clipped(draw_x + 1, draw_y + actual_h - 1, "─" * (c.w - 2) + "┘", BOT_C)

            elif c.tool_type == 13: 
                for r in range(c.h):
                    if r == 0:
                        display_text = c.caption
                        if len(display_text) >= c.w:
                            display_text = display_text[-(c.w-1):]
                        text = (display_text + " " * c.w)[:c.w]
                        write_clipped(draw_x, draw_y + r, text, C_TEXTBOX)
                    else:
                        write_clipped(draw_x, draw_y + r, " " * c.w, C_TEXTBOX)
                        
            elif c.tool_type == 2: 
                disp_text = c.caption
                if c.items and 0 <= c.list_index < len(c.items):
                    disp_text = c.items[c.list_index]
                text = (disp_text + " " * c.w)[:c.w-1] + "▼"
                write_clipped(draw_x, draw_y, text, C_TEXTBOX)

            elif c.tool_type == 10: 
                for r in range(c.h):
                    idx = c.scroll_offset + r
                    if c.items and 0 <= idx < len(c.items):
                        disp_text = c.items[idx]
                        text = (disp_text + " " * c.w)[:c.w]
                        attr = C_HANDLE if idx == c.list_index else C_TEXTBOX
                        write_clipped(draw_x, draw_y + r, text, attr)
                    else:
                        write_clipped(draw_x, draw_y + r, " " * c.w, C_TEXTBOX)

            elif c.tool_type == 14: 
                write_clipped(draw_x, draw_y, ("[⏱] " + c.name_id)[:c.w], C_TEXTBOX)

            elif c.tool_type == 7: 
                write_clipped(draw_x, draw_y, "┌" + "─" * (c.w - 2) + "┐", C_BORDER)
                for r in range(1, c.h - 1):
                    write_clipped(draw_x, draw_y + r, "│", C_BORDER)
                    write_clipped(draw_x + 1, draw_y + r, " " * (c.w - 2), C_BG)
                    write_clipped(draw_x + c.w - 1, draw_y + r, "│", C_BORDER)
                write_clipped(draw_x, draw_y + c.h - 1, "└" + "─" * (c.w - 2) + "┘", C_BORDER)
                cap_str = f" {c.caption} "
                if len(cap_str) <= c.w - 2:
                    write_clipped(draw_x + 2, draw_y, cap_str, C_BORDER)
                    
            elif c.tool_type == 1: 
                for r in range(c.h):
                    if r == 0:
                        mark = "X" if c.value else " "
                        text = (f"[{mark}] {c.caption}" + " " * c.w)[:c.w]
                        write_clipped(draw_x, draw_y + r, text, C_TEXTBOX)
                    else:
                        write_clipped(draw_x, draw_y + r, " " * c.w, C_TEXTBOX)
                        
            elif c.tool_type == 11: 
                for r in range(c.h):
                    if r == 0:
                        mark = "•" if c.value else " "
                        text = (f"({mark}) {c.caption}" + " " * c.w)[:c.w]
                        write_clipped(draw_x, draw_y + r, text, C_TEXTBOX)
                    else:
                        write_clipped(draw_x, draw_y + r, " " * c.w, C_TEXTBOX)
                        
            else:  
                for r in range(c.h):
                    if r == 0:
                        text = (c.caption + " " * c.w)[:c.w]
                        write_clipped(draw_x, draw_y + r, text, C_TEXTBOX)
                    else:
                        write_clipped(draw_x, draw_y + r, " " * c.w, C_TEXTBOX)

        if not run_mode and active_ctrl >= 0 and active_ctrl < len(self.controls):
            c = self.controls[active_ctrl]
            hx = self.x + c.x + c.w
            hy = self.y + c.y + c.h
            write_clipped(hx, hy, "■", C_HANDLE)

    def hit_test(self, mx, my):
        return (self.x <= mx < self.x + self.w) and (self.y <= my < self.y + self.h)

    def hit_control(self, lx, ly):
        if lx <= 0 or lx >= self.w - 1 or ly <= 0 or ly >= self.h - 1:
            return -1 
        for i in range(len(self.controls) - 1, -1, -1):
            c = self.controls[i]
            if (c.x <= lx < c.x + c.w) and (c.y <= ly < c.y + c.h):
                return i
        return -1

class Toolbox:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 16
        self.h = 20
        self.active_tool = -1
        self.items = [
            "Move/Size", "Check Box", "Combo Box", "Command Btn",
            "Dir List", "Drive List", "File List", "Frame",
            "HScrollBar", "Label", "List Box", "Option Btn",
            "Picture Box", "Text Box", "Timer", "VScrollBar"
        ]

    def draw(self, stdscr, colors):
        C_TB = colors['textbox']
        C_ACTIVE = colors['active_tool']

        write_at(stdscr, self.x, self.y, "┌" + "─" * (self.w - 2) + "┐", C_TB)
        write_at(stdscr, self.x + (self.w // 2) - 3, self.y, "-Tools-", C_TB)
        
        curr_y = self.y + 1
        write_at(stdscr, self.x, curr_y, "│", C_TB)
        text = (self.items[0] + " " * (self.w - 2))[:self.w - 2]
        write_at(stdscr, self.x + 1, curr_y, text, C_ACTIVE if self.active_tool == 0 else C_TB)
        write_at(stdscr, self.x + self.w - 1, curr_y, "│", C_TB)
        curr_y += 1
        
        write_at(stdscr, self.x, curr_y, "├" + "─" * (self.w - 2) + "┤", C_TB)
        curr_y += 1
        
        for i in range(1, 16):
            write_at(stdscr, self.x, curr_y, "│", C_TB)
            text = (self.items[i] + " " * (self.w - 2))[:self.w - 2]
            write_at(stdscr, self.x + 1, curr_y, text, C_ACTIVE if self.active_tool == i else C_TB)
            write_at(stdscr, self.x + self.w - 1, curr_y, "│", C_TB)
            curr_y += 1
            
        write_at(stdscr, self.x, curr_y, "└" + "─" * (self.w - 2) + "┘", C_TB)

    def process_click(self, mx, my):
        if self.x <= mx < self.x + self.w:
            if my == self.y + 1:
                self.active_tool = 0
                return True
            elif self.y + 3 <= my <= self.y + 17:
                self.active_tool = my - (self.y + 2)
                return True
        return False

def write_at(stdscr, x, y, text, attr=0):
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass

def draw_properties(stdscr, prop_win, selected_win, selected_ctrl_idx, editing_prop, edit_buffer, colors, tools):
    C_BG = colors['bg']
    C_TB = colors['textbox']
    C_LABEL = colors['prop_label']
    
    for py in range(1, prop_win.h - 1):
        write_at(stdscr, prop_win.x + 1, prop_win.y + py, " " * (prop_win.w - 2), C_BG)

    def draw_prop(ly, lbl, p_id, val_str):
        write_at(stdscr, prop_win.x + 2, prop_win.y + ly, lbl, C_LABEL)
        if editing_prop == p_id:
            eb = edit_buffer + "_"
            display_text = eb[-10:] if len(eb) > 10 else (eb + "          ")[:10]
        else:
            vs = str(val_str)
            display_text = vs[:10] if len(vs) > 10 else (vs + "          ")[:10]
        write_at(stdscr, prop_win.x + 8, prop_win.y + ly, display_text, C_TB)

    if selected_win is not None and selected_ctrl_idx >= 0:
        c = selected_win.controls[selected_ctrl_idx]
        tool_name = "Timer" if c.tool_type == 14 else tools.items[c.tool_type].strip()
        
        write_at(stdscr, prop_win.x + 2, prop_win.y + 2, f"Type: {tool_name}", C_LABEL)
        write_at(stdscr, prop_win.x + 1, prop_win.y + 3, "─" * (prop_win.w - 2), C_BG)

        draw_prop(5, "Name:", 1, c.name_id)
        draw_prop(6, "Cap: ", 2, c.caption)
        draw_prop(7, "X:   ", 3, c.x)
        draw_prop(8, "Y:   ", 4, c.y)
        draw_prop(9, "W:   ", 5, c.w)
        draw_prop(10,"H:   ", 6, c.h)
        
        if c.tool_type in (1, 11): 
            write_at(stdscr, prop_win.x + 2, prop_win.y + 11, "Val: ", C_LABEL)
            mark = "X" if c.value else " "
            write_at(stdscr, prop_win.x + 8, prop_win.y + 11, f"[{mark}]       ", C_TB)
            
        if c.tool_type in (2, 10):
            draw_prop(11,"Items:", 8, ",".join(c.items))
            draw_prop(12,"Idx: ", 9, str(c.list_index))
            
        if c.tool_type == 14:
            draw_prop(11,"Intrv:", 7, str(c.interval))
            
        if c.tool_type == 3: 
            write_at(stdscr, prop_win.x + 2, prop_win.y + 11, "Color:", C_LABEL)
            palette = [12, 13, 14, 15, 16, 17] 
            for p_idx, p_color in enumerate(palette):
                write_at(stdscr, prop_win.x + 9 + (p_idx * 2), prop_win.y + 11, "  ", curses.color_pair(p_color))

    elif selected_win is not None and selected_ctrl_idx == -1:
        w = selected_win
        write_at(stdscr, prop_win.x + 2, prop_win.y + 2, f"Type: Form", C_LABEL)
        write_at(stdscr, prop_win.x + 1, prop_win.y + 3, "─" * (prop_win.w - 2), C_BG)

        draw_prop(5, "Name:", 1, w.name_id)
        draw_prop(6, "Cap: ", 2, w.title)
        draw_prop(7, "X:   ", 3, w.x)
        draw_prop(8, "Y:   ", 4, w.y)
        draw_prop(9, "W:   ", 5, w.w)
        draw_prop(10,"H:   ", 6, w.h)
        draw_prop(11,"Pinned:", 7, "[X]" if w.pinned_topmost else "[ ]")
        draw_prop(12,"Resiz:", 8, "[X]" if w.resizable else "[ ]")
    else:
        write_at(stdscr, prop_win.x + 2, prop_win.y + 2, "No selection.", C_LABEL)

def draw_code_editor(stdscr, lines, cy, cx, target_name, box_x, box_y, box_w, box_h, colors):
    C_BORDER = colors['border']
    C_BG = colors['bg']
    
    write_at(stdscr, box_x, box_y, "┌" + "─" * (box_w - 2) + "┐", C_BORDER)
    for i in range(1, box_h - 1):
        write_at(stdscr, box_x, box_y + i, "│", C_BORDER)
        write_at(stdscr, box_x + box_w - 1, box_y + i, "│", C_BORDER)
        
        line_idx = i - 1
        if line_idx < len(lines):
            line_text = lines[line_idx]
            tokens = tokenize_python(line_text)
            
            curr_x = box_x + 1
            chars_printed = 0
            
            for text_chunk, ttype in tokens:
                if chars_printed >= box_w - 2:
                    break
                    
                space_left = (box_w - 2) - chars_printed
                render_str = text_chunk[:space_left]
                
                attr = C_BG
                if ttype == 'keyword': attr = colors['kw']
                elif ttype == 'string': attr = colors['str']
                elif ttype == 'number': attr = colors['num']
                elif ttype == 'comment': attr = colors['comment']
                
                write_at(stdscr, curr_x, box_y + i, render_str, attr)
                curr_x += len(render_str)
                chars_printed += len(render_str)
            
            if chars_printed < box_w - 2:
                write_at(stdscr, curr_x, box_y + i, " " * ((box_w - 2) - chars_printed), C_BG)
        else:
            write_at(stdscr, box_x + 1, box_y + i, " " * (box_w - 2), C_BG)
            
    write_at(stdscr, box_x, box_y + box_h - 1, "└" + "─" * (box_w - 2) + "┘", C_BORDER)
    
    title = f" Code: {target_name} "
    write_at(stdscr, box_x + (box_w - len(title))//2, box_y, title, C_BORDER)
    write_at(stdscr, box_x + box_w - 4, box_y, "[X]", C_BORDER)

    if cy < box_h - 2:
        real_x = box_x + 1 + min(cx, box_w - 3)
        real_y = box_y + 1 + cy
        try:
            stdscr.move(real_y, real_x)
        except curses.error:
            pass

def handle_combobox_dropdown(stdscr, dx, dy, w, items, colors):
    if not items: return None
    C_BORDER = colors['border']
    C_BG = colors['bg']
    C_HL = colors['handle']
    
    h = min(len(items) + 2, 10)
    if dy + h >= curses.LINES:
        dy = curses.LINES - h
        
    scroll = 0
    selected = 0
    
    while True:
        write_at(stdscr, dx, dy, "┌" + "─" * (w - 2) + "┐", C_BORDER)
        for r in range(h - 2):
            idx = scroll + r
            write_at(stdscr, dx, dy + 1 + r, "│", C_BORDER)
            if idx < len(items):
                text = (items[idx] + " " * (w - 2))[:w - 2]
                attr = C_HL if idx == selected else C_BG
                write_at(stdscr, dx + 1, dy + 1 + r, text, attr)
            else:
                write_at(stdscr, dx + 1, dy + 1 + r, " " * (w - 2), C_BG)
            write_at(stdscr, dx + w - 1, dy + 1 + r, "│", C_BORDER)
        write_at(stdscr, dx, dy + h - 1, "└" + "─" * (w - 2) + "┘", C_BORDER)
        stdscr.refresh()
        
        ch = stdscr.getch()
        if ch == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                if bstate & curses.BUTTON1_PRESSED or bstate & curses.BUTTON1_CLICKED:
                    if dx < mx < dx + w and dy < my < dy + h:
                        click_r = my - dy - 1
                        click_idx = scroll + click_r
                        if 0 <= click_idx < len(items):
                            return click_idx
                    else:
                        return None
            except curses.error: pass
        elif ch == 27: return None
        elif ch == curses.KEY_UP:
            selected = max(0, selected - 1)
            if selected < scroll: scroll = selected
        elif ch == curses.KEY_DOWN:
            selected = min(len(items) - 1, selected + 1)
            if selected >= scroll + (h - 2): scroll = selected - (h - 3)
        elif ch in (10, 13, curses.KEY_ENTER):
            return selected
        time.sleep(0.01)

def draw_msgbox(stdscr, msg, colors):
    C_BORDER = colors['border']
    C_BG = colors['bg']
    lines = msg.split('\n')
    w = max([len(l) for l in lines] + [20]) + 4
    h = len(lines) + 4
    x = (curses.COLS - w) // 2
    y = (curses.LINES - h) // 2
    
    write_at(stdscr, x, y, "┌" + "─" * (w - 2) + "┐", C_BORDER)
    for i in range(1, h - 1):
        write_at(stdscr, x, y + i, "│", C_BORDER)
        write_at(stdscr, x + 1, y + i, " " * (w - 2), C_BG)
        write_at(stdscr, x + w - 1, y + i, "│", C_BORDER)
    write_at(stdscr, x, y + h - 1, "└" + "─" * (w - 2) + "┘", C_BORDER)
    
    for i, l in enumerate(lines):
        write_at(stdscr, x + 2, y + 2 + i, l, C_BG)
    
    write_at(stdscr, x + (w - 6) // 2, y + h - 2, "[ OK ]", C_BORDER)

def show_sync_msgbox(stdscr, msg, colors):
    draw_msgbox(stdscr, msg, colors)
    stdscr.refresh()
    while True:
        ch = stdscr.getch()
        if ch == curses.KEY_MOUSE:
            try:
                _, _, _, _, bstate = curses.getmouse()
                if bstate & curses.BUTTON1_PRESSED or bstate & curses.BUTTON1_CLICKED:
                    break
            except curses.error:
                pass
        elif ch in (10, 13, 27) and ch != -1:
            break
        time.sleep(0.01)

def handle_file_menu(stdscr, colors):
    C_BORDER = colors['border']
    C_BG = colors['bg']
    menu_items = [" Save Project As... ", " Load Project...    ", " Exit IDE           "]
    w = 22
    h = len(menu_items) + 2
    x = 1
    y = 1
    
    write_at(stdscr, x, y, "┌" + "─" * (w - 2) + "┐", C_BORDER)
    for i, item in enumerate(menu_items):
        write_at(stdscr, x, y + i + 1, "│", C_BORDER)
        write_at(stdscr, x + 1, y + i + 1, item, C_BG)
        write_at(stdscr, x + w - 1, y + i + 1, "│", C_BORDER)
    write_at(stdscr, x, y + h - 1, "└" + "─" * (w - 2) + "┘", C_BORDER)
    stdscr.refresh()
    
    while True:
        ch = stdscr.getch()
        if ch == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                if bstate & curses.BUTTON1_PRESSED or bstate & curses.BUTTON1_CLICKED:
                    if x < mx < x + w and y < my < y + h:
                        idx = my - y - 1
                        if idx == 0: return 'save'
                        if idx == 1: return 'load'
                        if idx == 2: return 'exit'
                    return None
            except curses.error:
                pass
        elif ch == 27:
            return None
        time.sleep(0.01)

def prompt_input(stdscr, prompt_title, colors):
    C_BORDER = colors['border']
    C_BG = colors['bg']
    C_TB = colors['textbox']
    
    box_w = 40
    box_h = 5
    box_x = (curses.COLS - box_w) // 2
    box_y = (curses.LINES - box_h) // 2
    
    buffer = ""
    while True:
        write_at(stdscr, box_x, box_y, "┌" + "─" * (box_w - 2) + "┐", C_BORDER)
        for i in range(1, box_h - 1):
            write_at(stdscr, box_x, box_y + i, "│", C_BORDER)
            write_at(stdscr, box_x + 1, box_y + i, " " * (box_w - 2), C_BG)
            write_at(stdscr, box_x + box_w - 1, box_y + i, "│", C_BORDER)
        write_at(stdscr, box_x, box_y + box_h - 1, "└" + "─" * (box_w - 2) + "┘", C_BORDER)
        
        title = f" {prompt_title} "
        write_at(stdscr, box_x + (box_w - len(title))//2, box_y, title, C_BORDER)
        write_at(stdscr, box_x + 2, box_y + 2, (buffer + "_").ljust(box_w - 4)[:box_w-4], C_TB)
        stdscr.refresh()
        
        ch = stdscr.getch()
        if ch == 27:
            return None
        elif ch in (10, 13, curses.KEY_ENTER):
            return buffer.strip()
        elif ch in (8, 127, curses.KEY_BACKSPACE):
            buffer = buffer[:-1]
        elif 32 <= ch <= 126 and ch != -1:
            if len(buffer) < box_w - 5:
                buffer += chr(ch)
        time.sleep(0.01)

def menu_editor_loop(stdscr, form, colors):
    C_LABEL = colors['prop_label']

    me_win = Window(10, 5, 52, 16, "Menu Editor", "MenuEditor")
    me_win.resizable = False
    
    me_win.add_control(2, 3, 2, "Selected Menu")
    me_win.controls[0].w = 46
    
    me_win.add_control(2, 6, 3, "Add Top Menu")
    me_win.controls[1].w = 22
    me_win.controls[1].caption = "Add Top Menu"
    
    me_win.add_control(26, 6, 3, "Add Sub Menu")
    me_win.controls[2].w = 22
    me_win.controls[2].caption = "Add Sub Menu"
    
    me_win.add_control(2, 10, 3, "Delete Selected")
    me_win.controls[3].w = 22
    me_win.controls[3].caption = "Delete Menu"
    
    me_win.add_control(26, 10, 3, "Edit Code")
    me_win.controls[4].w = 22
    me_win.controls[4].caption = "Edit Code"
    
    me_win.add_control(14, 13, 3, "Close Editor")
    me_win.controls[5].w = 22
    me_win.controls[5].caption = "OK"

    flat_list = []

    def refresh_combos():
        nonlocal flat_list
        top_combo = me_win.controls[0]
        flat_list = flatten_menus(form.menus)
        
        if not flat_list:
            top_combo.items = ["(None)"]
            top_combo.list_index = 0
        else:
            top_combo.items = [f"{'...' * depth}{m.label} ({m.name})" for m, depth, _ in flat_list]
            if top_combo.list_index >= len(flat_list):
                top_combo.list_index = max(0, len(flat_list) - 1)

    refresh_combos()

    mouse_down = False
    pressed_ctrl = -1

    while True:
        stdscr.clear()
        me_win.draw(stdscr, colors, pressed_ctrl=pressed_ctrl, run_mode=True)
        write_at(stdscr, me_win.x + 2, me_win.y + 2, "Selected Menu:", C_LABEL)
        stdscr.refresh()
        
        ch = stdscr.getch()
        if ch == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                left_click = bool(bstate & curses.BUTTON1_PRESSED) or bool(bstate & curses.BUTTON1_CLICKED)
                mouse_released = bool(bstate & curses.BUTTON1_RELEASED)
                
                if left_click and not mouse_down:
                    mouse_down = True
                    if me_win.hit_test(mx, my):
                        lx = mx - me_win.x
                        ly = my - me_win.y
                        idx = me_win.hit_control(lx, ly)
                        if idx >= 0:
                            c = me_win.controls[idx]
                            if c.tool_type == 3:
                                pressed_ctrl = idx
                            elif c.tool_type == 2:
                                drop_idx = handle_combobox_dropdown(stdscr, me_win.x + c.x, me_win.y + c.y + 1, c.w, c.items, colors)
                                if drop_idx is not None:
                                    c.list_index = drop_idx
                                    refresh_combos()
                elif mouse_released:
                    mouse_down = False
                    if pressed_ctrl >= 0:
                        if me_win.hit_test(mx, my):
                            lx = mx - me_win.x
                            ly = my - me_win.y
                            if me_win.hit_control(lx, ly) == pressed_ctrl:
                                if pressed_ctrl == 1: 
                                    lbl = prompt_input(stdscr, "Top Menu Label:", colors)
                                    if lbl:
                                        nm = prompt_input(stdscr, "Func (e.g. mnu_file):", colors)
                                        if nm:
                                            form.menus.append(MenuItem(lbl, nm))
                                            refresh_combos()
                                            me_win.controls[0].list_index = len(flat_list) - 1
                                elif pressed_ctrl == 2: 
                                    if flat_list:
                                        sel_menu, _, _ = flat_list[me_win.controls[0].list_index]
                                        lbl = prompt_input(stdscr, "Sub-Menu Label:", colors)
                                        if lbl:
                                            nm = prompt_input(stdscr, "Function Name:", colors)
                                            if nm:
                                                sel_menu.sub.append(MenuItem(lbl, nm))
                                                refresh_combos()
                                                me_win.controls[0].list_index += len(sel_menu.sub) 
                                elif pressed_ctrl == 3: 
                                    if flat_list:
                                        target, _, parent_list = flat_list[me_win.controls[0].list_index]
                                        parent_list.remove(target)
                                        refresh_combos()
                                elif pressed_ctrl == 4: 
                                    if flat_list:
                                        target, _, _ = flat_list[me_win.controls[0].list_index]
                                        return ('edit_code', target)
                                elif pressed_ctrl == 5: 
                                    return ('quit', None)
                        pressed_ctrl = -1
            except curses.error:
                pass
        elif ch == 27:
            return ('quit', None)
        time.sleep(0.01)

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    curses.mouseinterval(0) 
    print('\033[?1003h', end='', flush=True) 

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)   
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_WHITE)   
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)    
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)   
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)    
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_WHITE)   
    
    curses.init_pair(8, curses.COLOR_BLUE, curses.COLOR_WHITE)    
    curses.init_pair(9, curses.COLOR_GREEN, curses.COLOR_WHITE)   
    curses.init_pair(10, curses.COLOR_RED, curses.COLOR_WHITE)    
    curses.init_pair(11, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
    
    curses.init_pair(12, curses.COLOR_BLACK, curses.COLOR_WHITE)   
    curses.init_pair(13, curses.COLOR_WHITE, curses.COLOR_BLUE)    
    curses.init_pair(14, curses.COLOR_BLACK, curses.COLOR_GREEN)   
    curses.init_pair(15, curses.COLOR_WHITE, curses.COLOR_RED)     
    curses.init_pair(16, curses.COLOR_BLACK, curses.COLOR_CYAN)    
    curses.init_pair(17, curses.COLOR_WHITE, curses.COLOR_MAGENTA) 

    C = {
        'border': curses.color_pair(1) | curses.A_BOLD,
        'bg': curses.color_pair(2),
        'btn_face': curses.color_pair(2),
        'btn_hl': curses.color_pair(3) | curses.A_BOLD,
        'textbox': curses.color_pair(4),
        'handle': curses.color_pair(5),
        'active_tool': curses.color_pair(6) | curses.A_BOLD,
        'prop_label': curses.color_pair(7),
        'kw': curses.color_pair(8) | curses.A_BOLD,
        'str': curses.color_pair(9),
        'comment': curses.color_pair(10),
        'num': curses.color_pair(11)
    }

    tools = Toolbox(0, 1)
    main_form = Window(17, 1, 41, 18, "Form 1", "Form1")
    prop_win = Window(48, 8, 22, 14, "Properties", "Properties")
    
    windows = [main_form, prop_win]

    selected_win = main_form
    selected_ctrl_idx = -1
    editing_prop = 0 
    edit_buffer = ""

    mx, my, old_mx, old_my = 0, 0, 0, 0
    dragged_win = None
    resizing_win = None 
    dragged_ctrl = -1
    dragged_frame_children = [] 
    dragged_tool = False
    resizing_ctrl = False
    mouse_down = False
    drag_offset_x, drag_offset_y = 0, 0

    last_click_time = 0.0
    last_click_x = -1
    last_click_y = -1
    
    code_mode = False
    code_lines = []
    code_cx, code_cy = 0, 0
    code_target_ctrl = None
    
    run_mode = False
    run_globals = {}
    run_focused_ctrl = -1 
    run_pressed_ctrl = -1 
    design_backup = None

    def commit_edit():
        nonlocal editing_prop, edit_buffer, selected_win, selected_ctrl_idx
        if editing_prop > 0 and selected_win is not None:
            if selected_ctrl_idx >= 0:
                c = selected_win.controls[selected_ctrl_idx]
                try:
                    if editing_prop == 1: c.name_id = edit_buffer
                    elif editing_prop == 2: c.caption = edit_buffer
                    elif editing_prop == 3: c.x = int(edit_buffer)
                    elif editing_prop == 4: c.y = int(edit_buffer)
                    elif editing_prop == 5: c.w = int(edit_buffer)
                    elif editing_prop == 6: c.h = int(edit_buffer)
                    elif editing_prop == 7: c.interval = int(edit_buffer) if edit_buffer.isdigit() else 1000
                    elif editing_prop == 8: c.items = [s.strip() for s in edit_buffer.split(',')] if edit_buffer else []
                    elif editing_prop == 9: c.list_index = int(edit_buffer) if edit_buffer.lstrip('-').isdigit() else 0
                except ValueError:
                    pass 
                c.w = max(4, c.w)
                c.h = max(3 if c.tool_type in (3, 7) else 1, c.h)
                c.x = max(1, min(c.x, selected_win.w - c.w - 1))
                c.y = max(1, min(c.y, selected_win.h - c.h - 1))
            else:
                w = selected_win
                try:
                    if editing_prop == 1: w.name_id = edit_buffer
                    elif editing_prop == 2: w.title = edit_buffer
                    elif editing_prop == 3: w.x = int(edit_buffer)
                    elif editing_prop == 4: w.y = int(edit_buffer)
                    elif editing_prop == 5: w.w = int(edit_buffer)
                    elif editing_prop == 6: w.h = int(edit_buffer)
                except ValueError:
                    pass
                w.w = max(10, w.w)
                w.h = max(5, w.h)
                w.x = max(0, min(w.x, curses.COLS - w.w))
                w.y = max(1, min(w.y, curses.LINES - w.h))
                
        editing_prop = 0

    parser = argparse.ArgumentParser()
    parser.add_argument("-run", help="Path to script.json for run mode")
    args, _ = parser.parse_known_args()
    
    if args.run:
        try:
            with open(args.run, 'r', encoding='utf-8') as f:
                data = json.load(f)
            main_form = Window.from_dict(data)
            windows[0] = main_form
            
            design_backup = copy.deepcopy(main_form)
            run_mode = True
            run_focused_ctrl = -1
            run_globals = {'__msg__': None}
            def _msgbox(text): run_globals['__msg__'] = str(text)
            run_globals['msgbox'] = _msgbox
            
            current_time_ms = time.time() * 1000
            for w in [main_form]:
                if w.code:
                    try: exec(w.code, run_globals)
                    except Exception as e: _msgbox(f"Compile Error in {w.name_id}:\n{e}")
                for c in w.controls:
                    run_globals[c.name_id] = c
                    if c.tool_type == 14:
                        c.last_tick = current_time_ms
            
            for w in [main_form]:
                for c in w.controls:
                    if c.code:
                        try: exec(c.code, run_globals)
                        except Exception as e: _msgbox(f"Compile Error in {c.name_id}:\n{e}")
                        
            for m, _, _ in flatten_menus(main_form.menus):
                if m.code:
                    try: exec(m.code, run_globals)
                    except Exception as e: _msgbox(f"Compile Error in {m.name_id}:\n{e}")
                    
            if "on_form_load" in run_globals:
                try: run_globals["on_form_load"]()
                except Exception as e: _msgbox(f"Runtime Error in on_form_load:\n{e}")
        except Exception as e:
            pass

    stdscr.clear()

    while True:
        box_w = max(50, curses.COLS - 10)
        box_h = max(15, curses.LINES - 6)
        box_x = (curses.COLS - box_w) // 2
        box_y = (curses.LINES - box_h) // 2

        if run_mode:
            current_time_ms = time.time() * 1000
            for w in [main_form]:
                for c in w.controls:
                    if c.tool_type == 14: 
                        if not hasattr(c, 'last_tick'): c.last_tick = current_time_ms
                        if current_time_ms - getattr(c, 'last_tick', 0) >= c.interval:
                            c.last_tick = current_time_ms
                            fn = f"on_tick_{c.name_id}"
                            if fn in run_globals:
                                try: run_globals[fn]()
                                except Exception as e: run_globals['__msg__'] = f"Timer Error:\n{e}"

        current_pressed_idx = -1
        if mouse_down:
            if run_mode and run_pressed_ctrl >= 0:
                win = main_form
                if win.hit_test(mx, my) and win.hit_control(mx - win.x, my - win.y) == run_pressed_ctrl:
                    current_pressed_idx = run_pressed_ctrl
            elif not run_mode and dragged_ctrl >= 0:
                current_pressed_idx = dragged_ctrl

        if code_mode:
            draw_code_editor(stdscr, code_lines, code_cy, code_cx, code_target_ctrl.name_id, box_x, box_y, box_w, box_h, C)
            curses.curs_set(1) 
        else:
            if run_mode and run_focused_ctrl >= 0 and main_form.controls[run_focused_ctrl].tool_type == 13:
                c = main_form.controls[run_focused_ctrl]
                cursor_y = main_form.y + c.y
                display_text = c.caption
                if len(display_text) >= c.w:
                    display_text = display_text[-(c.w-1):]
                cursor_x = main_form.x + c.x + len(display_text)
                
                if (cursor_y > main_form.y and cursor_y < main_form.y + main_form.h - 1 and
                    cursor_x > main_form.x and cursor_x < main_form.x + main_form.w - 1):
                    try:
                        stdscr.move(cursor_y, cursor_x)
                        curses.curs_set(1)
                    except curses.error:
                        curses.curs_set(0)
                else:
                    curses.curs_set(0) 
            else:
                curses.curs_set(0) 
            
            menu_positions = []
            stop_pos = (0, 0)
            
            if run_mode:
                write_at(stdscr, 0, 0, " " * curses.COLS, C['handle'])
                menu_x = 1
                for m in main_form.menus:
                    lbl = f" {m.label} "
                    write_at(stdscr, menu_x, 0, lbl, C['handle'])
                    menu_positions.append((menu_x, menu_x + len(lbl), m))
                    menu_x += len(lbl)
                
                stop_lbl = " [STOP] "
                menu_x += 2
                write_at(stdscr, menu_x, 0, stop_lbl, C['handle'])
                stop_pos = (menu_x, menu_x + len(stop_lbl))
            else:
                menu_str = " File  Edit  View [RUN ] Menu Editor  Options"
                write_at(stdscr, 0, 0, menu_str + " " * max(0, curses.COLS - len(menu_str)), C['handle'])
                tools.draw(stdscr, C)
            
            for win in windows:
                if run_mode and win != main_form:
                    continue
                    
                act_idx = selected_ctrl_idx if (win is selected_win and not run_mode) else -1
                press_idx = current_pressed_idx if ((run_mode and win is main_form) or (not run_mode and win is selected_win)) else -1
                
                win.draw(stdscr, C, act_idx, press_idx, run_mode)
                
                if win.name_id == "Properties" and not run_mode:
                    draw_properties(stdscr, win, selected_win, selected_ctrl_idx, editing_prop, edit_buffer, C, tools)

            if run_mode and run_globals.get('__msg__'):
                draw_msgbox(stdscr, run_globals['__msg__'], C)

        stdscr.refresh()
        ch = stdscr.getch()
        
        if ch == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                mouse_moved = (mx != old_mx or my != old_my)
                left_click = bool(bstate & curses.BUTTON1_PRESSED) or bool(bstate & curses.BUTTON1_CLICKED)
                right_click = bool(bstate & curses.BUTTON3_PRESSED) or bool(bstate & curses.BUTTON3_CLICKED)
                mouse_released = bool(bstate & curses.BUTTON1_RELEASED) or bool(bstate & curses.BUTTON3_RELEASED)

                if left_click or right_click:
                    current_time = time.time()
                    is_double_click = False
                    if (current_time - last_click_time < 0.4) and (mx == last_click_x and my == last_click_y):
                        is_double_click = True
                    last_click_time = current_time
                    last_click_x = mx
                    last_click_y = my

                    if not mouse_down:
                        mouse_down = True
                        
                        if code_mode:
                            if box_x + box_w - 5 <= mx <= box_x + box_w - 1 and my == box_y:
                                code_target_ctrl.code = "\n".join(code_lines)
                                code_mode = False
                                stdscr.clear()
                        
                        elif run_mode:
                            if run_globals.get('__msg__'):
                                run_globals['__msg__'] = None 
                                stdscr.clear()
                            elif stop_pos[0] <= mx < stop_pos[1] and my == 0 and left_click:
                                run_mode = False
                                run_focused_ctrl = -1
                                run_pressed_ctrl = -1
                                if design_backup is not None:
                                    main_form = copy.deepcopy(design_backup)
                                    windows[0] = main_form
                                stdscr.clear()
                            elif my == 0 and left_click:
                                for start_x, end_x, m in menu_positions:
                                    if start_x <= mx < end_x:
                                        curr_m = m
                                        curr_x = start_x
                                        curr_y = 1
                                        while curr_m:
                                            if curr_m.sub:
                                                drop_items = [(s.label + " >" if s.sub else s.label) for s in curr_m.sub]
                                                drop_w = max(15, max([len(i) for i in drop_items]) + 2)
                                                idx = handle_combobox_dropdown(stdscr, curr_x, curr_y, drop_w, drop_items, C)
                                                if idx is not None:
                                                    curr_m = curr_m.sub[idx]
                                                    curr_x = curr_x + drop_w - 2
                                                    curr_y = curr_y + idx + 1
                                                else:
                                                    curr_m = None
                                            else:
                                                fn = f"{curr_m.name}_clicked"
                                                if fn in run_globals:
                                                    try: run_globals[fn]()
                                                    except Exception as e: run_globals['__msg__'] = str(e)
                                                curr_m = None
                                        break
                            else:
                                win = main_form
                                if win.hit_test(mx, my):
                                    lx = mx - win.x
                                    ly = my - win.y
                                    
                                    if lx == win.w - 1 and ly == win.h - 1 and left_click and win.resizable:
                                        resizing_win = win
                                    else:
                                        idx = win.hit_control(lx, ly)
                                        if idx >= 0:
                                            c = win.controls[idx]
                                            run_focused_ctrl = idx if c.tool_type in (10, 13) else -1
                                            
                                            if right_click:
                                                fn_rclick = f"on_right_click_{c.name_id}"
                                                if fn_rclick in run_globals:
                                                    try: run_globals[fn_rclick]()
                                                    except Exception as e: run_globals['__msg__'] = f"Runtime Error:\n{e}"
                                            else:
                                                trigger_click = False
                                                if c.tool_type == 3: 
                                                    run_pressed_ctrl = idx 
                                                    fn_down = f"button_down_{c.name_id}"
                                                    if fn_down in run_globals:
                                                        try: run_globals[fn_down]()
                                                        except Exception as e: run_globals['__msg__'] = f"Runtime Error:\n{e}"
                                                elif c.tool_type == 1: 
                                                    c.value = not c.value
                                                    trigger_click = True
                                                elif c.tool_type == 11: 
                                                    c.value = True
                                                    parent = win.get_parent_frame(c)
                                                    for other_c in win.controls:
                                                        if other_c.tool_type == 11 and other_c != c:
                                                            if win.get_parent_frame(other_c) == parent:
                                                                other_c.value = False
                                                    trigger_click = True
                                                elif c.tool_type == 2:
                                                    drop_idx = handle_combobox_dropdown(stdscr, win.x + c.x, win.y + c.y + 1, c.w, c.items, C)
                                                    if drop_idx is not None:
                                                        c.list_index = drop_idx
                                                        trigger_click = True
                                                elif c.tool_type == 10:
                                                    click_r = ly - c.y
                                                    click_idx = c.scroll_offset + click_r
                                                    if 0 <= click_idx < len(c.items):
                                                        c.list_index = click_idx
                                                        trigger_click = True
                                                    
                                                if trigger_click:
                                                    fn = f"on_click_{c.name_id}"
                                                    if fn in run_globals:
                                                        try: run_globals[fn]()
                                                        except Exception as e: run_globals['__msg__'] = f"Runtime Error:\n{e}"
                                        else:
                                            run_focused_ctrl = -1
                                            dragged_win = win
                                            drag_offset_x = lx
                                            drag_offset_y = ly
                                else:
                                    run_focused_ctrl = -1
                        
                        else:
                            clicked_handled = False
                            prop_local_y = my - prop_win.y
                            clicked_prop_row = False
                            
                            if prop_win.hit_test(mx, my):
                                if selected_ctrl_idx >= 0 and 5 <= prop_local_y <= 12:
                                    clicked_prop_row = True
                                elif selected_ctrl_idx == -1 and selected_win is not None and 5 <= prop_local_y <= 12:
                                    clicked_prop_row = True
                            
                            if not clicked_prop_row:
                                commit_edit()

                            if 1 <= mx <= 5 and my == 0:
                                choice = handle_file_menu(stdscr, C)
                                if choice == 'save':
                                    fname = prompt_input(stdscr, "Save Project As (*.json)", C)
                                    if fname:
                                        if not fname.endswith('.json'): fname += '.json'
                                        try:
                                            with open(fname, 'w', encoding='utf-8') as f:
                                                json.dump(main_form.to_dict(), f, indent=2)
                                            show_sync_msgbox(stdscr, f"Project saved to {fname}", C)
                                        except Exception as e:
                                            show_sync_msgbox(stdscr, f"Save Error:\n{e}", C)
                                elif choice == 'load':
                                    fname = prompt_input(stdscr, "Load Project (*.json)", C)
                                    if fname:
                                        if not fname.endswith('.json'): fname += '.json'
                                        try:
                                            with open(fname, 'r', encoding='utf-8') as f:
                                                data = json.load(f)
                                            main_form = Window.from_dict(data)
                                            windows[0] = main_form
                                            selected_win = main_form
                                            selected_ctrl_idx = -1
                                            show_sync_msgbox(stdscr, f"Project loaded from {fname}", C)
                                        except Exception as e:
                                            show_sync_msgbox(stdscr, f"Load Error:\n{e}", C)
                                elif choice == 'exit':
                                    return 
                                
                                stdscr.clear()
                                clicked_handled = True

                            elif 18 <= mx <= 23 and my == 0:
                                design_backup = copy.deepcopy(main_form)
                                run_mode = True
                                run_focused_ctrl = -1
                                stdscr.clear()
                                run_globals = {'__msg__': None}
                                def _msgbox(text): run_globals['__msg__'] = str(text)
                                run_globals['msgbox'] = _msgbox
                                
                                current_time_ms = time.time() * 1000
                                for w in [main_form]:
                                    if w.code:
                                        try: exec(w.code, run_globals)
                                        except Exception as e: _msgbox(f"Compile Error in {w.name_id}:\n{e}")
                                    for c in w.controls:
                                        run_globals[c.name_id] = c
                                        if c.tool_type == 14:
                                            c.last_tick = current_time_ms
                                
                                for w in [main_form]:
                                    for c in w.controls:
                                        if c.code:
                                            try: exec(c.code, run_globals)
                                            except Exception as e: _msgbox(f"Compile Error in {c.name_id}:\n{e}")
                                            
                                for m, _, _ in flatten_menus(main_form.menus):
                                    if m.code:
                                        try: exec(m.code, run_globals)
                                        except Exception as e: _msgbox(f"Compile Error in {m.name_id}:\n{e}")
                                        
                                if "on_form_load" in run_globals:
                                    try: run_globals["on_form_load"]()
                                    except Exception as e: _msgbox(f"Runtime Error in on_form_load:\n{e}")
                                    
                                clicked_handled = True

                            elif 25 <= mx <= 36 and my == 0:
                                action, item = menu_editor_loop(stdscr, main_form, C)
                                if action == 'edit_code' and item:
                                    code_mode = True
                                    code_target_ctrl = item
                                    code_lines = item.code.split("\n")
                                    code_cy = min(1, len(code_lines)-1)
                                    code_cx = 4 
                                stdscr.clear()
                                clicked_handled = True

                            elif tools.x <= mx < tools.x + tools.w and tools.y <= my < tools.y + tools.h:
                                if tools.process_click(mx, my):
                                    pass
                                else:
                                    dragged_tool = True
                                    drag_offset_x = mx - tools.x
                                    drag_offset_y = my - tools.y
                                clicked_handled = True
                                
                            if not clicked_handled:
                                hit_window = False
                                for win_search_idx in range(len(windows)-1, -1, -1): 
                                    win = windows[win_search_idx]
                                    if win.hit_test(mx, my):
                                        hit_window = True
                                        local_x = mx - win.x
                                        local_y = my - win.y
                                        
                                        windows.remove(win)
                                        if win.pinned_topmost:
                                            windows.append(win)
                                        else:
                                            insert_idx = len(windows)
                                            for idx in range(len(windows)-1, -1, -1):
                                                if windows[idx].pinned_topmost:
                                                    insert_idx = idx
                                                else:
                                                    break
                                            windows.insert(insert_idx, win)
                                        
                                        if win.name_id == "Properties": 
                                            if clicked_prop_row:
                                                if selected_ctrl_idx >= 0 and selected_win is not None:
                                                    c = selected_win.controls[selected_ctrl_idx]
                                                    if prop_local_y == 5: editing_prop, edit_buffer = 1, c.name_id
                                                    elif prop_local_y == 6: editing_prop, edit_buffer = 2, c.caption
                                                    elif prop_local_y == 7: editing_prop, edit_buffer = 3, str(c.x)
                                                    elif prop_local_y == 8: editing_prop, edit_buffer = 4, str(c.y)
                                                    elif prop_local_y == 9: editing_prop, edit_buffer = 5, str(c.w)
                                                    elif prop_local_y == 10: editing_prop, edit_buffer = 6, str(c.h)
                                                    elif prop_local_y == 11:
                                                        if c.tool_type in (1, 11): 
                                                            c.value = not c.value
                                                            clicked_prop_row = False 
                                                        elif c.tool_type == 14: 
                                                            editing_prop, edit_buffer = 7, str(c.interval)
                                                        elif c.tool_type in (2, 10): 
                                                            editing_prop, edit_buffer = 8, ",".join(c.items)
                                                        elif c.tool_type == 3:
                                                            block_idx = (local_x - 9) // 2
                                                            palette = [12, 13, 14, 15, 16, 17]
                                                            if 0 <= block_idx < len(palette):
                                                                c.bg_color = palette[block_idx]
                                                            clicked_prop_row = False
                                                        else: 
                                                            clicked_prop_row = False
                                                    elif prop_local_y == 12 and c.tool_type in (2, 10):
                                                        editing_prop, edit_buffer = 9, str(c.list_index)
                                                    else:
                                                        clicked_prop_row = False
                                                elif selected_win is not None:
                                                    w = selected_win
                                                    if prop_local_y == 5: editing_prop, edit_buffer = 1, w.name_id
                                                    elif prop_local_y == 6: editing_prop, edit_buffer = 2, w.title
                                                    elif prop_local_y == 7: editing_prop, edit_buffer = 3, str(w.x)
                                                    elif prop_local_y == 8: editing_prop, edit_buffer = 4, str(w.y)
                                                    elif prop_local_y == 9: editing_prop, edit_buffer = 5, str(w.w)
                                                    elif prop_local_y == 10: editing_prop, edit_buffer = 6, str(w.h)
                                                    elif prop_local_y == 11:
                                                        w.pinned_topmost = not w.pinned_topmost
                                                        clicked_prop_row = False
                                                    elif prop_local_y == 12:
                                                        w.resizable = not w.resizable
                                                        clicked_prop_row = False
                                                    else: clicked_prop_row = False
                                            else:
                                                dragged_win = win
                                                drag_offset_x = local_x
                                                drag_offset_y = local_y
                                        else: 
                                            if tools.active_tool <= 0:
                                                matched_control = False
                                                if selected_win is win and selected_ctrl_idx >= 0:
                                                    c = win.controls[selected_ctrl_idx]
                                                    if local_x == c.x + c.w and local_y == c.y + c.h:
                                                        resizing_ctrl = True
                                                        dragged_ctrl = selected_ctrl_idx
                                                        matched_control = True
                                                
                                                if not matched_control:
                                                    clicked_ctrl = win.hit_control(local_x, local_y)
                                                    if clicked_ctrl >= 0:
                                                        selected_win = win
                                                        selected_ctrl_idx = clicked_ctrl
                                                        dragged_ctrl = clicked_ctrl
                                                        c = win.controls[clicked_ctrl]
                                                        drag_offset_x = local_x - c.x
                                                        drag_offset_y = local_y - c.y
                                                        matched_control = True
                                                        
                                                        dragged_frame_children = []
                                                        if c.tool_type == 7:
                                                            for child_idx, child in enumerate(win.controls):
                                                                if child != c and win.get_parent_frame(child) == c:
                                                                    dragged_frame_children.append(child_idx)
                                                        
                                                        if is_double_click and c.tool_type in (1, 2, 3, 7, 10, 11, 13, 14): 
                                                            code_mode = True
                                                            code_target_ctrl = c
                                                            if not c.code:
                                                                if c.tool_type == 14:
                                                                    c.code = f"def on_tick_{c.name_id}():\n    pass\n"
                                                                elif c.tool_type == 3:
                                                                    c.code = f"def button_down_{c.name_id}():\n    pass\n\ndef on_button_up_{c.name_id}():\n    pass\n\ndef on_click_{c.name_id}():\n    pass\n\ndef on_right_click_{c.name_id}():\n    pass\n"
                                                                else:
                                                                    c.code = f"def on_click_{c.name_id}():\n    pass\n\ndef on_right_click_{c.name_id}():\n    pass\n"
                                                            code_lines = c.code.split("\n")
                                                            code_cy = min(1, len(code_lines)-1)
                                                            code_cx = 4 
                                                            stdscr.clear()
                                                            
                                                if not matched_control:
                                                    if is_double_click and win is main_form:
                                                        code_mode = True
                                                        code_target_ctrl = win
                                                        if not getattr(win, 'code', None):
                                                            win.code = f"def on_form_load():\n    pass\n"
                                                        code_lines = win.code.split("\n")
                                                        code_cy = min(1, len(code_lines)-1)
                                                        code_cx = 4 
                                                        stdscr.clear()
                                                    elif local_x == win.w - 1 and local_y == win.h - 1 and win.resizable:
                                                        resizing_win = win
                                                        selected_win = win
                                                        selected_ctrl_idx = -1
                                                        hit_window = True
                                                        break
                                                    else:
                                                        dragged_win = win
                                                        drag_offset_x = local_x
                                                        drag_offset_y = local_y
                                                        selected_win = win
                                                        selected_ctrl_idx = -1
                                            else:
                                                if 0 < local_x < win.w - 14 and 0 < local_y < win.h - 1:
                                                    win.add_control(local_x, local_y, tools.active_tool, tools.items[tools.active_tool])
                                                    selected_win = win
                                                    selected_ctrl_idx = len(win.controls) - 1
                                                    tools.active_tool = 0
                                        break

                elif mouse_released:
                    if run_mode and run_pressed_ctrl >= 0:
                        win = main_form
                        if win.hit_test(mx, my):
                            lx = mx - win.x
                            ly = my - win.y
                            if win.hit_control(lx, ly) == run_pressed_ctrl:
                                c = win.controls[run_pressed_ctrl]
                                
                                if c.tool_type == 3:
                                    fn_up = f"on_button_up_{c.name_id}"
                                    if fn_up in run_globals:
                                        try: run_globals[fn_up]()
                                        except Exception as e: run_globals['__msg__'] = f"Runtime Error:\n{e}"
                                        
                                fn = f"on_click_{c.name_id}"
                                if fn in run_globals:
                                    try: run_globals[fn]()
                                    except Exception as e: run_globals['__msg__'] = f"Runtime Error:\n{e}"

                    mouse_down = False
                    dragged_win = None
                    resizing_win = None
                    dragged_ctrl = -1
                    dragged_frame_children = []
                    dragged_tool = False
                    resizing_ctrl = False
                    run_pressed_ctrl = -1

                if mouse_down and mouse_moved and not code_mode:
                    stdscr.clear() 
                    
                    if run_mode:
                        if resizing_win is not None and resizing_win.resizable:
                            win = resizing_win
                            win.w = max(10, min(mx - win.x + 1, curses.COLS - win.x))
                            win.h = max(5, min(my - win.y + 1, curses.LINES - win.y))
                        elif dragged_win is main_form:
                            main_form.x = mx - drag_offset_x
                            main_form.y = my - drag_offset_y
                            
                    else:
                        if resizing_win is not None and resizing_win.resizable:
                            win = resizing_win
                            win.w = max(10, min(mx - win.x + 1, curses.COLS - win.x))
                            win.h = max(5, min(my - win.y + 1, curses.LINES - win.y))
                        elif resizing_ctrl and dragged_ctrl >= 0 and selected_win is not None:
                            c = selected_win.controls[dragged_ctrl]
                            new_w = (mx - selected_win.x) - c.x
                            new_h = (my - selected_win.y) - c.y
                            c.w = max(4, min(new_w, selected_win.w - c.x - 1))
                            min_h = 3 if c.tool_type in (3, 7) else 1
                            c.h = max(min_h, min(new_h, selected_win.h - c.y - 1))
                            
                        elif dragged_ctrl >= 0 and selected_win is not None:
                            c = selected_win.controls[dragged_ctrl]
                            new_x = (mx - selected_win.x) - drag_offset_x
                            new_y = (my - selected_win.y) - drag_offset_y
                            
                            new_x = max(1, min(new_x, selected_win.w - c.w - 1))
                            new_y = max(1, min(new_y, selected_win.h - c.h - 1))
                            
                            dx = new_x - c.x
                            dy = new_y - c.y
                            
                            if dx != 0 or dy != 0:
                                c.x = new_x
                                c.y = new_y
                                for child_idx in dragged_frame_children:
                                    child = selected_win.controls[child_idx]
                                    child.x += dx
                                    child.y += dy
                                
                        elif dragged_tool:
                            tools.x = max(0, min(mx - drag_offset_x, curses.COLS - tools.w))
                            tools.y = max(1, min(my - drag_offset_y, curses.LINES - tools.h))
                            
                        elif dragged_win is not None:
                            dragged_win.x = mx - drag_offset_x
                            dragged_win.y = my - drag_offset_y

                old_mx = mx
                old_my = my

            except curses.error:
                pass

        elif ch == 27 and not code_mode: 
            break

        elif ch != -1:
            if code_mode:
                if ch == curses.KEY_UP:
                    code_cy = max(0, code_cy - 1)
                    code_cx = min(code_cx, len(code_lines[code_cy]))
                elif ch == curses.KEY_DOWN:
                    code_cy = min(len(code_lines) - 1, code_cy + 1)
                    code_cx = min(code_cx, len(code_lines[code_cy]))
                elif ch == curses.KEY_LEFT:
                    if code_cx > 0: code_cx -= 1
                elif ch == curses.KEY_RIGHT:
                    if code_cx < len(code_lines[code_cy]): code_cx += 1
                elif ch in (10, 13, curses.KEY_ENTER):
                    left_part = code_lines[code_cy][:code_cx]
                    right_part = code_lines[code_cy][code_cx:]
                    code_lines[code_cy] = left_part
                    code_lines.insert(code_cy + 1, right_part)
                    code_cy += 1
                    code_cx = 0
                    stdscr.clear() 
                elif ch in (8, 127, curses.KEY_BACKSPACE):
                    if code_cx > 0:
                        line = code_lines[code_cy]
                        code_lines[code_cy] = line[:code_cx-1] + line[code_cx:]
                        code_cx -= 1
                    elif code_cy > 0:
                        code_cx = len(code_lines[code_cy-1])
                        code_lines[code_cy-1] += code_lines[code_cy]
                        code_lines.pop(code_cy)
                        code_cy -= 1
                        stdscr.clear()
                elif 32 <= ch <= 126:
                    line = code_lines[code_cy]
                    code_lines[code_cy] = line[:code_cx] + chr(ch) + line[code_cx:]
                    code_cx += 1

            elif run_mode:
                if run_focused_ctrl >= 0:
                    c = main_form.controls[run_focused_ctrl]
                    if c.tool_type == 13: 
                        if ch in (8, 127, curses.KEY_BACKSPACE):
                            c.caption = c.caption[:-1]
                        elif 32 <= ch <= 126:
                            c.caption += chr(ch)
                    elif c.tool_type == 10: 
                        if ch == curses.KEY_UP:
                            c.list_index = max(0, c.list_index - 1)
                            if c.list_index < c.scroll_offset: c.scroll_offset = c.list_index
                            fn = f"on_click_{c.name_id}"
                            if fn in run_globals:
                                try: run_globals[fn]()
                                except Exception as e: run_globals['__msg__'] = f"Runtime Error:\n{e}"
                        elif ch == curses.KEY_DOWN:
                            if c.items:
                                c.list_index = min(len(c.items) - 1, c.list_index + 1)
                                if c.list_index >= c.scroll_offset + c.h:
                                    c.scroll_offset = c.list_index - c.h + 1
                                fn = f"on_click_{c.name_id}"
                                if fn in run_globals:
                                    try: run_globals[fn]()
                                    except Exception as e: run_globals['__msg__'] = f"Runtime Error:\n{e}"

            elif not run_mode:
                if editing_prop == 0 and selected_win is not None:
                    target_cap = ""
                    if selected_ctrl_idx >= 0:
                        target_cap = selected_win.controls[selected_ctrl_idx].caption
                    else:
                        target_cap = selected_win.title

                    if ch in (8, 127, curses.KEY_BACKSPACE) or (32 <= ch <= 126):
                        editing_prop = 2
                        edit_buffer = target_cap
                
                if editing_prop > 0:
                    if ch in (10, 13, curses.KEY_ENTER):
                        commit_edit()
                    elif ch in (8, 127, curses.KEY_BACKSPACE):
                        edit_buffer = edit_buffer[:-1]
                    elif 32 <= ch <= 126:
                        if editing_prop >= 3 and not (ord('0') <= ch <= ord('9') or ch == ord('-')):
                            pass 
                        else:
                            edit_buffer += chr(ch)

        time.sleep(0.01)

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    finally:
        print('\033[?1003l', end='', flush=True)