#!/usr/bin/env python3
"""
RAD-TUI Python Edition v2.2.0
Rapid Application Development - Terminal User Interface
Integrated with v2.2.0 modules: TreeView, TabControl, ProgressBar, Slider, 
Toolbar, StatusBar, Splitter, ColorPicker, Chart, Database, Network, Regex, Custom Dialogs

Copyright (c) 2024
"""

import argparse
import glob
import os
import sys
import json
import curses
import re
import sqlite3
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, List, Any, Optional, Callable

# =============================================================================
# VERSION INFO
# =============================================================================
VERSION = "2.2.0"
VERSION_DATE = "2024-01-15"

# =============================================================================
# IMPORT V2.2.0 MODULES (with fallbacks)
# =============================================================================

# Try to import from src/ directory, otherwise use embedded implementations
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from treeview import TreeView, TreeNode
    from tabcontrol import TabControl, TabPage
    from progressbar import ProgressBar
    from slider import Slider
    from toolbar import Toolbar, ToolbarButton
    from statusbar import StatusBar, StatusPanel
    from splitter import Splitter
    from colorpicker import ColorPicker, Color
    from chart import Chart, ChartSeries
    from database import Database, QueryResult
    from network import NetworkManager, HttpResponse, http_get, http_post
    from regex import Regex, Match, regex_search, regex_replace
    from custom_dialog import CustomDialog, DialogResult
    V22_MODULES_LOADED = True
except ImportError:
    V22_MODULES_LOADED = False
    print("Warning: v2.2.0 modules not found in src/, using embedded stubs")

# =============================================================================
# EMBEDDED V2.2.0 STUBS (for when modules not available)
# =============================================================================

if not V22_MODULES_LOADED:
    class TreeNode:
        def __init__(self, text="", icon="", parent=None):
            self.text = text
            self.icon = icon
            self.expanded = False
            self.parent = parent
            self.children = []
            self.tag = None
            
        def add_child(self, text, icon=""):
            node = TreeNode(text, icon, self)
            self.children.append(node)
            return node
            
        def remove_child(self, node):
            if node in self.children:
                self.children.remove(node)
                
        def has_children(self):
            return len(self.children) > 0

    class TreeView:
        def __init__(self, name_id="", x=0, y=0, width=20, height=10):
            self.name_id = name_id
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.root_nodes = []
            self.selected_node = None
            self.indent_size = 2
            self.show_icons = True
            self.show_lines = True
            self.visible = True
            self.enabled = True
            
        def add_root_node(self, text, icon=""):
            node = TreeNode(text, icon)
            self.root_nodes.append(node)
            return node
            
        def remove_node(self, node):
            if node in self.root_nodes:
                self.root_nodes.remove(node)
            for root in self.root_nodes:
                self._remove_from_children(root, node)
                
        def _remove_from_children(self, parent, target):
            if target in parent.children:
                parent.children.remove(target)
                return True
            for child in parent.children:
                if self._remove_from_children(child, target):
                    return True
            return False
            
        def expand_node(self, node):
            node.expanded = True
            
        def collapse_node(self, node):
            node.expanded = False
            
        def toggle_node(self, node):
            node.expanded = not node.expanded
            
        def get_selected(self):
            return self.selected_node
            
        def set_selected(self, node):
            self.selected_node = node
            
        def clear(self):
            self.root_nodes = []
            self.selected_node = None

    class TabPage:
        def __init__(self, caption="", name_id=""):
            self.caption = caption
            self.name_id = name_id
            self.controls = []
            self.visible = True
            
        def add_control(self, control):
            self.controls.append(control)
            return control

    class TabControl:
        HORIZONTAL = 0
        VERTICAL = 1
        
        def __init__(self, name_id="", x=0, y=0, width=30, height=10):
            self.name_id = name_id
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.tabs = []
            self.active_tab_index = 0
            self.orientation = self.HORIZONTAL
            self.show_close_button = False
            self.visible = True
            self.enabled = True
            
        def add_tab(self, caption, name_id=""):
            tab = TabPage(caption, name_id)
            self.tabs.append(tab)
            return tab
            
        def remove_tab(self, index):
            if 0 <= index < len(self.tabs):
                del self.tabs[index]
                if self.active_tab_index >= len(self.tabs):
                    self.active_tab_index = max(0, len(self.tabs) - 1)
                    
        def set_active_tab(self, index):
            if 0 <= index < len(self.tabs):
                self.active_tab_index = index
                
        def get_active_tab(self):
            if 0 <= self.active_tab_index < len(self.tabs):
                return self.tabs[self.active_tab_index]
            return None
            
        def get_tab_count(self):
            return len(self.tabs)

    class ProgressBar:
        HORIZONTAL = 0
        VERTICAL = 1
        
        def __init__(self, name_id="", x=0, y=0, width=20, height=1):
            self.name_id = name_id
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.min_value = 0
            self.max_value = 100
            self.current_value = 0
            self.orientation = self.HORIZONTAL
            self.show_percentage = True
            self.bar_char = "█"
            self.fill_char = "░"
            self.visible = True
            self.enabled = True
            
        def set_range(self, min_val, max_val):
            self.min_value = min_val
            self.max_value = max_val
            
        def set_value(self, value):
            self.current_value = max(self.min_value, min(self.max_value, value))
            
        def get_value(self):
            return self.current_value
            
        def get_percentage(self):
            if self.max_value == self.min_value:
                return 0.0
            return ((self.current_value - self.min_value) / 
                   (self.max_value - self.min_value)) * 100
            
        def increment(self, amount=1):
            self.set_value(self.current_value + amount)
            
        def is_complete(self):
            return self.current_value >= self.max_value

    class Slider:
        HORIZONTAL = 0
        VERTICAL = 1
        
        def __init__(self, name_id="", x=0, y=0, width=20, height=1):
            self.name_id = name_id
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.min_value = 0
            self.max_value = 100
            self.current_value = 0
            self.step_increment = 1
            self.orientation = self.HORIZONTAL
            self.show_ticks = False
            self.tick_frequency = 10
            self.visible = True
            self.enabled = True
            
        def set_range(self, min_val, max_val):
            self.min_value = min_val
            self.max_value = max_val
            
        def set_value(self, value):
            self.current_value = max(self.min_value, min(self.max_value, value))
            
        def get_value(self):
            return self.current_value
            
        def set_step(self, step):
            self.step_increment = step
            
        def get_percentage(self):
            if self.max_value == self.min_value:
                return 0.0
            return ((self.current_value - self.min_value) / 
                   (self.max_value - self.min_value))

    class ToolbarButton:
        BUTTON = 0
        SEPARATOR = 1
        TOGGLE = 2
        
        def __init__(self, caption="", icon="", tooltip=""):
            self.caption = caption
            self.icon = icon
            self.tooltip = tooltip
            self.enabled = True
            self.checked = False
            self.button_type = self.BUTTON

    class Toolbar:
        HORIZONTAL = 0
        VERTICAL = 1
        
        def __init__(self, name_id="", x=0, y=0, width=40, height=1):
            self.name_id = name_id
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.buttons = []
            self.orientation = self.HORIZONTAL
            self.button_size = 3
            self.visible = True
            self.enabled = True
            
        def add_button(self, caption, icon="", tooltip=""):
            btn = ToolbarButton(caption, icon, tooltip)
            self.buttons.append(btn)
            return btn
            
        def add_separator(self):
            btn = ToolbarButton()
            btn.button_type = ToolbarButton.SEPARATOR
            self.buttons.append(btn)
            return btn
            
        def remove_button(self, index):
            if 0 <= index < len(self.buttons):
                del self.buttons[index]

    class StatusPanel:
        def __init__(self, text="", width=10, alignment="left"):
            self.text = text
            self.width = width
            self.alignment = alignment
            self.auto_size = False

    class StatusBar:
        def __init__(self, name_id="", x=0, y=0, width=76, height=1):
            self.name_id = name_id
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.panels = []
            self.simple_mode = False
            self.simple_text = ""
            self.visible = True
            
        def add_panel(self, text, width=10, auto_size=0):
            panel = StatusPanel(text, width)
            panel.auto_size = bool(auto_size)
            self.panels.append(panel)
            return panel
            
        def set_panel_text(self, index, text):
            if 0 <= index < len(self.panels):
                self.panels[index].text = text
                
        def get_panel_text(self, index):
            if 0 <= index < len(self.panels):
                return self.panels[index].text
            return ""

    class Splitter:
        HORIZONTAL = 0
        VERTICAL = 1
        
        def __init__(self, name_id="", x=0, y=0, width=1, height=10):
            self.name_id = name_id
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.orientation = self.VERTICAL
            self.position = 0.5
            self.min_position = 0.1
            self.max_position = 0.9
            self.min_size = 5
            self.visible = True
            
        def set_orientation(self, orientation):
            self.orientation = orientation
            
        def set_position(self, position):
            self.position = max(self.min_position, min(self.max_position, position))
            
        def get_position(self):
            return self.position
            
        def set_range(self, min_pos, max_pos):
            self.min_position = min_pos
            self.max_position = max_pos

    class Color:
        def __init__(self, r=0, g=0, b=0):
            self.r = max(0, min(255, r))
            self.g = max(0, min(255, g))
            self.b = max(0, min(255, b))
            
        def to_hex(self):
            return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
            
        def from_hex(self, hex_str):
            hex_str = hex_str.lstrip('#')
            self.r = int(hex_str[0:2], 16)
            self.g = int(hex_str[2:4], 16)
            self.b = int(hex_str[4:6], 16)

    class ColorPicker:
        def __init__(self, name_id="", x=0, y=0, width=20, height=8):
            self.name_id = name_id
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.selected_color = Color(128, 128, 128)
            self.color_palette = [
                Color(255, 0, 0), Color(0, 255, 0), Color(0, 0, 255),
                Color(255, 255, 0), Color(255, 0, 255), Color(0, 255, 255),
                Color(255, 255, 255), Color(0, 0, 0), Color(128, 128, 128)
            ]
            self.visible = True
            self.enabled = True
            
        def set_color(self, color):
            if isinstance(color, str):
                self.selected_color.from_hex(color)
            else:
                self.selected_color = color
                
        def get_color(self):
            return self.selected_color

    class ChartSeries:
        def __init__(self, name="", color="white"):
            self.name = name
            self.data = []
            self.color = color
            
        def add_point(self, x, y):
            self.data.append((x, y))
            
        def clear(self):
            self.data = []

    class Chart:
        BAR = 0
        LINE = 1
        PIE = 2
        
        def __init__(self, name_id="", x=0, y=0, width=40, height=15):
            self.name_id = name_id
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.chart_type = self.BAR
            self.series_list = []
            self.title = ""
            self.x_label = ""
            self.y_label = ""
            self.show_legend = True
            self.show_grid = True
            self.min_x = 0
            self.max_x = 10
            self.min_y = 0
            self.max_y = 100
            self.visible = True
            self.enabled = True
            
        def set_chart_type(self, chart_type):
            self.chart_type = chart_type
            
        def add_series(self, name, color="white"):
            series = ChartSeries(name, color)
            self.series_list.append(series)
            return series
            
        def remove_series(self, series):
            if series in self.series_list:
                self.series_list.remove(series)
                
        def clear_data(self):
            for series in self.series_list:
                series.clear()
                
        def auto_scale_range(self):
            if not self.series_list:
                return
            all_y = [y for s in self.series_list for (x, y) in s.data]
            if all_y:
                self.min_y = min(all_y)
                self.max_y = max(all_y)

    class QueryResult:
        def __init__(self):
            self.rows = []
            self.columns = []
            self.row_count = 0
            self.column_count = 0
            self.error = None

    class Database:
        def __init__(self):
            self.connection = None
            self.database_path = ""
            self.is_connected = False
            
        def connect(self, database_path):
            try:
                self.connection = sqlite3.connect(database_path)
                self.database_path = database_path
                self.is_connected = True
                return True
            except Exception as e:
                print(f"Database connection error: {e}")
                return False
                
        def disconnect(self):
            if self.connection:
                self.connection.close()
                self.connection = None
            self.is_connected = False
            
        def execute_query(self, sql, parameters=None):
            result = QueryResult()
            if not self.connection:
                result.error = "Not connected"
                return result
            try:
                cursor = self.connection.cursor()
                if parameters:
                    cursor.execute(sql, parameters)
                else:
                    cursor.execute(sql)
                result.columns = [desc[0] for desc in cursor.description] if cursor.description else []
                result.rows = cursor.fetchall()
                result.row_count = len(result.rows)
                result.column_count = len(result.columns)
            except Exception as e:
                result.error = str(e)
            return result
            
        def execute_non_query(self, sql, parameters=None):
            if not self.connection:
                return -1
            try:
                cursor = self.connection.cursor()
                if parameters:
                    cursor.execute(sql, parameters)
                else:
                    cursor.execute(sql)
                self.connection.commit()
                return cursor.rowcount
            except Exception as e:
                print(f"Query error: {e}")
                return -1
                
        def insert(self, table, data):
            if not self.connection or not data:
                return -1
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            try:
                cursor = self.connection.cursor()
                cursor.execute(sql, tuple(data.values()))
                self.connection.commit()
                return cursor.lastrowid
            except Exception as e:
                print(f"Insert error: {e}")
                return -1

    class HttpResponse:
        def __init__(self):
            self.status_code = 0
            self.headers = {}
            self.body = ""
            self.error = None
            
        def is_success(self):
            return 200 <= self.status_code < 300
            
        def json(self):
            import json
            try:
                return json.loads(self.body)
            except:
                return None

    class NetworkManager:
        def __init__(self):
            self.timeout = 30
            self.follow_redirects = True
            self.default_headers = {}
            
        def get(self, url, headers=None):
            response = HttpResponse()
            try:
                req = urllib.request.Request(url, method='GET')
                req.add_header('User-Agent', 'RAD-TUI/2.2.0')
                if headers:
                    for key, value in headers.items():
                        req.add_header(key, value)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    response.status_code = resp.getcode()
                    response.headers = dict(resp.headers)
                    response.body = resp.read().decode('utf-8')
            except Exception as e:
                response.error = str(e)
            return response
            
        def post(self, url, data=None, headers=None):
            response = HttpResponse()
            try:
                if data and isinstance(data, dict):
                    data = urllib.parse.urlencode(data).encode()
                req = urllib.request.Request(url, data=data, method='POST')
                req.add_header('User-Agent', 'RAD-TUI/2.2.0')
                if headers:
                    for key, value in headers.items():
                        req.add_header(key, value)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    response.status_code = resp.getcode()
                    response.headers = dict(resp.headers)
                    response.body = resp.read().decode('utf-8')
            except Exception as e:
                response.error = str(e)
            return response

    def http_get(url, headers=None):
        nm = NetworkManager()
        return nm.get(url, headers)
        
    def http_post(url, data=None, headers=None):
        nm = NetworkManager()
        return nm.post(url, data, headers)

    class Regex:
        def __init__(self, pattern, flags=0):
            self.pattern = pattern
            self.flags = flags
            self.compiled = None
            try:
                self.compiled = re.compile(pattern, flags)
            except re.error:
                pass
                
        def search(self, text):
            if not self.compiled:
                return None
            m = self.compiled.search(text)
            if m:
                match = Match()
                match.value = m.group(0)
                match.position = m.start()
                match.groups = m.groups()
                match._match = m
                return match
            return None
            
        def match(self, text):
            if not self.compiled:
                return None
            m = self.compiled.match(text)
            if m:
                match = Match()
                match.value = m.group(0)
                match.position = m.start()
                match.groups = m.groups()
                match._match = m
                return match
            return None
            
        def find_all(self, text):
            if not self.compiled:
                return []
            return self.compiled.findall(text)
            
        def replace(self, text, replacement):
            if not self.compiled:
                return text
            return self.compiled.sub(replacement, text)

    class Match:
        def __init__(self):
            self.value = ""
            self.position = 0
            self.groups = ()
            self._match = None
            
        def is_valid(self):
            return self._match is not None
            
        def group(self, n):
            if self._match:
                try:
                    return self._match.group(n)
                except IndexError:
                    return None
            return None

    def regex_search(pattern, text, flags=0):
        r = Regex(pattern, flags)
        return r.search(text)
        
    def regex_replace(pattern, text, replacement, flags=0):
        r = Regex(pattern, flags)
        return r.replace(text, replacement)

    class DialogResult:
        NONE = 0
        OK = 1
        CANCEL = 2
        YES = 3
        NO = 4

    class CustomDialog:
        def __init__(self, name_id="", title="Dialog", width=40, height=10):
            self.name_id = name_id
            self.title = title
            self.width = width
            self.height = height
            self.controls = []
            self.modal = True
            self.result = DialogResult.NONE
            self.values = {}
            self.visible = False
            
        def add_control(self, control):
            self.controls.append(control)
            return control
            
        def show_dialog(self, modal=True):
            self.modal = modal
            self.visible = True
            return self.result
            
        def close_dialog(self, result):
            self.result = result
            self.visible = False
            
        def get_result(self):
            return self.result
            
        def set_value(self, name, value):
            self.values[name] = value
            
        def get_value(self, name):
            return self.values.get(name)

# =============================================================================
# V2.2.0 BUILT-IN FUNCTIONS REGISTRY
# =============================================================================

V22_BUILTINS = {
    # Database
    'Database': Database,
    'QueryResult': QueryResult,
    'database_connect': lambda path: (lambda db: db.connect(path) and db or None)(Database()),
    'execute_query': lambda db, sql, params=None: db.execute_query(sql, params) if hasattr(db, 'execute_query') else None,
    'execute_non_query': lambda db, sql, params=None: db.execute_non_query(sql, params) if hasattr(db, 'execute_non_query') else -1,
    
    # Network
    'NetworkManager': NetworkManager,
    'HttpResponse': HttpResponse,
    'http_get': http_get,
    'http_post': http_post,
    
    # Regex
    'Regex': Regex,
    'Match': Match,
    'regex_search': regex_search,
    'regex_replace': regex_replace,
    'regex_match': lambda p, t: Regex(p).match(t),
    'regex_find_all': lambda p, t: Regex(p).find_all(t),
    'regex_split': lambda p, t: re.split(p, t),
    
    # Dialogs
    'CustomDialog': CustomDialog,
    'DialogResult': DialogResult,
    'create_input_dialog': lambda t, p, d="": CustomDialog(),
    'create_confirm_dialog': lambda t, m: CustomDialog(),
    
    # Color
    'Color': Color,
}

# =============================================================================
# ORIGINAL RAD-TUI CODE (v2.1.0 base)
# =============================================================================

class Control:
    """Base control class"""
    def __init__(self, name_id="", x=0, y=0, width=10, height=1):
        self.name_id = name_id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.caption = ""
        self.visible = True
        self.enabled = True
        self.tag = None
        self.code = ""
        self.tab_order = 0
        self.parent = None

def _apply_control_kwargs(control, kwargs):
    """Apply optional constructor properties used by dynamic dialog code."""
    for key, value in kwargs.items():
        setattr(control, key, value)


class Label(Control):
    def __init__(self, name_id="", x=0, y=0, width=10, **kwargs):
        super().__init__(name_id, x, y, width, 1)
        self.alignment = "left"
        _apply_control_kwargs(self, kwargs)

class Button(Control):
    def __init__(self, name_id="", x=0, y=0, width=10, **kwargs):
        super().__init__(name_id, x, y, width, 1)
        self.default = False
        self.cancel = False
        _apply_control_kwargs(self, kwargs)

class TextBox(Control):
    def __init__(self, name_id="", x=0, y=0, width=20, **kwargs):
        super().__init__(name_id, x, y, width, 1)
        self.text = ""
        self.password_char = ""
        self.max_length = 0
        _apply_control_kwargs(self, kwargs)

class CheckBox(Control):
    def __init__(self, name_id="", x=0, y=0, width=20, **kwargs):
        super().__init__(name_id, x, y, width, 1)
        self.checked = False
        _apply_control_kwargs(self, kwargs)

class RadioButton(Control):
    def __init__(self, name_id="", x=0, y=0, width=20, **kwargs):
        super().__init__(name_id, x, y, width, 1)
        self.checked = False
        self.group = 0
        _apply_control_kwargs(self, kwargs)

class ListBox(Control):
    def __init__(self, name_id="", x=0, y=0, width=20, height=5, **kwargs):
        super().__init__(name_id, x, y, width, height)
        self.items = []
        self.selected_index = -1
        self.multi_select = False
        _apply_control_kwargs(self, kwargs)

class ComboBox(Control):
    def __init__(self, name_id="", x=0, y=0, width=20, **kwargs):
        super().__init__(name_id, x, y, width, 1)
        self.items = []
        self.selected_index = -1
        self.drop_down_count = 8
        _apply_control_kwargs(self, kwargs)

class Frame(Control):
    def __init__(self, name_id="", x=0, y=0, width=30, height=10):
        super().__init__(name_id, x, y, width, height)

class Timer(Control):
    def __init__(self, name_id=""):
        super().__init__(name_id, 0, 0, 0, 0)
        self.interval = 1000
        self.enabled = False

class Image(Control):
    def __init__(self, name_id="", x=0, y=0, width=10, height=5):
        super().__init__(name_id, x, y, width, height)
        self.image_path = ""
        self.stretch = False

class PictureBox(Control):
    """Image/ASCII-art display used by the legacy image examples."""
    def __init__(self, name_id="", x=0, y=0, width=10, height=5):
        super().__init__(name_id, x, y, width, height)
        self.image_list = None
        self.image = None

    def set_image(self, image):
        self.image = image
        return image


class ASCIIImage:
    """Small ASCII image object used by examples/image_viewer.json."""
    def __init__(self):
        self.pixels = []
        self.width = 0
        self.height = 0

    def load_from_file(self, path):
        try:
            with open(path, "r") as handle:
                lines = handle.read().splitlines()
        except Exception:
            return False
        self.pixels = [list(line) for line in lines]
        self.height = len(self.pixels)
        self.width = max((len(row) for row in self.pixels), default=0)
        for row in self.pixels:
            while len(row) < self.width:
                row.append(" ")
        return True


class ImageList:
    """Minimal image collection with the frame-navigation API examples use."""
    def __init__(self):
        self.images = []
        self.current_index = 0

    def add_image(self, image):
        self.images.append(image)
        return image

    def get_current(self):
        if not self.images:
            return None
        self.current_index = max(0, min(self.current_index, len(self.images) - 1))
        return self.images[self.current_index]

    def next_frame(self):
        if self.images:
            self.current_index = (self.current_index + 1) % len(self.images)
        return self.get_current()

    def prev_frame(self):
        if self.images:
            self.current_index = (self.current_index - 1) % len(self.images)
        return self.get_current()


class Grid(Control):
    def __init__(self, name_id="", x=0, y=0, width=40, height=10):
        super().__init__(name_id, x, y, width, height)
        self.rows = 5
        self.cols = 3
        self.grid_headers = []
        self.grid_data = []
        self.show_headers = True

class Edit(Control):
    def __init__(self, name_id="", x=0, y=0, width=20):
        super().__init__(name_id, x, y, width, 1)
        self.text = ""

class Memo(Control):
    def __init__(self, name_id="", x=0, y=0, width=40, height=10):
        super().__init__(name_id, x, y, width, height)
        self.lines = []
        self.scrollbars = True

# =============================================================================
# TOOL PALETTE (Updated for v2.2.0)
# =============================================================================

TOOL_PALETTE = {
    # v2.1.0 Controls (1-16)
    1: ("Label", "lbl", 10, 1, "Static text display"),
    2: ("Button", "btn", 12, 1, "Clickable button"),
    3: ("Button (Def)", "btn", 12, 1, "Default button"),
    4: ("TextBox", "txt", 20, 1, "Single-line text input"),
    5: ("CheckBox", "chk", 20, 1, "Checkable option"),
    6: ("RadioButton", "rad", 20, 1, "Mutually exclusive option"),
    7: ("ListBox", "lst", 20, 5, "List of items"),
    8: ("ComboBox", "cmb", 20, 1, "Dropdown selection"),
    9: ("Frame", "frm", 30, 10, "Container with border"),
    10: ("Timer", "tmr", 0, 0, "Non-visual timer"),
    11: ("Image", "img", 10, 5, "Image display"),
    12: ("Menu", "mnu", 0, 0, "Menu bar"),
    13: ("PopupMenu", "pop", 0, 0, "Context menu"),
    14: ("Edit", "edt", 20, 1, "Editable text"),
    15: ("Memo", "mem", 40, 10, "Multi-line text"),
    16: ("Grid", "grd", 40, 10, "Data grid"),
    
    # v2.2.0 Controls (17-25)
    17: ("TreeView", "tree", 30, 10, "Hierarchical tree display"),
    18: ("TabControl", "tab", 50, 15, "Tabbed container"),
    19: ("ProgressBar", "prg", 40, 1, "Progress indicator"),
    20: ("Slider", "sld", 30, 1, "Value slider"),
    21: ("Toolbar", "tbr", 50, 1, "Command toolbar"),
    22: ("StatusBar", "sts", 76, 1, "Status display"),
    23: ("Splitter", "spl", 1, 15, "Resizable divider"),
    24: ("ColorPicker", "clr", 20, 8, "Color selection"),
    25: ("Chart", "cht", 40, 15, "Data visualization"),
}

# =============================================================================
# CONTROL FACTORY (Updated for v2.2.0)
# =============================================================================

def create_control(tool_type, x, y, name_id=""):
    """Factory function to create controls by type"""
    
    # v2.1.0 Controls
    if tool_type == 1:
        return Label(name_id=name_id or "lbl", x=x, y=y)
    elif tool_type in [2, 3]:
        btn = Button(name_id=name_id or "btn", x=x, y=y)
        btn.default = (tool_type == 3)
        return btn
    elif tool_type == 4:
        return TextBox(name_id=name_id or "txt", x=x, y=y)
    elif tool_type == 5:
        return CheckBox(name_id=name_id or "chk", x=x, y=y)
    elif tool_type == 6:
        return RadioButton(name_id=name_id or "rad", x=x, y=y)
    elif tool_type == 7:
        return ListBox(name_id=name_id or "lst", x=x, y=y)
    elif tool_type == 8:
        return ComboBox(name_id=name_id or "cmb", x=x, y=y)
    elif tool_type == 9:
        return Frame(name_id=name_id or "frm", x=x, y=y)
    elif tool_type == 10:
        return Timer(name_id=name_id or "tmr")
    elif tool_type == 11:
        return Image(name_id=name_id or "img", x=x, y=y)
    elif tool_type in [12, 13]:
        return PictureBox(name_id=name_id or "pic", x=x, y=y)  # image/menu composite
    elif tool_type == 14:
        return Edit(name_id=name_id or "edt", x=x, y=y)
    elif tool_type == 15:
        return Memo(name_id=name_id or "mem", x=x, y=y)
    elif tool_type == 16:
        return Grid(name_id=name_id or "grd", x=x, y=y)
    
    # v2.2.0 Controls
    elif tool_type == 17:
        return TreeView(name_id=name_id or "tree", x=x, y=y)
    elif tool_type == 18:
        return TabControl(name_id=name_id or "tab", x=x, y=y)
    elif tool_type == 19:
        return ProgressBar(name_id=name_id or "prg", x=x, y=y)
    elif tool_type == 20:
        return Slider(name_id=name_id or "sld", x=x, y=y)
    elif tool_type == 21:
        return Toolbar(name_id=name_id or "tbr", x=x, y=y)
    elif tool_type == 22:
        return StatusBar(name_id=name_id or "sts", x=x, y=y)
    elif tool_type == 23:
        return Splitter(name_id=name_id or "spl", x=x, y=y)
    elif tool_type == 24:
        return ColorPicker(name_id=name_id or "clr", x=x, y=y)
    elif tool_type == 25:
        return Chart(name_id=name_id or "cht", x=x, y=y)
    
    return None

# =============================================================================
# PROJECT LOADER (with backward compatibility)
# =============================================================================

def _unescape_code(code):
    """Turn literal \\n/\\t/\\r escapes into real characters.

    Older project files (and the v2.2 format docs) store code with the
    newlines escaped twice, so json.load leaves literal backslash-n
    sequences in the string.  Decode them without touching other escapes.
    """
    out = []
    i = 0
    while i < len(code):
        ch = code[i]
        if ch == '\\' and i + 1 < len(code):
            nxt = code[i + 1]
            if nxt == 'n':
                out.append('\n')
                i += 2
                continue
            if nxt == 'r':
                out.append('\r')
                i += 2
                continue
            if nxt == 't':
                out.append('\t')
                i += 2
                continue
            if nxt in ('\\', '"', "'"):
                out.append(nxt)
                i += 2
                continue
        out.append(ch)
        i += 1
    return ''.join(out)


def _normalize_code(code):
    """Repair legacy double-escaped code fields when necessary."""
    if not isinstance(code, str) or not code:
        return code
    if '\n' in code:
        return code
    if '\\n' not in code and '\\t' not in code and '\\r' not in code:
        return code
    try:
        compile(code, '<project>', 'exec')
    except SyntaxError:
        return _unescape_code(code)
    return code


def _normalize_code_fields(obj):
    """Walk a project structure and normalize every ``code`` field."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'code' and isinstance(value, str):
                obj[key] = _normalize_code(value)
            else:
                _normalize_code_fields(value)
    elif isinstance(obj, list):
        for item in obj:
            _normalize_code_fields(item)


def load_project(filepath):
    """Load project from JSON file with version handling"""
    with open(filepath, 'r') as f:
        project = json.load(f)
    
    # Version compatibility check
    version = project.get('version', '2.1.0')
    print(f"Loading project version {version}")
    
    # Convert v2.1.0 to v2.2.0 if needed
    if version == '2.1.0':
        project['version'] = '2.2.0'
        # Ensure backward compatibility - no conversion needed for basic controls

    # Repair code fields written with escaped newlines (legacy v2.2 files)
    _normalize_code_fields(project)
    
    return project

def save_project(filepath, project):
    """Save project to JSON file"""
    project['version'] = VERSION
    with open(filepath, 'w') as f:
        json.dump(project, f, indent=2)

# =============================================================================
# RUNTIME ENVIRONMENT (with v2.2.0 functions)
# =============================================================================

class FormInfo:
    """Small object exposed to project code as ``frmMain``."""
    def __init__(self, x=0, y=0, w=70, h=20, title=""):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.width = w
        self.height = h
        self.title = title


class RuntimeDialog:
    """Adapter that routes the v2.2 dialog helper factories through the UI."""

    def __init__(self, runtime, kind, title, prompt="", default="", items=None):
        self.runtime = runtime
        self.kind = kind
        self.title = title
        self.prompt = prompt
        self.default = default
        self.items = list(items or [])
        self.result = DialogResult.NONE
        self.values = {}
        self.visible = False

    def show_dialog(self, modal=True, parent_x=0, parent_y=0,
                    parent_width=80, parent_height=24):
        ui = self.runtime.ui
        if self.kind == "input":
            if ui is not None:
                value = ui.input_box(self.prompt, self.title, self.default)
            else:
                print(f"\n[{self.title}]")
                print(self.prompt)
                value = input(f"Default: {self.default}\n> " if self.default else "> ")
            if value is None:
                self.result = DialogResult.CANCEL
            else:
                self.values["input"] = value
                self.result = DialogResult.OK
        elif self.kind == "confirm":
            if ui is not None:
                answer = ui.confirm_dialog(self.prompt, self.title)
            else:
                print(f"\n[{self.title}]")
                print(self.prompt)
                answer = input("(y/n): ").strip().lower() in ("y", "yes")
            self.result = DialogResult.YES if answer else DialogResult.NO
        elif self.kind == "list":
            if ui is not None:
                value = ui.list_dialog(self.items, self.title)
            else:
                print(f"\n[{self.title}]")
                for index, item in enumerate(self.items, 1):
                    print(f"  {index}. {item}")
                try:
                    value = self.items[int(input("Number: ")) - 1]
                except (ValueError, IndexError):
                    value = None
            if value is None:
                self.result = DialogResult.CANCEL
            else:
                self.values["selection"] = value
                self.result = DialogResult.OK
        else:
            self.result = DialogResult.OK
        return self.result

    def get_value(self, name):
        return self.values.get(name)

    def get_values(self):
        return dict(self.values)

    def set_value(self, name, value):
        self.values[name] = value

    def close_dialog(self, result=None):
        if result is not None:
            self.result = result
        self.visible = False


class RuntimeCustomDialog(CustomDialog):
    """CustomDialog variant that asks the active UI to render itself."""

    ui = None

    def show_dialog(self, modal=True, parent_x=0, parent_y=0,
                    parent_width=80, parent_height=24):
        super().show_dialog(modal, parent_x, parent_y,
                            parent_width, parent_height)
        ui = RuntimeCustomDialog.ui
        if ui is None:
            return self.result
        return ui.custom_dialog(self)


class RuntimeEnvironment:
    """Runtime environment for executing RAD-TUI applications"""
    
    def __init__(self):
        self.variables = {}
        self.controls = {}
        self.event_handlers = {}
        self.running = False
        self.ui = None
        self.last_error = None
        self.exit_requested = False
        self.clipboard = ""
        
        # Initialize built-in functions
        self.init_builtins()
        
    def init_builtins(self):
        """Initialize built-in functions"""
        
        # Standard built-ins
        self.builtins = {
            'print': print,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'open': open,
            'json': json,
            'os': os,
            'sys': sys,
            're': re,
        }
        
        # RAD-TUI specific functions
        self.builtins.update({
            'msgbox': self.builtin_msgbox,
            'input_box': self.builtin_input_box,
            'confirm_dialog': self.builtin_confirm_dialog,
            'file_dialog': self.builtin_file_dialog,
            'open_file': self.builtin_open_file,
            'read_line': self.builtin_read_line,
            'write_line': self.builtin_write_line,
            'close_file': self.builtin_close_file,
            'end_app': self.builtin_end_app,
            'inputbox': self.builtin_input_box,
            'file_exists': os.path.exists,
            'file_size': self.builtin_file_size,
            'list_files': self.builtin_list_files,
            'split': lambda text, sep=None: text.split(sep) if sep is not None else text.split(),
            'join': lambda items, sep: sep.join(str(item) for item in items),
            'clipboard_set': self.builtin_clipboard_set,
            'clipboard_get': self.builtin_clipboard_get,
            'expand_all_nodes': self.builtin_expand_all_nodes,
            'collapse_all_nodes': self.builtin_collapse_all_nodes,
            'is_valid_url': lambda url: bool(urllib.parse.urlparse(url).scheme and urllib.parse.urlparse(url).netloc),
            'exit': self.builtin_end_app,
            'true': True,
            'false': False,
            'null': None,
        })
        
        # Add v2.2.0 built-ins and control classes used by dialog code
        self.builtins.update(V22_BUILTINS)
        self.builtins.update({
            'Label': Label,
            'Button': Button,
            'TextBox': TextBox,
            'CheckBox': CheckBox,
            'RadioButton': RadioButton,
            'ListBox': ListBox,
            'ComboBox': ComboBox,
            'Frame': Frame,
            'Image': Image,
            'PictureBox': PictureBox,
            'ASCIIImage': ASCIIImage,
            'ImageList': ImageList,
            'Edit': Edit,
            'Memo': Memo,
            'Grid': Grid,
            'TreeView': TreeView,
            'TabControl': TabControl,
            'ProgressBar': ProgressBar,
            'Slider': Slider,
            'Toolbar': Toolbar,
            'StatusBar': StatusBar,
            'Splitter': Splitter,
            'ColorPicker': ColorPicker,
            'Chart': Chart,
            'CustomDialog': RuntimeCustomDialog,
        })

        # Route the dialog helper factories through the curses runner (or the
        # text fallback) instead of the skeletal CustomDialog implementation.
        self.builtins.update({
            'create_input_dialog': lambda title, prompt, default="": RuntimeDialog(
                self, "input", title, prompt, default),
            'create_confirm_dialog': lambda title, message, yes_no=False: RuntimeDialog(
                self, "confirm", title, message),
            'create_list_dialog': lambda title, items, multi_select=False: RuntimeDialog(
                self, "list", title, items=items),
            'create_progress_dialog': lambda title, message="Please wait...": RuntimeDialog(
                self, "progress", title, message),
        })
        
    def builtin_msgbox(self, text, title="Message", style=None):
        """Show a message box.  ``style`` may be yesno/yesnocancel."""
        style = (style or "").lower()
        if style in ("yesno", "yesnocancel", "okcancel"):
            if self.ui is not None:
                if style == "yesnocancel":
                    return self.ui.option_dialog(
                        text, title,
                        [("Yes", "yes"), ("No", "no"), ("Cancel", "cancel")],
                    )
                answer = self.ui.confirm_dialog(text, title)
                return "yes" if answer else "no"
            print(f"\n[{title}]")
            print(text)
            response = input("(yes/no): ").strip().lower()
            return "yes" if response in ("y", "yes") else "no"
        if self.ui is not None:
            return self.ui.msgbox(text, title)
        print(f"\n[{title}]")
        print(text)
        input("Press Enter to continue...")
        
    def builtin_input_box(self, prompt, title="Input", default=""):
        if self.ui is not None:
            return self.ui.input_box(prompt, title, default)
        print(f"\n[{title}]")
        if default:
            print(f"Default: {default}")
        result = input(f"{prompt}: ")
        return result if result else default
        
    def builtin_confirm_dialog(self, text, title="Confirm"):
        if self.ui is not None:
            return self.ui.confirm_dialog(text, title)
        print(f"\n[{title}]")
        print(text)
        response = input("(y/n): ").lower()
        return response in ['y', 'yes']
        
    def builtin_file_dialog(self, mode="open", filters=None):
        if self.ui is not None:
            return self.ui.file_dialog(mode, filters)
        return input(f"Enter file path ({mode}): ")
        
    def builtin_open_file(self, path, mode="r"):
        try:
            return open(path, mode)
        except Exception as e:
            print(f"Error opening file: {e}")
            return None
            
    def builtin_read_line(self, handle):
        if handle:
            return handle.readline()
        return ""
        
    def builtin_write_line(self, handle, text):
        if handle:
            handle.write(text + "\n")
            
    def builtin_close_file(self, handle):
        if handle:
            handle.close()

    def builtin_end_app(self):
        """Request that the current application window close."""
        self.exit_requested = True
        self.running = False
        if self.ui is not None:
            self.ui.running = False

    def builtin_file_size(self, path):
        try:
            return os.path.getsize(path)
        except OSError:
            return -1

    def builtin_list_files(self, path=".", pattern="*"):
        try:
            return sorted(
                os.path.basename(item)
                for item in glob.glob(os.path.join(path, pattern))
            )
        except OSError:
            return []

    def builtin_clipboard_set(self, text):
        self.clipboard = str(text)

    def builtin_clipboard_get(self):
        return self.clipboard

    def builtin_expand_all_nodes(self, tree):
        for root in getattr(tree, "root_nodes", []):
            self._set_node_expanded(root, True)
        update = getattr(tree, "_update_visible_nodes", None)
        if callable(update):
            update()

    def builtin_collapse_all_nodes(self, tree):
        for root in getattr(tree, "root_nodes", []):
            self._set_node_expanded(root, False)
        update = getattr(tree, "_update_visible_nodes", None)
        if callable(update):
            update()

    def _set_node_expanded(self, node, expanded):
        node.expanded = expanded
        for child in getattr(node, "children", []):
            self._set_node_expanded(child, expanded)
            
    def execute_code(self, code):
        """Execute user code with access to built-ins"""
        self.last_error = None
        try:
            # Create execution namespace
            namespace = {
                '__name__': '__main__',
                'controls': self.controls,
            }
            namespace.update(self.controls)
            namespace.update(self.builtins)
            namespace.update(self.variables)
            
            exec(code, namespace)
            
            # Update variables
            for key, value in namespace.items():
                if not key.startswith('__'):
                    self.variables[key] = value
                    
        except Exception as e:
            self.last_error = f"Runtime error: {e}"
            if self.ui is None:
                print(self.last_error)
            
    def register_control(self, control):
        """Register a control for runtime access"""
        if control.name_id:
            self.controls[control.name_id] = control
            self.variables[control.name_id] = control
            
    def get_control(self, name_id):
        """Get control by name_id"""
        return self.controls.get(name_id)

# =============================================================================
# MAIN APPLICATION
# =============================================================================

class RAD_TUI_App:
    """Main RAD-TUI Application"""
    
    def __init__(self):
        self.project = None
        self.runtime = RuntimeEnvironment()
        self.modified = False
        
    def new_project(self):
        """Create new project"""
        self.project = {
            "version": VERSION,
            "x": 5,
            "y": 5,
            "w": 70,
            "h": 20,
            "title": "Untitled",
            "menu_count": 0,
            "menu_items": [],
            "controls": [],
            "code": ""
        }
        self.modified = False
        print(f"Created new project (v{VERSION})")
        
    def open_project(self, filepath):
        """Open existing project"""
        try:
            self.project = load_project(filepath)
            self.modified = False
            print(f"Opened: {filepath}")
            return True
        except Exception as e:
            print(f"Error opening project: {e}")
            return False
            
    def save_project(self, filepath):
        """Save current project"""
        try:
            save_project(filepath, self.project)
            self.modified = False
            print(f"Saved: {filepath}")
            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
            
    def _can_run_tui(self):
        """Return True when curses can use the current terminal."""
        return (
            sys.stdin.isatty()
            and sys.stdout.isatty()
            and os.environ.get('TERM') not in (None, '', 'dumb')
        )

    def prepare_project(self):
        """Create runtime controls, execute project code and fire on_load."""
        if not self.project:
            print("No project loaded")
            return False

        self.runtime.controls = {}
        self.runtime.variables = {}
        self.runtime.last_error = None
        self.runtime.exit_requested = False
        self.runtime.running = True

        project = self.project
        form = FormInfo(
            project.get('x', 0),
            project.get('y', 0),
            project.get('w', 70),
            project.get('h', 20),
            project.get('title', ''),
        )
        self.runtime.variables['frmMain'] = form

        for ctrl_data in project.get('controls', []):
            tool_type = ctrl_data.get('tool_type', 1)
            name_id = ctrl_data.get('name_id', '')
            x = ctrl_data.get('x', 0)
            y = ctrl_data.get('y', 0)

            control = create_control(tool_type, x, y, name_id)
            if not control:
                continue

            width = ctrl_data.get('w', getattr(control, 'width', 10))
            height = ctrl_data.get('h', getattr(control, 'height', 1))
            control.tool_type = int(tool_type)
            control.width = max(1, int(width))
            control.height = max(1, int(height))
            control.w = control.width
            control.h = control.height
            control._json = ctrl_data

            for key, value in ctrl_data.items():
                if key in ('tool_type', 'w', 'h'):
                    continue
                if key == 'panels' and hasattr(control, 'add_panel'):
                    for panel_data in value or []:
                        panel = control.add_panel(
                            panel_data.get('text', ''),
                            panel_data.get('width', 10),
                            panel_data.get('auto_size', 0),
                        )
                        for pkey, pvalue in panel_data.items():
                            if pkey not in ('text', 'width', 'auto_size') and hasattr(panel, pkey):
                                setattr(panel, pkey, pvalue)
                    continue
                if key == 'tabs' and hasattr(control, 'add_tab'):
                    for tab_data in value or []:
                        tab = control.add_tab(
                            tab_data.get('caption', 'Tab'),
                            tab_data.get('name_id', ''),
                        )
                        for tkey, tvalue in tab_data.items():
                            if tkey not in ('caption', 'name_id') and hasattr(tab, tkey):
                                setattr(tab, tkey, tvalue)
                    continue
                if key in ('current_color', 'color') and hasattr(control, 'set_color'):
                    control.set_color(value)
                    continue
                try:
                    setattr(control, key, value)
                except Exception:
                    pass

            self.runtime.register_control(control)

        # Execute the project code and every control's code in one namespace,
        # so handlers can see each other and all controls.
        code_sections = []
        project_code = project.get('code', '')
        if project_code:
            code_sections.append(project_code)
        for control in self.runtime.controls.values():
            control_code = getattr(control, 'code', '')
            if control_code:
                code_sections.append(control_code)

        if code_sections:
            self.runtime.execute_code("\n\n".join(code_sections))

        # Fire the form's load handler, following the documented convention
        for handler_name in ('on_load_frmMain', 'on_load_form'):
            handler = self.runtime.variables.get(handler_name)
            if callable(handler):
                try:
                    handler()
                except Exception as e:
                    self.runtime.last_error = f"Runtime error in {handler_name}: {e}"
                break
        return True

    def run_project(self, headless=False):
        """Open the current project in a curses window (or run headlessly)."""
        if not self.project:
            print("No project loaded")
            return

        if headless or not self._can_run_tui():
            self.runtime.ui = None
            self.prepare_project()
            print(f"\n{'='*60}")
            print(f"Running: {self.project.get('title', 'Untitled')} (headless)")
            print(f"{'='*60}\n")
            if self.runtime.last_error:
                print(self.runtime.last_error)
            else:
                print(f"Controls: {len(self.runtime.controls)}")
                print("Execution complete")
            print(f"{'='*60}\n")
            return

        try:
            from tui_runner import ProjectRunner
        except Exception as e:
            print(f"Unable to load the TUI runner: {e}")
            return

        runner = ProjectRunner(self.project, self.runtime)
        self.runtime.ui = runner
        RuntimeCustomDialog.ui = runner
        try:
            curses.wrapper(lambda screen: runner.run(screen, self.prepare_project))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Unable to start the TUI: {e}")
        finally:
            self.runtime.ui = None
            RuntimeCustomDialog.ui = None
            self.runtime.exit_requested = False

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def print_banner():
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           RAD-TUI Python Edition v{VERSION}                    ║
║                                                              ║
║     Rapid Application Development - Terminal User Interface   ║
║                                                              ║
║     Now with v2.2.0 features:                               ║
║     • TreeView, TabControl, ProgressBar, Slider             ║
║     • Toolbar, StatusBar, Splitter                          ║
║     • ColorPicker, Chart                                    ║
║     • Database, Network, Regex, Custom Dialogs              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

def print_help():
    print("""
Interactive commands:
  new              Create new project
  open <file>      Open project file
  save <file>      Save project file
  run              Open the current project in a TUI window
  tools            List available controls
  exit             Exit application

Command line:
  python3 rad-tui-py-v22.py --help
  python3 rad-tui-py-v22.py --version
  python3 rad-tui-py-v22.py --list-examples
  python3 rad-tui-py-v22.py examples/file_explorer_v22.json
  python3 rad-tui-py-v22.py --run examples/file_explorer_v22.json
  python3 rad-tui-py-v22.py --run --headless examples/file_explorer_v22.json

Inside a running form:
  Mouse            Click menus, buttons, lists, grids and trees
  Tab / Shift-Tab  Move focus
  Enter / Space    Activate the focused control
  Esc              Close the form or cancel a dialog

Control Types:
  v2.1.0: 1-16 (Label, Button, TextBox, etc.)
  v2.2.0: 17-25 (TreeView, TabControl, Chart, etc.)
""")


def list_examples():
    examples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'examples')
    if not os.path.isdir(examples_dir):
        print(f"Examples directory not found: {examples_dir}")
        return
    for name in sorted(os.listdir(examples_dir)):
        if not name.endswith('.json'):
            continue
        path = os.path.join(examples_dir, name)
        try:
            with open(path, 'r') as handle:
                title = json.load(handle).get('title', 'Untitled')
        except Exception:
            title = '(invalid JSON)'
        print(f"{os.path.join('examples', name):<45} {title}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog='rad-tui-py-v22.py',
        description='RAD-TUI v2.2 project shell and curses form runner.',
    )
    parser.add_argument('project', nargs='?', help='project JSON file to open')
    parser.add_argument('-r', '--run', action='store_true',
                        help='open the project and start its form immediately')
    parser.add_argument('--headless', action='store_true',
                        help='execute the project code without starting the TUI')
    parser.add_argument('--list-examples', action='store_true',
                        help='list the example projects and exit')
    parser.add_argument('--version', action='version',
                        version=f'RAD-TUI Python Edition v{VERSION}')
    parser.add_argument('--export-web', metavar='PROJECT', help='export project to standalone web app (WASM via Pyodide)')
    parser.add_argument('--out', metavar='DIR', default='dist', help='output dir for --export-web (default: dist/<name>)')
    args = parser.parse_args(argv)

    if args.export_web:
        from src.export_web import export_project
        import pathlib
        out = args.out
        # if default dist, nest by project basename
        if out == 'dist':
            out = pathlib.Path(out) / pathlib.Path(args.export_web).stem
        export_project(args.export_web, out)
        print(f"Exported {args.export_web} -> {out}/ (open index.html or: python3 -m http.server --directory {out})")
        return 0

    if args.list_examples:
        list_examples()
        return 0

    if args.run and not args.project:
        parser.error('--run requires a project file')

    app = RAD_TUI_App()

    if args.project:
        if not app.open_project(args.project):
            return 1
        if args.run or args.headless:
            app.run_project(headless=args.headless)
            return 0
        print_banner()
    else:
        print_banner()
        app.new_project()

    while True:
        try:
            cmd = input("RAD-TUI> ").strip().split()
            if not cmd:
                continue

            action = cmd[0].lower()

            if action in ('exit', 'quit'):
                break

            elif action == 'new':
                app.new_project()

            elif action == 'open':
                if len(cmd) > 1:
                    app.open_project(cmd[1])
                else:
                    print("Usage: open <filepath>")

            elif action == 'save':
                if len(cmd) > 1:
                    app.save_project(cmd[1])
                else:
                    print("Usage: save <filepath>")

            elif action == 'run':
                app.run_project()

            elif action == 'tools':
                print("\nAvailable Controls:")
                print("-" * 60)
                print(f"{'Type':<6} {'Name':<15} {'Prefix':<8} {'Description'}")
                print("-" * 60)
                for tool_type, (name, prefix, w, h, desc) in TOOL_PALETTE.items():
                    version = "v2.2" if tool_type >= 17 else "v2.1"
                    print(f"{tool_type:<6} {name:<15} {prefix:<8} {desc} [{version}]")
                print("-" * 60)

            elif action == 'help':
                print_help()

            else:
                print(f"Unknown command: {action}")
                print("Type 'help' for available commands")

        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except Exception as e:
            print(f"Error: {e}")

    print("Goodbye!")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
