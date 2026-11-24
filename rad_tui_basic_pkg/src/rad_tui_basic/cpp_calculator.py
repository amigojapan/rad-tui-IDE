"""Native callbacks for the bundled calculator projects."""

import hashlib
import json


def _fingerprint(project):
    sources = [project.get('code', '')]
    sources += [(item.get('name_id'), item.get('code', ''))
                for item in project.get('controls', [])]

    def menus(items):
        for item in items:
            yield item.get('name'), item.get('code', '')
            yield from menus(item.get('sub', []))

    sources += list(menus(project.get('menus', [])))
    return hashlib.sha256(json.dumps(sources, ensure_ascii=False).encode()).hexdigest()


# Review this adapter if any of the bundled calculator callbacks change.
CALCULATOR_FINGERPRINT = 'f4003851149d5332e2ca9880da9f885b271d0ec6d1218f7c3dd9ec1b9c9e54e4'
CALCULATOR_CONTROLS = {
    'display', 'btn_c', 'btn_ce', 'btn_div', 'btn_mul', 'btn_7', 'btn_8',
    'btn_9', 'btn_sub', 'btn_4', 'btn_5', 'btn_6', 'btn_add', 'btn_1',
    'btn_2', 'btn_3', 'btn_eq', 'btn_0', 'btn_dot',
}


def is_calculator(project):
    controls = project.get('controls', [])
    return (len(controls) == len(CALCULATOR_CONTROLS) and
            {item.get('name_id') for item in controls} == CALCULATOR_CONTROLS and
            _fingerprint(project) == CALCULATOR_FINGERPRINT)


CALCULATOR_CPP = r'''
#include <charconv>
#include <cmath>
#include <stdexcept>
#include <system_error>

static void native_msgbox(const std::string& message);

class NativeCalculator {
public:
    std::string current_val = "0", operation;
    double stored_val = 0.0;
    bool new_input = true;

    Control& display() {
        auto item = std::find(control_names.begin(), control_names.end(), "display");
        return controls[static_cast<std::size_t>(item - control_names.begin())];
    }

    void show() { display().caption = current_val; }

    void clear_all() {
        current_val = "0"; stored_val = 0.0; operation.clear();
        new_input = true; show();
    }

    void clear_entry() { current_val = "0"; new_input = true; show(); }

    void append_digit(char digit) {
        if (new_input || current_val == "0") {
            current_val.assign(1, digit);
            new_input = false;
        } else if (current_val.size() < 18) current_val += digit;
        show();
    }

    void add_dot() {
        if (new_input) {
            current_val = "0.";
            new_input = false;
        } else if (current_val.find('.') == std::string::npos) current_val += '.';
        show();
    }

    static std::string format(double value) {
        char buffer[128];
        auto result = std::to_chars(buffer, buffer + sizeof(buffer), value);
        if (result.ec != std::errc()) throw std::runtime_error("Cannot format result");
        std::string output(buffer, result.ptr);
        if (output.find_first_of(".eE") == std::string::npos) output += ".0";
        if (output.size() >= 2 && output.substr(output.size() - 2) == ".0")
            output.resize(output.size() - 2);
        return output.substr(0, 18);
    }

    void calculate() {
        if (operation.empty()) return;
        try {
            double second = std::stod(current_val);
            double result = 0.0;
            if (operation == "+") result = stored_val + second;
            else if (operation == "-") result = stored_val - second;
            else if (operation == "*") result = stored_val * second;
            else if (operation == "/") {
                if (second == 0.0) {
                    native_msgbox("Cannot divide by zero");
                    clear_all();
                    return;
                }
                result = stored_val / second;
            }
            current_val = format(result);
            operation.clear(); new_input = true; show();
        } catch (const std::exception& error) {
            native_msgbox(std::string("Error: ") + error.what());
        }
    }

    void set_op(char next) {
        if (!new_input && !operation.empty()) calculate();
        operation.assign(1, next);
        stored_val = std::stod(current_val);
        new_input = true;
    }
};

static NativeCalculator calculator;
static void native_start_hook() {}
static void native_tick_hook() {}
static void native_draw_hook() {}
static void native_cursor_hook() {}
static bool native_key_hook(wint_t) { return false; }
static bool native_mouse_hook(const MEVENT&) { return false; }
static void native_end_hook() {}
[[maybe_unused]] static void native_msgbox(const std::string& message) {
    draw();
    const int width = std::min(COLS, std::max(18, cells(message) + 4));
    const int x = std::max(0, (COLS - width) / 2);
    const int y = std::max(1, LINES / 2 - 2);
    box(x, y, width, 4, 1, false);
    text(y + 1, x + 2, std::max(0, width - 4), message, 2);
    text(y + 2, x + 2, std::max(0, width - 4), "Press any key", 2);
    refresh();
    timeout(-1);
    wint_t key = 0;
    get_wch(&key);
    timeout(50);
}
static void dispatch(const std::string& name) {
    if (name == "on_form_load" || name == "on_click_btn_c") calculator.clear_all();
    else if (name == "on_click_btn_ce") calculator.clear_entry();
    else if (name == "on_click_btn_dot") calculator.add_dot();
    else if (name == "on_click_btn_eq") calculator.calculate();
    else if (name == "mnu_view_std_clicked") native_msgbox("Already in Standard view.");
    else if (name == "mnu_help_about_clicked")
        native_msgbox("TUI Python Calculator\nBuilt with rad-tui-IDE");
    else if (name.rfind("on_click_btn_", 0) == 0) {
        std::string button = name.substr(13);
        if (button.size() == 1 && button[0] >= '0' && button[0] <= '9')
            calculator.append_digit(button[0]);
        else if (button == "add") calculator.set_op('+');
        else if (button == "sub") calculator.set_op('-');
        else if (button == "mul") calculator.set_op('*');
        else if (button == "div") calculator.set_op('/');
    }
}
'''


def calculator_cpp(project):
    if not is_calculator(project):
        raise ValueError('Calculator project does not match the native adapter.')
    return CALCULATOR_CPP
