"""Native callback adapter for the built-in phone shell project."""

import ast
import hashlib
import json

try:
    from .cpp_native_terminal import NATIVE_TERMINAL_CPP
except ImportError:
    from cpp_native_terminal import NATIVE_TERMINAL_CPP


def _fingerprint(project):
    sources = [project.get('code', '')]
    sources += [(item.get('name_id'), item.get('code', '')) for item in project.get('controls', [])]
    def menus(items):
        for item in items:
            sources.append((item.get('name'), item.get('code', '')))
            menus(item.get('sub', []))
    menus(project.get('menus', []))
    return hashlib.sha256(json.dumps(sources, ensure_ascii=False).encode()).hexdigest()


# Fingerprint covers the form and every control/menu callback.  It prevents a
# changed Python implementation from silently receiving an outdated C++ port.
PHONE_SHELL_FINGERPRINT = '8ed4774af18c2cb530575b5753ffd134de1bf716495691c2b0af09567c5ea5be'


def is_phone_shell(project):
    names = {item.get('name_id') for item in project.get('controls', [])}
    return (len(names) == 53 and {'txt_shell', 'txt_command', 'btn_keyboard_toggle',
                                  'btn_cand_0', 'btn_symbols', 'key_31'} <= names and
            _fingerprint(project) == PHONE_SHELL_FINGERPRINT)


def _cpp_string(value):
    return '"' + ''.join('\\x%02x' % byte for byte in value.encode('utf-8')) + '"'


def _kanji_initializer(project):
    tree = ast.parse(project['code'])
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and
                target.id == 'KANJI_CANDIDATES' for target in node.targets):
            entries = ast.literal_eval(node.value)
            return ',\n'.join('        {' + _cpp_string(key) + ', {' +
                              ', '.join(_cpp_string(value) for value in values) + '}}'
                              for key, values in entries.items())
    raise ValueError('Phone shell code has no KANJI_CANDIDATES table')


PHONE_CPP = r'''
#include <array>
#include <chrono>
#include <cctype>
#include <cstdio>
#include <map>
#include <stdexcept>

class NativePhoneShell {
public:
    NativeTerminal terminal{30, 20};
    NativePty pty;
    bool started = false, shell_exit_reported = false, keyboard_visible = true;
    bool ctrl_latch = false, alt_latch = false, shift_latch = false, caps_lock = false;
    bool pending_escape = false;
    int mouse_down = 0;
    int last_kana_key = -1, candidate_index = 0, slash_escape_state = 0;
    int layout_rows = 0, layout_cols = 0;
    std::string mode = "ABC", symbol_return_mode = "ABC", romaji_prefix, romaji_tail, candidate_prefix, candidate_reading;
    std::vector<std::string> candidate_options;
    std::chrono::steady_clock::time_point last_kana_time{}, last_shift_time{}, last_q_time{};
    std::chrono::steady_clock::time_point escape_time{};
    std::map<std::string, std::vector<std::string>> kanji = {
@@KANJI_MAP@@
    };
    std::map<std::string, std::string> romaji;

    Control& c(const std::string& name) {
        for (std::size_t i = 0; i < control_names.size(); ++i)
            if (control_names[i] == name) return controls[i];
        throw std::runtime_error("Phone shell control missing: " + name);
    }
    Control& key(int index) {
        char name[12]; std::snprintf(name, sizeof(name), "key_%02d", index);
        return c(name);
    }
    std::string command() { return c("txt_command").caption; }
    void command_set(const std::string& value) {
        auto& control = c("txt_command");
        control.caption = value;
        control.cursor = wide(value).size();
        control.scroll_x = std::max(0, cells(value) - 29);
    }
    static bool elapsed(std::chrono::steady_clock::time_point point, double seconds) {
        if (point.time_since_epoch().count() == 0) return false;
        return std::chrono::duration<double>(std::chrono::steady_clock::now() - point).count() <= seconds;
    }
    void init_romaji() {
        const std::array<std::pair<std::string, std::string>, 15> groups = {{{"", "あいうえお"},
            {"k", "かきくけこ"}, {"s", "さしすせそ"}, {"t", "たちつてと"},
            {"n", "なにぬねの"}, {"h", "はひふへほ"}, {"m", "まみむめも"},
            {"y", "や ゆ よ"}, {"r", "らりるれろ"}, {"w", "わ   を"},
            {"g", "がぎぐげご"}, {"z", "ざじずぜぞ"}, {"d", "だぢづでど"},
            {"b", "ばびぶべぼ"}, {"p", "ぱぴぷぺぽ"}}};
        for (const auto& group : groups) {
            auto chars = wide(group.second);
            for (int i = 0; i < 5; ++i) if (chars[i] != L' ')
                romaji[group.first + std::string("aiueo").substr(i, 1)] = narrow(std::wstring(1, chars[i]));
        }
        const std::pair<const char*, const char*> exceptions[] = {
            {"shi","し"},{"chi","ち"},{"tsu","つ"},{"fu","ふ"},{"ji","じ"},
            {"si","し"},{"ti","ち"},{"tu","つ"},{"hu","ふ"},{"zi","じ"},
            {"sha","しゃ"},{"shu","しゅ"},{"sho","しょ"},
            {"cha","ちゃ"},{"chu","ちゅ"},{"cho","ちょ"},
            {"ja","じゃ"},{"ju","じゅ"},{"jo","じょ"},
            {"kya","きゃ"},{"kyu","きゅ"},{"kyo","きょ"},
            {"nya","にゃ"},{"nyu","にゅ"},{"nyo","にょ"},
            {"hya","ひゃ"},{"hyu","ひゅ"},{"hyo","ひょ"},
            {"mya","みゃ"},{"myu","みゅ"},{"myo","みょ"},
            {"rya","りゃ"},{"ryu","りゅ"},{"ryo","りょ"},
            {"gya","ぎゃ"},{"gyu","ぎゅ"},{"gyo","ぎょ"},
            {"bya","びゃ"},{"byu","びゅ"},{"byo","びょ"},
            {"pya","ぴゃ"},{"pyu","ぴゅ"},{"pyo","ぴょ"},
            {"nn","ん"},{"-","ー"}
        };
        for (const auto& item : exceptions) romaji[item.first] = item.second;
    }
    std::string convert_romaji(const std::string& raw) {
        std::string output;
        for (std::size_t i = 0; i < raw.size();) {
            std::string rest = raw.substr(i);
            for (char& ch : rest) ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
            if (rest.size() > 1 && rest[0] == rest[1] && std::string("aeioun").find(rest[0]) == std::string::npos) {
                output += "っ"; ++i; continue;
            }
            if (rest == "n" || (rest.size() > 1 && rest[0] == 'n' &&
                std::string("aiueoy").find(rest[1]) == std::string::npos)) {
                output += "ん"; ++i; continue;
            }
            std::size_t length = 0; std::string match;
            for (const auto& item : romaji) if (item.first.size() > length &&
                rest.compare(0, item.first.size(), item.first) == 0) {
                length = item.first.size(); match = item.second;
            }
            if (length) { output += match; i += length; }
            else output += raw[i++];
        }
        return output;
    }
    std::string katakana(const std::string& reading) {
        auto chars = wide(reading);
        for (auto& ch : chars) if (ch >= L'ぁ' && ch <= L'ゖ') ch += 96;
        return narrow(chars);
    }
    void clear_candidates() {
        candidate_options.clear(); candidate_index = 0;
        candidate_prefix.clear(); candidate_reading.clear(); layout();
    }
    bool start_candidates() {
        auto chars = wide(command());
        std::size_t index = chars.size();
        while (index && ((chars[index-1] >= L'ぁ' && chars[index-1] <= L'ゟ') || chars[index-1] == L'ー')) --index;
        if (index == chars.size()) return false;
        candidate_prefix = narrow(chars.substr(0, index));
        candidate_reading = narrow(chars.substr(index));
        auto found = kanji.find(candidate_reading);
        candidate_options = found == kanji.end() ? std::vector<std::string>{} : found->second;
        for (const auto& value : {candidate_reading, katakana(candidate_reading)})
            if (std::find(candidate_options.begin(), candidate_options.end(), value) == candidate_options.end())
                candidate_options.push_back(value);
        candidate_index = 0; layout(); return true;
    }
    void cycle_candidate(int step) {
        if (candidate_options.empty()) return;
        candidate_index = (candidate_index + step + static_cast<int>(candidate_options.size())) % candidate_options.size();
        layout();
    }
    void send_shell(const std::string& value) { pty.send(value); }
    void commit_candidate(int index = -1) {
        if (candidate_options.empty()) return;
        std::string value = candidate_prefix + candidate_options[index < 0 ? candidate_index : index];
        if (terminal.alt) { send_shell(value); command_set(""); }
        else command_set(value);
        romaji_prefix = command(); romaji_tail.clear(); last_kana_key = -1;
        clear_candidates();
    }
    void cancel_candidates() {
        if (candidate_options.empty()) return;
        command_set(candidate_prefix + candidate_reading);
        romaji_prefix = command(); romaji_tail.clear(); last_kana_key = -1;
        clear_candidates();
    }
    void append_romaji(char ch) {
        romaji_tail.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
        command_set(romaji_prefix + convert_romaji(romaji_tail));
    }
    void take_modifiers(bool& ctrl, bool& alt, bool& shift) {
        ctrl = ctrl_latch; alt = alt_latch; shift = shift_latch;
        ctrl_latch = alt_latch = shift_latch = false;
        last_shift_time = {}; layout();
    }
    std::string encode_text(const std::string& value, bool ctrl = false, bool alt = false) {
        std::string result = value;
        if (ctrl && result.size() == 1) {
            unsigned char ch = static_cast<unsigned char>(result[0]);
            if (std::isalpha(ch)) result[0] = static_cast<char>(std::toupper(ch) - 64);
            else {
                const std::string symbols = "@ 2[3\\4]5^6_7?";
                const int codes[] = {0,0,0,27,27,28,28,29,29,30,30,31,31,127};
                auto index = symbols.find(result[0]);
                if (index != std::string::npos && index < 14) result[0] = static_cast<char>(codes[index]);
            }
        }
        return (alt ? "\033" : "") + result;
    }
    void flush_key(const std::string& value) {
        send_shell(command() + value); command_set("");
        romaji_prefix.clear(); romaji_tail.clear(); last_kana_key = -1;
    }
    void send_nav(int index) {
        bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
        int modifier = 1 + shift + 2 * alt + 4 * ctrl;
        std::string seq = "\033";
        if (index < 4) {
            char final = "DACB"[index];
            seq += ctrl || alt || shift ? "[1;" + std::to_string(modifier) + final :
                   std::string(terminal.app_cursor ? "O" : "[") + final;
        } else if (index < 6) {
            char final = index == 4 ? 'H' : 'F';
            seq += ctrl || alt || shift ? "[1;" + std::to_string(modifier) + final :
                   std::string("[") + final;
        } else if (index < 10) {
            int number = std::array<int,4>{5,6,3,2}[index-6];
            seq += "[" + std::to_string(number) +
                (ctrl || alt || shift ? ";" + std::to_string(modifier) : "") + "~";
        } else {
            char final = index == 10 ? 'P' : 'Q';
            seq += ctrl || alt || shift ? "[1;" + std::to_string(modifier) + final :
                   std::string("O") + final;
        }
        flush_key(seq);
    }
    void set_mode(const std::string& next) {
        if (!candidate_options.empty()) commit_candidate();
        mode = next; romaji_prefix = command(); romaji_tail.clear();
        last_kana_key = -1; last_shift_time = {}; last_q_time = {};
        slash_escape_state = 0; layout();
    }
    void layout() {
        form_x = 0; form_y = 0;
        form_w = std::max(3, COLS); form_h = std::max(3, LINES);
        int content_w = std::max(1, form_w);
        int shell_w = std::max(1, content_w - 1);
        int keyboard_w = std::min(30, content_w);
        int keyboard_left = std::max(0, (form_w - keyboard_w) / 2);
        int button_h = form_h >= 32 ? 3 : 1;
        int key_rows = mode == "かな" || mode == "NAV" || mode == "SYM" ? 4 : 3;
        int candidates = !candidate_options.empty();
        int candidate_h = button_h;
        auto& shell = c("txt_shell");
        auto& input = c("txt_command");
        shell.x = input.x = 0;
        shell.y = 0;
        shell.w = input.w = content_w;

        auto place = [&](std::vector<Control*> buttons, int y) {
            int x = keyboard_left;
            int count = static_cast<int>(buttons.size());
            for (int i = 0; i < count; ++i) {
                int width = keyboard_w / count + (i < keyboard_w % count);
                if (width) {
                    buttons[i]->x = x; buttons[i]->y = y;
                    buttons[i]->w = width; buttons[i]->h = button_h;
                } else buttons[i]->x = -50;
                x += width;
            }
        };

        int shell_h, candidate_y, mode_y = 0, toggle_y = 0;
        if (keyboard_visible) {
            mode_y = form_h - (key_rows + 3) * button_h;
            shell_h = std::max(1, mode_y - 1 - candidate_h * candidates);
            candidate_y = mode_y - candidate_h;
        } else {
            toggle_y = form_h - button_h;
            shell_h = std::max(1, toggle_y - 1 - candidate_h * candidates);
            candidate_y = toggle_y - candidate_h;
        }
        shell.h = shell_h;
        input.y = shell_h;
        if (started && (terminal.rows != shell_h || terminal.cols != shell_w)) {
            terminal.resize(shell_w, shell_h);
            pty.resize(shell_w, shell_h);
        }

        if (candidates)
            place({&c("btn_cand_0"), &c("btn_cand_1"), &c("btn_cand_2")}, candidate_y);
        for (int i = 0; i < 3; ++i) {
            auto& button = c("btn_cand_" + std::to_string(i));
            int item = (candidate_index / 3) * 3 + i;
            if (candidates && item < static_cast<int>(candidate_options.size())) {
                button.caption = candidate_options[item];
                button.bg_color = item == candidate_index ? 13 : 12;
            } else button.x = -50;
        }

        if (!keyboard_visible) {
            for (const auto& name : {"btn_abc","btn_num","btn_kana","btn_rom","btn_nav","btn_ctrl",
                "btn_shift","btn_alt","btn_space","btn_back","btn_enter","btn_tab","btn_esc","btn_symbols"})
                c(name).x = -50;
            for (int i = 0; i < 32; ++i) key(i).x = -50;
            auto& toggle = c("btn_keyboard_toggle");
            toggle.caption = "↑ Keyboard " + mode;
            place({&toggle}, toggle_y);
            layout_rows = LINES; layout_cols = COLS;
            return;
        }

        const std::array<std::string,5> modes = {"ABC","123","かな","ROM","NAV"};
        const std::array<std::string,5> mode_names = {"btn_abc","btn_num","btn_kana","btn_rom","btn_nav"};
        place({&c("btn_abc"), &c("btn_num"), &c("btn_kana"), &c("btn_rom"), &c("btn_nav")}, mode_y);
        for (int i = 0; i < 5; ++i) {
            auto& button = c(mode_names[i]);
            button.caption = modes[i];
            button.bg_color = mode == modes[i] ? 13 : 12;
        }
        int mod_y = mode_y + button_h;
        place({&c("btn_ctrl"), &c("btn_shift"), &c("btn_alt"), &c("btn_keyboard_toggle")}, mod_y);
        c("btn_keyboard_toggle").caption = "↓";
        c("btn_ctrl").bg_color = ctrl_latch ? 13 : 12;
        c("btn_alt").bg_color = alt_latch ? 13 : 12;
        c("btn_shift").bg_color = shift_latch || caps_lock ? 13 : 12;
        c("btn_shift").caption = caps_lock ? "CAPS" : "Shift";
        c("btn_symbols").bg_color = mode == "SYM" ? 13 : 12;
        int key_y = mod_y + button_h;
        for (int i = 0; i < 32; ++i) {
            auto& button = key(i);
            button.x = -50; button.y = key_y; button.w = 1; button.h = button_h;
        }
        if (mode == "ABC" || mode == "ROM") {
            const std::array<std::string,3> rows = {"qwertyuiop","asdfghjkl","zxcvbnm"};
            int index = 0;
            for (int row = 0; row < 3; ++row) {
                std::vector<Control*> buttons;
                for (char ch : rows[row]) {
                    auto& button = key(index++);
                    button.caption = std::string(1, caps_lock ^ shift_latch ?
                        static_cast<char>(std::toupper(ch)) : ch);
                    buttons.push_back(&button);
                }
                place(buttons, key_y + row * button_h);
            }
        } else {
            std::vector<std::string> labels;
            std::vector<int> row_sizes;
            if (mode == "SYM") {
                labels = {"!","@","#","$","%","^","&","*","(",")","_","+","{","}","|","~","`","-","=","[","]","\\",";","'",",",".","/",":","\"","<",">","?"};
                row_sizes = {8,8,8,8};
            } else if (mode == "123") {
                labels = {"1","2","3","4","5","6","7","8","9","0"};
                row_sizes = {3,3,4};
            } else if (mode == "NAV") {
                labels = {"←","↑","→","↓","Home","End","PgUp","PgDn","Del","Ins","F1","F2"};
                row_sizes = {3,3,3,3};
            } else {
                labels = {"あ","か","さ","た","な","は","ま","や","ら","゛","わ","小"};
                row_sizes = {3,3,3,3};
            }
            int index = 0;
            for (int row = 0; row < static_cast<int>(row_sizes.size()); ++row) {
                std::vector<Control*> buttons;
                for (int col = 0; col < row_sizes[row]; ++col) {
                    auto& button = key(index);
                    button.caption = labels[index];
                    buttons.push_back(&button);
                    ++index;
                }
                place(buttons, key_y + row * button_h);
            }
        }
        place({&c("btn_space"), &c("btn_back"), &c("btn_enter"), &c("btn_tab"),
               &c("btn_esc"), &c("btn_symbols")}, key_y + key_rows * button_h);
        layout_rows = LINES; layout_cols = COLS;
    }
    void start() {
        init_romaji(); c("txt_shell").caption.clear();
        layout(); terminal.resize(std::max(1, c("txt_shell").w - 1), c("txt_shell").h);
        started = pty.start(terminal.cols, terminal.rows);
        if (!started) terminal.feed(L"[Shell could not start]\n");
    }
    void tick() {
        winsize size{};
        if (ioctl(STDIN_FILENO, TIOCGWINSZ, &size) == 0 && size.ws_row && size.ws_col &&
            (size.ws_row != LINES || size.ws_col != COLS))
            resizeterm(size.ws_row, size.ws_col);
        if (LINES != layout_rows || COLS != layout_cols) layout();
        if (!started) return;
        if (pending_escape && !elapsed(escape_time, 0.12)) {
            pending_escape = false;
            escape();
        }
        std::wstring output = pty.poll();
        if (!output.empty()) terminal.feed(output, pty.master);
        if (pty.exited() && !shell_exit_reported) {
            terminal.feed(L"\n[Shell exited]\n"); shell_exit_reported = true;
        }
    }
    void draw_terminal() {
        const auto& shell = c("txt_shell");
        terminal.draw_at(origin_y + shell.y, origin_x + shell.x,
                         std::min(shell.h, LINES - origin_y - shell.y), terminal.cols);
    }
    void draw_cursor() {
        int x, y;
        if (terminal.alt) {
            const auto& shell = c("txt_shell");
            x = origin_x + shell.x + terminal.x;
            y = origin_y + shell.y + terminal.y;
        } else {
            const auto& input = c("txt_command");
            x = origin_x + input.x + std::min(std::max(0, input.w - 1), cells(input.caption));
            y = origin_y + input.y;
        }
        if (x >= 0 && x < COLS && y >= 0 && y < LINES) { curs_set(1); move(y, x); }
    }
    void click(const std::string& name) {
        if (name == "btn_abc") set_mode("ABC");
        else if (name == "btn_num") set_mode("123");
        else if (name == "btn_kana") set_mode("かな");
        else if (name == "btn_rom") set_mode("ROM");
        else if (name == "btn_nav") set_mode("NAV");
        else if (name == "btn_symbols") {
            if (mode == "SYM") set_mode(symbol_return_mode);
            else { symbol_return_mode = mode; set_mode("SYM"); }
        }
        else if (name == "btn_keyboard_toggle") { keyboard_visible = !keyboard_visible; layout(); }
        else if (name == "btn_ctrl") { ctrl_latch = !ctrl_latch; last_shift_time = {}; layout(); }
        else if (name == "btn_alt") { alt_latch = !alt_latch; last_shift_time = {}; layout(); }
        else if (name == "btn_shift") {
            if (elapsed(last_shift_time, 0.45)) { caps_lock = !caps_lock; shift_latch = false; last_shift_time = {}; }
            else { shift_latch = !shift_latch; last_shift_time = std::chrono::steady_clock::now(); }
            layout();
        } else if (name == "btn_space") space();
        else if (name == "btn_back") back();
        else if (name == "btn_enter") enter();
        else if (name == "btn_tab") tab();
        else if (name == "btn_esc") escape();
        else if (name.substr(0, 8) == "btn_cand") {
            int slot = name.back() - '0';
            int index = (candidate_index / 3)*3 + slot;
            if (index >= 0 && index < static_cast<int>(candidate_options.size())) commit_candidate(index);
        } else if (name.size() == 6 && name.substr(0, 4) == "key_")
            press_key(std::atoi(name.c_str() + 4));
    }
    void space() {
        if (alt_latch && !ctrl_latch) { bool a,b,d; take_modifiers(a,b,d); set_mode(mode == "ROM" ? "ABC" : "ROM"); return; }
        if (ctrl_latch || alt_latch) {
            if (!candidate_options.empty()) commit_candidate();
            bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
            flush_key(encode_text(" ", ctrl, alt)); return;
        }
        if (!candidate_options.empty()) {
            cycle_candidate(1); bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift); return;
        }
        if ((mode == "かな" || mode == "ROM") && start_candidates()) {
            bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift); return;
        }
        command_set(command() + " "); romaji_prefix = command(); romaji_tail.clear();
        last_kana_key = -1;
        bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
    }
    void back() {
        if (!candidate_options.empty()) {
            cancel_candidates(); bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift); return;
        }
        if (ctrl_latch || alt_latch || (terminal.alt && command().empty())) {
            bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
            flush_key(encode_text(ctrl ? "\x08" : "\x7f", false, alt)); return;
        }
        if (mode == "ROM" && !romaji_tail.empty()) {
            romaji_tail.pop_back(); command_set(romaji_prefix + convert_romaji(romaji_tail));
        } else {
            auto value = wide(command());
            if (!value.empty()) { value.pop_back(); command_set(narrow(value)); }
            else send_shell("\x7f");
            romaji_prefix = command(); romaji_tail.clear();
        }
        last_kana_key = -1;
        bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
    }
    void enter() {
        if (!candidate_options.empty()) {
            commit_candidate(); bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift); return;
        }
        bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
        flush_key(encode_text("\r", false, alt));
    }
    void tab() {
        if (!candidate_options.empty()) commit_candidate();
        bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
        if (ctrl) flush_key("\033[27;" + std::to_string(1 + shift + 2*alt + 4*ctrl) + ";9~");
        else if (shift) flush_key((alt ? "\033" : "") + std::string("\033[Z"));
        else flush_key(encode_text("\t", false, alt));
    }
    void escape() {
        if (!candidate_options.empty()) {
            cancel_candidates(); bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift); return;
        }
        bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
        flush_key(encode_text("\033", false, alt));
    }
    void press_key(int index) {
        if (index < 0 || index >= 32) return;
        if (!candidate_options.empty()) commit_candidate();
        std::string pressed = key(index).caption;
        if (key(index).x < 0) return;
        if (mode == "NAV") { send_nav(index); return; }
        if (mode == "かな") {
            const std::array<std::string,12> labels = {"あ","か","さ","た","な","は","ま","や","ら","゛","わ","小"};
            const std::array<std::string,12> choices = {"あいうえお","かきくけこ","さしすせそ","たちつてと",
                "なにぬねの","はひふへほ","まみむめも","やゆよ","らりるれろ","","わをん",""};
            if (index >= 12) return;
            if (ctrl_latch || alt_latch) {
                bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
                auto chars = wide(choices[index]);
                flush_key(encode_text(chars.empty() ? labels[index] : narrow(chars.substr(0,1)), ctrl, alt)); return;
            }
            auto plain = wide(command());
            if (index == 9 || index == 11) {
                if (!plain.empty()) {
                    auto from = wide(index == 9 ? "かきくけこさしすせそたちつてとはひふへほばびぶべぼ" : "あいうえおやゆよつ");
                    auto to = wide(index == 9 ? "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ" : "ぁぃぅぇぉゃゅょっ");
                    auto pos = from.find(plain.back());
                    if (pos != std::wstring::npos && pos < to.size()) plain.back() = to[pos];
                    command_set(narrow(plain));
                }
                last_kana_key = -1;
            } else {
                auto chars = wide(choices[index]);
                if (!chars.empty()) {
                    if (index == last_kana_key && elapsed(last_kana_time, 0.9) && !plain.empty()) {
                        auto pos = chars.find(plain.back());
                        if (pos != std::wstring::npos) plain.back() = chars[(pos + 1) % chars.size()];
                        else plain.push_back(chars[0]);
                    } else plain.push_back(chars[0]);
                    command_set(narrow(plain));
                    last_kana_key = index; last_kana_time = std::chrono::steady_clock::now();
                }
            }
            romaji_prefix = command(); romaji_tail.clear();
            bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift); return;
        }
        last_kana_key = -1;
        if (ctrl_latch || alt_latch) {
            bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
            flush_key(encode_text(pressed, ctrl, alt)); return;
        }
        if (mode == "ROM" && pressed.size() == 1 && std::isalpha(static_cast<unsigned char>(pressed[0])) &&
            !caps_lock && !shift_latch) append_romaji(pressed[0]);
        else { command_set(command() + pressed); romaji_prefix = command(); romaji_tail.clear(); }
        bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
    }
    bool physical(wint_t input) {
        if (pending_escape) {
            pending_escape = false;
            if (input == ' ') { set_mode(mode == "ROM" ? "ABC" : "ROM"); return true; }
            escape();
        }
        if (input == KEY_LEFT || input == KEY_UP || input == KEY_RIGHT || input == KEY_DOWN) {
            if (!candidate_options.empty()) cycle_candidate(input == KEY_LEFT || input == KEY_UP ? -1 : 1);
            else if (command().empty()) send_nav(input == KEY_LEFT ? 0 : input == KEY_UP ? 1 : input == KEY_RIGHT ? 2 : 3);
            return true;
        }
        if (input == KEY_HOME || input == KEY_END || input == KEY_PPAGE || input == KEY_NPAGE ||
            input == KEY_DC || input == KEY_IC || input == KEY_F(1) || input == KEY_F(2)) {
            if (command().empty()) {
                int index = input == KEY_HOME ? 4 : input == KEY_END ? 5 : input == KEY_PPAGE ? 6 :
                    input == KEY_NPAGE ? 7 : input == KEY_DC ? 8 : input == KEY_IC ? 9 : input == KEY_F(1) ? 10 : 11;
                send_nav(index);
            }
            return true;
        }
        if (input == 27) { pending_escape = true; escape_time = std::chrono::steady_clock::now(); return true; }
        if (input == 0) return true;
        if (input == '\n' || input == '\r' || input == KEY_ENTER) { enter(); return true; }
        if (input == KEY_BACKSPACE || input == 8 || input == 127) { back(); return true; }
        if (input == '\t') { tab(); return true; }
        if (input == 3) {
            if (!candidate_options.empty()) clear_candidates();
            bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
            flush_key("\x03"); return true;
        }
        if (input > 0 && input < 32) {
            if (!candidate_options.empty()) commit_candidate();
            flush_key(std::string(1, static_cast<char>(input)));
            return true;
        }
        if (input > 0x10ffff || !iswprint(input)) return true;
        wchar_t ch = static_cast<wchar_t>(input);
        std::string value = narrow(std::wstring(1,ch));
        if (ch != L'q' && ch != L'z') last_q_time = {};
        if (ch != L'/' && ch != L'q' && ch != L'z') slash_escape_state = 0;
        if (ch == L'/' && !ctrl_latch && !alt_latch) {
            if (slash_escape_state == 1 && !command().empty() && command().back() == '/') { slash_escape_state = 2; return true; }
            slash_escape_state = 1;
        } else if (ch == L'q' && !ctrl_latch && !alt_latch) {
            if ((slash_escape_state == 1 || slash_escape_state == 2) && !command().empty() && command().back() == '/')
                slash_escape_state = slash_escape_state == 1 ? 3 : 4;
            else slash_escape_state = 0;
        } else if (ch == L'z' && !ctrl_latch && !alt_latch) {
            if ((slash_escape_state == 3 || slash_escape_state == 4) &&
                command().size() >= 2 && command().substr(command().size()-2) == "/q") {
                std::string prefix = command().substr(0, command().size()-2);
                command_set(prefix + (slash_escape_state == 3 ? "qz" : "/qz"));
                romaji_prefix = command(); romaji_tail.clear(); last_q_time = {}; slash_escape_state = 0; return true;
            }
            slash_escape_state = 0;
        }
        if (ch == L'z' && elapsed(last_q_time, 1.5) && !ctrl_latch && !alt_latch &&
            !command().empty() && command().back() == 'q') {
            command_set(command().substr(0, command().size()-1)); romaji_prefix = command();
            romaji_tail.clear(); last_q_time = {}; set_mode(mode == "ROM" ? "ABC" : "ROM"); return true;
        }
        if (ch == L' ') { space(); return true; }
        if (!candidate_options.empty()) commit_candidate();
        if (ctrl_latch || alt_latch) {
            bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
            flush_key(encode_text(value, ctrl, alt)); return true;
        }
        if (value.size() == 1) {
            if (std::isalpha(static_cast<unsigned char>(value[0])) && (caps_lock ^ shift_latch))
                value[0] = static_cast<char>(std::toupper(static_cast<unsigned char>(value[0])));
            else if (shift_latch) {
                const std::string from = "1234567890-/.=";
                const std::string to = "!@#$%^&*()_?>+";
                auto pos = from.find(value[0]); if (pos != std::string::npos) value[0] = to[pos];
            }
            if ((mode == "かな" || mode == "ROM") && std::islower(static_cast<unsigned char>(value[0])) &&
                std::isalpha(static_cast<unsigned char>(value[0]))) append_romaji(value[0]);
            else { command_set(command() + value); romaji_prefix = command(); romaji_tail.clear(); }
        } else { command_set(command() + value); romaji_prefix = command(); romaji_tail.clear(); }
        last_kana_key = -1;
        bool ctrl, alt, shift; take_modifiers(ctrl, alt, shift);
        if (ch == L'q') last_q_time = std::chrono::steady_clock::now();
        return true;
    }
    bool mouse(const MEVENT& event) {
        int index = hit_control(event.x, event.y);
        if (index < 0) return true;
        const std::string& name = control_names[index];
        if (name == "txt_shell" && (terminal.mouse_1000 || terminal.mouse_1002 || terminal.mouse_1003)) {
            int x = event.x - origin_x - c("txt_shell").x;
            int y = event.y - origin_y - c("txt_shell").y;
            if (x >= 0 && x < terminal.cols && y >= 0 && y < c("txt_shell").h) {
                auto report = [&](int button, bool released = false) {
                    if (terminal.mouse_sgr) send_shell("\033[<" + std::to_string(button) + ";" +
                        std::to_string(x+1) + ";" + std::to_string(y+1) + (released ? "m" : "M"));
                    else send_shell("\033[M" + std::string(1, static_cast<char>(32 + (released ? 3 : button))) +
                        std::string(1, static_cast<char>(33+x)) + std::string(1, static_cast<char>(33+y)));
                };
                if (event.bstate & BUTTON4_PRESSED) report(64);
                else if (event.bstate & BUTTON5_PRESSED) report(65);
                else if (event.bstate & BUTTON1_CLICKED) { report(0); report(0, true); mouse_down = 0; }
                else if (event.bstate & BUTTON1_PRESSED) { report(0); mouse_down = 1; }
                else if (event.bstate & BUTTON1_RELEASED) { report(0, true); mouse_down = 0; }
                else if (event.bstate & BUTTON2_PRESSED) { report(1); mouse_down = 2; }
                else if (event.bstate & BUTTON2_RELEASED) { report(1, true); mouse_down = 0; }
                else if (event.bstate & BUTTON3_PRESSED) { report(2); mouse_down = 3; }
                else if (event.bstate & BUTTON3_RELEASED) { report(2, true); mouse_down = 0; }
                else if (event.bstate & REPORT_MOUSE_POSITION) {
                    if (mouse_down && (terminal.mouse_1002 || terminal.mouse_1003)) report(32 + mouse_down - 1);
                    else if (terminal.mouse_1003) report(35);
                }
            }
            return true;
        }
        if (event.bstate & (BUTTON1_CLICKED | BUTTON1_RELEASED)) click(name);
        return true;
    }
};

static NativePhoneShell phone;
static void native_start_hook() { phone.start(); }
static void native_tick_hook() { phone.tick(); }
static void native_draw_hook() { phone.draw_terminal(); }
static void native_cursor_hook() { phone.draw_cursor(); }
static bool native_key_hook(wint_t key) { return phone.physical(key); }
static bool native_mouse_hook(const MEVENT& event) { return phone.mouse(event); }
static void native_end_hook() { phone.pty.stop(); }
static void dispatch(const std::string& name) { (void)name; }
'''


def phone_cpp(project):
    return NATIVE_TERMINAL_CPP + '\n' + PHONE_CPP.replace('@@KANJI_MAP@@', _kanji_initializer(project))
