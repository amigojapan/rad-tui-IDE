import curses
import time

# ==========================================================
# VB1-DOS Clone: Python curses Port (Mouse Fixed)
# ==========================================================

class UIControl:
    def __init__(self, x, y, w, h, tool_type, name_id, caption):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.tool_type = tool_type
        self.name_id = name_id
        self.caption = caption

class Window:
    def __init__(self, x, y, w, h, title="untitled"):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.title = title
        self.controls = []

    def add_control(self, cx, cy, ctype, ctitle):
        if len(self.controls) < 30:
            name_id = f"ctrl{len(self.controls) + 1}"
            if ctype == 3:  
                ctrl = UIControl(cx, cy, 12, 3, ctype, name_id, "Button")
            elif ctype == 13: 
                ctrl = UIControl(cx, cy, 15, 1, ctype, name_id, "Text1")
            else:
                ctrl = UIControl(cx, cy, 12, 1, ctype, name_id, ctitle.strip())
            self.controls.append(ctrl)

    def draw(self, stdscr, colors, active_ctrl=-1):
        C_BORDER = colors['border']
        C_BG = colors['bg']
        C_BTN_FACE = colors['btn_face']
        C_BTN_HL = colors['btn_hl']
        C_TEXTBOX = colors['textbox']
        C_HANDLE = colors['handle']

        # 1. Draw Window Background & Borders
        write_at(stdscr, self.x, self.y, "┌" + "─" * (self.w - 2) + "┐", C_BORDER)
        for i in range(1, self.h - 1):
            write_at(stdscr, self.x, self.y + i, "│", C_BORDER)
            write_at(stdscr, self.x + 1, self.y + i, " " * (self.w - 2), C_BG)
            write_at(stdscr, self.x + self.w - 1, self.y + i, "│", C_BORDER)
        write_at(stdscr, self.x, self.y + self.h - 1, "└" + "─" * (self.w - 2) + "┘", C_BORDER)

        # Draw Title
        title_str = f" {self.title} "
        tx = self.x + (self.w // 2) - (len(title_str) // 2)
        write_at(stdscr, tx, self.y, title_str, C_BORDER)

        # 2. Draw Child Controls
        for i, c in enumerate(self.controls):
            draw_x = self.x + c.x
            draw_y = self.y + c.y

            if c.tool_type == 3:  # COMMAND BUTTON
                actual_h = max(3, c.h)
                write_at(stdscr, draw_x, draw_y, "┌" + "─" * (c.w - 2), C_BTN_HL)
                write_at(stdscr, draw_x + c.w - 1, draw_y, "┐", C_BTN_FACE)
                
                for r in range(1, actual_h - 1):
                    write_at(stdscr, draw_x, draw_y + r, "│", C_BTN_HL)
                    if r == actual_h // 2:
                        pad = (c.w - 2 - len(c.caption)) // 2
                        text = (" " * pad + c.caption + " " * (c.w - 2))[:c.w - 2]
                        write_at(stdscr, draw_x + 1, draw_y + r, text, C_BTN_FACE)
                    else:
                        write_at(stdscr, draw_x + 1, draw_y + r, " " * (c.w - 2), C_BTN_FACE)
                    write_at(stdscr, draw_x + c.w - 1, draw_y + r, "│", C_BTN_FACE)
                
                write_at(stdscr, draw_x, draw_y + actual_h - 1, "└", C_BTN_HL)
                write_at(stdscr, draw_x + 1, draw_y + actual_h - 1, "─" * (c.w - 2) + "┘", C_BTN_FACE)

            elif c.tool_type == 13:  # TEXT BOX
                for r in range(c.h):
                    if r == 0:
                        text = (" " * max(0, c.w - len(c.caption)) + c.caption)[-c.w:]
                        write_at(stdscr, draw_x, draw_y + r, text, C_TEXTBOX)
                    else:
                        write_at(stdscr, draw_x, draw_y + r, " " * c.w, C_TEXTBOX)
            else:  # DEFAULT LABEL
                for r in range(c.h):
                    if r == 0:
                        text = (c.caption + " " * c.w)[:c.w]
                        write_at(stdscr, draw_x, draw_y + r, text, C_TEXTBOX)
                    else:
                        write_at(stdscr, draw_x, draw_y + r, " " * c.w, C_TEXTBOX)

        # 3. Draw Resize Grab Handle
        if active_ctrl >= 0 and active_ctrl < len(self.controls):
            c = self.controls[active_ctrl]
            hx = self.x + c.x + c.w
            hy = self.y + c.y + c.h
            if hx < self.x + self.w and hy < self.y + self.h:
                write_at(stdscr, hx, hy, "■", C_HANDLE)

    def hit_test(self, mx, my):
        return (self.x <= mx < self.x + self.w) and (self.y <= my < self.y + self.h)

    def hit_control(self, lx, ly):
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


def draw_properties(stdscr, prop_win, windows, selected_win_idx, selected_ctrl_idx, editing_prop, edit_buffer, colors, tools):
    C_BG = colors['bg']
    C_TB = colors['textbox']
    C_LABEL = colors['prop_label']
    
    for py in range(1, prop_win.h - 1):
        write_at(stdscr, prop_win.x + 1, prop_win.y + py, " " * (prop_win.w - 2), C_BG)

    if selected_win_idx >= 0 and selected_ctrl_idx >= 0:
        c = windows[selected_win_idx].controls[selected_ctrl_idx]
        tool_name = tools.items[c.tool_type].strip()
        
        write_at(stdscr, prop_win.x + 2, prop_win.y + 2, f"Type: {tool_name}", C_LABEL)
        write_at(stdscr, prop_win.x + 1, prop_win.y + 3, "─" * (prop_win.w - 2), C_BG)

        def draw_prop(ly, lbl, p_id, val_str):
            write_at(stdscr, prop_win.x + 2, prop_win.y + ly, lbl, C_LABEL)
            display_text = (edit_buffer + "_         ")[:10] if editing_prop == p_id else (str(val_str) + "          ")[:10]
            write_at(stdscr, prop_win.x + 8, prop_win.y + ly, display_text, C_TB)

        draw_prop(5, "Name:", 1, c.name_id)
        draw_prop(6, "Cap: ", 2, c.caption)
        draw_prop(7, "X:   ", 3, c.x)
        draw_prop(8, "Y:   ", 4, c.y)
        draw_prop(9, "W:   ", 5, c.w)
        draw_prop(10,"H:   ", 6, c.h)
    else:
        write_at(stdscr, prop_win.x + 2, prop_win.y + 2, "No selection.", C_LABEL)


def main(stdscr):
    # Setup curses environment
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    
    # CRITICAL FIX: Disable click resolution so we get raw PRESSED/RELEASED events
    curses.mouseinterval(0) 
    
    # CRITICAL FIX 2: Enable advanced terminal mouse tracking (X11 & SGR)
    print('\033[?1003h\033[?1015h\033[?1006h', end='', flush=True) 

    # Color Palette
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)   
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_WHITE)   
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)    
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)   
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)    
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_WHITE)   

    C = {
        'border': curses.color_pair(1) | curses.A_BOLD,
        'bg': curses.color_pair(2),
        'btn_face': curses.color_pair(2),
        'btn_hl': curses.color_pair(3) | curses.A_BOLD,
        'textbox': curses.color_pair(4),
        'handle': curses.color_pair(5),
        'active_tool': curses.color_pair(6) | curses.A_BOLD,
        'prop_label': curses.color_pair(7)
    }

    tools = Toolbox(1, 2)
    windows = [
        Window(21, 4, 36, 17, "Form 1"),
        Window(59, 2, 20, 15, "Properties")
    ]

    selected_win_idx = -1
    selected_ctrl_idx = -1
    editing_prop = 0 
    edit_buffer = ""

    mx, my, old_mx, old_my = 0, 0, 0, 0
    dragged_win = -1
    dragged_ctrl = -1
    dragged_tool = False
    resizing_ctrl = False
    mouse_down = False
    drag_offset_x, drag_offset_y = 0, 0

    def commit_edit():
        nonlocal editing_prop, edit_buffer, selected_win_idx, selected_ctrl_idx
        if editing_prop > 0 and selected_win_idx >= 0 and selected_ctrl_idx >= 0:
            c = windows[selected_win_idx].controls[selected_ctrl_idx]
            try:
                if editing_prop == 1: c.name_id = edit_buffer
                elif editing_prop == 2: c.caption = edit_buffer
                elif editing_prop == 3: c.x = int(edit_buffer)
                elif editing_prop == 4: c.y = int(edit_buffer)
                elif editing_prop == 5: c.w = int(edit_buffer)
                elif editing_prop == 6: c.h = int(edit_buffer)
            except ValueError:
                pass 
            
            c.w = max(4, c.w)
            if c.tool_type == 3: c.h = max(3, c.h)
            else: c.h = max(1, c.h)
            c.x = max(1, c.x)
            c.y = max(1, c.y)
            c.x = min(c.x, windows[selected_win_idx].w - c.w - 1)
            c.y = min(c.y, windows[selected_win_idx].h - c.h - 1)
        editing_prop = 0

    stdscr.clear()

    while True:
        write_at(stdscr, 0, 0, " File  Edit  View  Run  Debug  Options" + " " * 40, C['handle'])
        
        tools.draw(stdscr, C)
        for i, win in enumerate(windows):
            act_idx = selected_ctrl_idx if i == selected_win_idx else -1
            win.draw(stdscr, C, act_idx)
            if i == 1:
                draw_properties(stdscr, win, windows, selected_win_idx, selected_ctrl_idx, editing_prop, edit_buffer, C, tools)
        
        stdscr.refresh()

        ch = stdscr.getch()
        
        if ch == 27: 
            break
            
        elif ch == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                mouse_moved = (mx != old_mx or my != old_my)
                
                # Rigid boolean checks for exact hardware states
                left_click = bool(bstate & curses.BUTTON1_PRESSED)
                mouse_released = bool(bstate & curses.BUTTON1_RELEASED)

                if left_click:
                    if not mouse_down:
                        mouse_down = True
                        clicked_handled = False
                        
                        prop_win = windows[1]
                        prop_local_y = my - prop_win.y
                        clicked_prop_row = False
                        if prop_win.hit_test(mx, my) and selected_ctrl_idx >= 0 and 5 <= prop_local_y <= 10:
                            clicked_prop_row = True
                        
                        if not clicked_prop_row:
                            commit_edit()

                        if my == 0:
                            write_at(stdscr, 60, 0, "Menu Clicked!       ", C['handle'])
                            clicked_handled = True
                            
                        elif tools.x <= mx < tools.x + tools.w and tools.y <= my < tools.y + tools.h:
                            if tools.process_click(mx, my):
                                write_at(stdscr, 60, 0, f"Selected: {tools.items[max(0, tools.active_tool)].strip()}" + " " * 10, C['handle'])
                            else:
                                dragged_tool = True
                                drag_offset_x = mx - tools.x
                                drag_offset_y = my - tools.y
                            clicked_handled = True
                            
                        if not clicked_handled:
                            for i in range(1, -1, -1): 
                                win = windows[i]
                                if win.hit_test(mx, my):
                                    local_x = mx - win.x
                                    local_y = my - win.y
                                    
                                    if i == 1: 
                                        if clicked_prop_row:
                                            c = windows[0].controls[selected_ctrl_idx]
                                            if prop_local_y == 5: editing_prop, edit_buffer = 1, c.name_id
                                            elif prop_local_y == 6: editing_prop, edit_buffer = 2, c.caption
                                            elif prop_local_y == 7: editing_prop, edit_buffer = 3, str(c.x)
                                            elif prop_local_y == 8: editing_prop, edit_buffer = 4, str(c.y)
                                            elif prop_local_y == 9: editing_prop, edit_buffer = 5, str(c.w)
                                            elif prop_local_y == 10: editing_prop, edit_buffer = 6, str(c.h)
                                        else:
                                            dragged_win = i
                                            drag_offset_x = local_x
                                            drag_offset_y = local_y
                                    else: 
                                        if tools.active_tool <= 0:
                                            matched_control = False
                                            if selected_win_idx == i and selected_ctrl_idx >= 0:
                                                c = win.controls[selected_ctrl_idx]
                                                if local_x == c.x + c.w and local_y == c.y + c.h:
                                                    resizing_ctrl = True
                                                    dragged_ctrl = selected_ctrl_idx
                                                    matched_control = True
                                            
                                            if not matched_control:
                                                clicked_ctrl = win.hit_control(local_x, local_y)
                                                if clicked_ctrl >= 0:
                                                    selected_win_idx = i
                                                    selected_ctrl_idx = clicked_ctrl
                                                    dragged_ctrl = clicked_ctrl
                                                    c = win.controls[clicked_ctrl]
                                                    drag_offset_x = local_x - c.x
                                                    drag_offset_y = local_y - c.y
                                                    matched_control = True
                                            
                                            if not matched_control:
                                                dragged_win = i
                                                drag_offset_x = local_x
                                                drag_offset_y = local_y
                                                selected_ctrl_idx = -1
                                        else:
                                            if 0 < local_x < win.w - 14 and 0 < local_y < win.h - 1:
                                                win.add_control(local_x, local_y, tools.active_tool, tools.items[tools.active_tool])
                                                selected_win_idx = i
                                                selected_ctrl_idx = len(win.controls) - 1
                                                tools.active_tool = 0
                                    break

                elif mouse_released:
                    mouse_down = False
                    dragged_win = -1
                    dragged_ctrl = -1
                    dragged_tool = False
                    resizing_ctrl = False

                if mouse_down and mouse_moved:
                    stdscr.clear() 
                    if resizing_ctrl and dragged_ctrl >= 0:
                        c = windows[selected_win_idx].controls[dragged_ctrl]
                        new_w = (mx - windows[selected_win_idx].x) - c.x
                        new_h = (my - windows[selected_win_idx].y) - c.y
                        c.w = max(4, min(new_w, windows[selected_win_idx].w - c.x - 1))
                        min_h = 3 if c.tool_type == 3 else 1
                        c.h = max(min_h, min(new_h, windows[selected_win_idx].h - c.y - 1))
                        
                    elif dragged_ctrl >= 0:
                        c = windows[selected_win_idx].controls[dragged_ctrl]
                        new_x = (mx - windows[selected_win_idx].x) - drag_offset_x
                        new_y = (my - windows[selected_win_idx].y) - drag_offset_y
                        if 0 < new_x and 0 < new_y and new_x + c.w < windows[selected_win_idx].w and new_y + c.h < windows[selected_win_idx].h:
                            c.x = new_x
                            c.y = new_y
                            
                    elif dragged_tool:
                        tools.x = max(0, min(mx - drag_offset_x, curses.COLS - tools.w))
                        tools.y = max(1, min(my - drag_offset_y, curses.LINES - tools.h))
                        
                    elif dragged_win >= 0:
                        windows[dragged_win].x = mx - drag_offset_x
                        windows[dragged_win].y = my - drag_offset_y

                old_mx = mx
                old_my = my

            except curses.error:
                pass

        elif ch != -1:
            if editing_prop == 0 and selected_win_idx >= 0 and selected_ctrl_idx >= 0:
                if ch in (8, 127, curses.KEY_BACKSPACE) or (32 <= ch <= 126):
                    editing_prop = 2
                    edit_buffer = windows[selected_win_idx].controls[selected_ctrl_idx].caption
            
            if editing_prop > 0:
                if ch in (10, 13, curses.KEY_ENTER):
                    commit_edit()
                elif ch in (8, 127, curses.KEY_BACKSPACE):
                    edit_buffer = edit_buffer[:-1]
                elif 32 <= ch <= 126:
                    if editing_prop >= 3 and not (ord('0') <= ch <= ord('9') or ch == ord('-')):
                        pass 
                    else:
                        if len(edit_buffer) < 9:
                            edit_buffer += chr(ch)

        time.sleep(0.01)

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    finally:
        # Restore terminal defaults on exit
        print('\033[?1003l\033[?1015l\033[?1006l', end='', flush=True)