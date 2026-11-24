"""Reusable, Python-free Linux PTY and terminal screen support for C++ exports."""

NATIVE_TERMINAL_CPP = r'''
#include <cerrno>
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <pty.h>
#include <sys/ioctl.h>
#include <sys/wait.h>
#include <unistd.h>
#include <deque>
#include <map>

struct NativeCell {
    wchar_t ch = L' ';
    int fg = 7, bg = 0;
    bool bold = false, underline = false, reverse = false, continuation = false;
};

class NativeTerminal {
public:
    int cols, rows, x = 0, y = 0, top = 0, bottom = 0;
    bool alt = false, app_cursor = false, autowrap = true, mouse_sgr = false;
    bool mouse_1000 = false, mouse_1002 = false, mouse_1003 = false;
    bool pending_wrap = false;
    NativeCell style;
    std::vector<std::vector<NativeCell>> screen;
    std::deque<std::vector<NativeCell>> history;
    int saved_x = 0, saved_y = 0;
    int state = 0;
    std::string params, osc_buffer;
    std::vector<std::string> osc_messages;

    explicit NativeTerminal(int width = 30, int height = 20)
        : cols(width), rows(std::max(1, height)), bottom(std::max(1, height) - 1) {
        screen.assign(rows, blank());
    }

    std::vector<NativeCell> blank() const { return std::vector<NativeCell>(cols, style); }

    void resize(int height) {
        height = std::max(1, height);
        if (height < rows) {
            int count = rows - height;
            for (int i = 0; i < count; ++i) {
                if (!alt) history.push_back(screen.front());
                screen.erase(screen.begin());
            }
            y = std::max(0, y - count);
        } else while (static_cast<int>(screen.size()) < height) screen.push_back(blank());
        rows = height;
        y = std::min(y, rows - 1);
        top = 0; bottom = rows - 1;
        trim_history();
    }

    void resize(int width, int height) {
        width = std::max(1, width);
        if (width != cols) {
            cols = width;
            for (auto* grid : {&screen, &normal_screen})
                for (auto& line : *grid) line.resize(cols, style);
            for (auto* grid : {&history, &normal_history})
                for (auto& line : *grid) line.resize(cols, style);
            x = std::min(x, cols - 1);
            normal_x = std::min(normal_x, cols - 1);
        }
        resize(height);
    }

    void trim_history() {
        while (history.size() > static_cast<std::size_t>(std::max(0, 100 - rows))) history.pop_front();
    }

    void scroll_up(int count = 1) {
        for (int i = 0; i < std::min(count, rows); ++i) {
            if (!alt && top == 0) history.push_back(screen[top]);
            screen.erase(screen.begin() + top);
            screen.insert(screen.begin() + bottom, blank());
        }
        trim_history();
    }

    void scroll_down(int count = 1) {
        for (int i = 0; i < std::min(count, rows); ++i) {
            screen.erase(screen.begin() + bottom);
            screen.insert(screen.begin() + top, blank());
        }
    }

    void linefeed() {
        if (y == bottom) scroll_up();
        else y = std::min(rows - 1, y + 1);
        pending_wrap = false;
    }

    void put(wchar_t ch) {
        int width = std::max(1, wcwidth(ch));
        width = std::min(width, cols);
        if (pending_wrap || x + width > cols) {
            if (autowrap) { x = 0; linefeed(); }
            else x = std::max(0, cols - width);
        }
        screen[y][x] = style;
        screen[y][x].ch = ch;
        screen[y][x].continuation = false;
        if (width == 2 && x + 1 < cols) {
            screen[y][x + 1] = style;
            screen[y][x + 1].continuation = true;
        }
        x += width;
        if (x >= cols) { x = cols - 1; pending_wrap = true; }
    }

    void enter_alt() {
        if (alt) return;
        normal_screen = screen; normal_history = history;
        normal_x = x; normal_y = y;
        screen.assign(rows, blank()); history.clear();
        x = y = 0; top = 0; bottom = rows - 1;
        alt = true; pending_wrap = false;
    }

    void leave_alt() {
        if (!alt) return;
        screen = normal_screen; history = normal_history;
        while (static_cast<int>(screen.size()) < rows) screen.push_back(blank());
        while (static_cast<int>(screen.size()) > rows) screen.erase(screen.begin());
        x = std::min(cols - 1, normal_x); y = std::min(rows - 1, normal_y);
        alt = false; pending_wrap = false; trim_history();
    }

    void sgr(const std::vector<int>& values) {
        for (std::size_t i = 0; i < values.size(); ++i) {
            int value = values[i];
            if (value == 0) style = NativeCell{};
            else if (value == 1) style.bold = true;
            else if (value == 4) style.underline = true;
            else if (value == 7) style.reverse = true;
            else if (value == 22) style.bold = false;
            else if (value == 24) style.underline = false;
            else if (value == 27) style.reverse = false;
            else if (value >= 30 && value <= 37) style.fg = value - 30;
            else if (value >= 40 && value <= 47) style.bg = value - 40;
            else if (value >= 90 && value <= 97) style.fg = value - 90 + 8;
            else if (value >= 100 && value <= 107) style.bg = value - 100 + 8;
            else if (value == 39) style.fg = 7;
            else if (value == 49) style.bg = 0;
            else if ((value == 38 || value == 48) && i + 2 < values.size()) {
                int color = -1;
                if (values[i + 1] == 5) { color = std::clamp(values[i + 2], 0, 255); i += 2; }
                else if (values[i + 1] == 2 && i + 4 < values.size()) {
                    int r = std::clamp(values[i + 2], 0, 255), g = std::clamp(values[i + 3], 0, 255);
                    int b = std::clamp(values[i + 4], 0, 255);
                    color = 16 + 36 * ((r + 25) / 51) + 6 * ((g + 25) / 51) + ((b + 25) / 51);
                    i += 4;
                }
                if (color >= 0) (value == 38 ? style.fg : style.bg) = color;
            }
        }
    }

    void csi(const std::string& raw, char final, int master = -1) {
        bool priv = !raw.empty() && raw[0] == '?';
        std::vector<int> values;
        std::string token;
        for (char ch : raw) {
            if (ch == ';') { values.push_back(token.empty() ? 0 : std::atoi(token.c_str())); token.clear(); }
            else if (ch >= '0' && ch <= '9' && token.size() < 8) token += ch;
            else if (ch == ':') { while (!token.empty() && token.back() == ':') token.pop_back(); }
        }
        values.push_back(token.empty() ? 0 : std::atoi(token.c_str()));
        auto num = [&](std::size_t index, int fallback) {
            return index < values.size() && values[index] ? values[index] : fallback;
        };
        int n = std::min(100, num(0, 1));
        pending_wrap = false;
        if (priv && (final == 'h' || final == 'l')) {
            bool enabled = final == 'h';
            for (int value : values) {
                if (value == 47 || value == 1047 || value == 1049) enabled ? enter_alt() : leave_alt();
                else if (value == 1) app_cursor = enabled;
                else if (value == 7) autowrap = enabled;
                else if (value == 1000) mouse_1000 = enabled;
                else if (value == 1002) mouse_1002 = enabled;
                else if (value == 1003) mouse_1003 = enabled;
                else if (value == 1006) mouse_sgr = enabled;
            }
        } else if (final == 'm') sgr(values);
        else if (final == 'H' || final == 'f') { y = std::clamp(num(0, 1) - 1, 0, rows - 1); x = std::clamp(num(1, 1) - 1, 0, cols - 1); }
        else if (final == 'A') y = std::max(0, y - n);
        else if (final == 'B') y = std::min(rows - 1, y + n);
        else if (final == 'C') x = std::min(cols - 1, x + n);
        else if (final == 'D') x = std::max(0, x - n);
        else if (final == 'E') { y = std::min(rows - 1, y + n); x = 0; }
        else if (final == 'F') { y = std::max(0, y - n); x = 0; }
        else if (final == 'G') x = std::clamp(n - 1, 0, cols - 1);
        else if (final == 'd') y = std::clamp(n - 1, 0, rows - 1);
        else if (final == 'J') {
            int mode = values[0];
            if (mode == 2 || mode == 3) {
                screen.assign(rows, blank());
                if (mode == 3) history.clear();
            } else if (mode == 0) {
                for (int col = x; col < cols; ++col) screen[y][col] = style;
                for (int row = y + 1; row < rows; ++row) screen[row] = blank();
            } else if (mode == 1) {
                for (int col = 0; col <= x; ++col) screen[y][col] = style;
                for (int row = 0; row < y; ++row) screen[row] = blank();
            }
        } else if (final == 'K') {
            int start = values[0] == 2 || values[0] == 1 ? 0 : x;
            int end = values[0] == 2 ? cols : (values[0] == 1 ? x + 1 : cols);
            for (int col = start; col < end; ++col) screen[y][col] = style;
        } else if (final == 'r') {
            int new_top = std::clamp(num(0, 1) - 1, 0, rows - 1);
            int new_bottom = std::clamp(num(1, rows) - 1, 0, rows - 1);
            if (new_top < new_bottom) { top = new_top; bottom = new_bottom; }
            x = y = 0;
        } else if (final == 'S') scroll_up(n);
        else if (final == 'T') scroll_down(n);
        else if (final == 'L' && y >= top && y <= bottom) { int old = top; top = y; scroll_down(n); top = old; }
        else if (final == 'M' && y >= top && y <= bottom) { int old = top; top = y; scroll_up(n); top = old; }
        else if (final == '@') {
            auto& row = screen[y];
            row.insert(row.begin() + x, std::min(n, cols - x), style);
            row.resize(cols);
        } else if (final == 'P') {
            auto& row = screen[y];
            row.erase(row.begin() + x, row.begin() + std::min(cols, x + n));
            row.resize(cols);
        } else if (final == 'X') {
            for (int col = x; col < std::min(cols, x + n); ++col) screen[y][col] = style;
        } else if (final == 's') { saved_x = x; saved_y = y; }
        else if (final == 'u') { x = saved_x; y = saved_y; }
        else if (final == 'n' && n == 6 && master >= 0) {
            std::string answer = "\033[" + std::to_string(y + 1) + ";" + std::to_string(x + 1) + "R";
            if (::write(master, answer.data(), answer.size()) < 0) return;
        }
    }

    void feed(const std::wstring& text, int master = -1) {
        for (wchar_t ch : text) {
            if (state == 2) {
                if (ch >= L'@' && ch <= L'~') { csi(params, static_cast<char>(ch), master); state = 0; params.clear(); }
                else if (params.size() < 80 && ch <= 127) params.push_back(static_cast<char>(ch));
                continue;
            }
            if (state == 3) {
                if (ch == 7) { osc_messages.push_back(osc_buffer); osc_buffer.clear(); state = 0; }
                else if (ch == 27) state = 4;
                else if (ch <= 127 && osc_buffer.size() < 128) osc_buffer.push_back(static_cast<char>(ch));
                continue;
            }
            if (state == 4) {
                if (ch == L'\\') { osc_messages.push_back(osc_buffer); osc_buffer.clear(); state = 0; }
                else state = 3;
                continue;
            }
            if (state == 5) { graphics = ch == L'0'; state = 0; continue; }
            if (state == 1) {
                state = 0;
                if (ch == L'[') { state = 2; params.clear(); }
                else if (ch == L']') { state = 3; osc_buffer.clear(); }
                else if (ch == L'(' || ch == L')') state = 5;
                else if (ch == L'7') { saved_x = x; saved_y = y; }
                else if (ch == L'8') { x = saved_x; y = saved_y; }
                else if (ch == L'D') linefeed();
                else if (ch == L'E') { x = 0; linefeed(); }
                else if (ch == L'M') { if (y == top) scroll_down(); else y = std::max(0, y - 1); }
                continue;
            }
            if (ch == 27) state = 1;
            else if (ch == L'\r') { x = 0; pending_wrap = false; }
            else if (ch == L'\n' || ch == 11 || ch == 12) linefeed();
            else if (ch == L'\b') { x = std::max(0, x - 1); pending_wrap = false; }
            else if (ch == L'\t') x = std::min(cols - 1, ((x / 8) + 1) * 8);
            else if (ch == 14) graphics = true;
            else if (ch == 15) graphics = false;
            else if (iswprint(ch)) {
                if (graphics) {
                    const std::wstring from = L"lkmjqxtuvwn", to = L"┌┐└┘─│├┤┴┬┼";
                    auto index = from.find(ch);
                    if (index != std::wstring::npos) ch = to[index];
                }
                put(ch);
            }
        }
    }

    void draw_at(int sy, int sx, int height, int width) const {
        static std::map<std::pair<int,int>, int> dynamic_pairs;
        std::vector<std::vector<NativeCell>> display;
        if (!alt) display.insert(display.end(), history.begin(), history.end());
        display.insert(display.end(), screen.begin(), screen.end());
        int start = std::max(0, static_cast<int>(display.size()) - height);
        for (int row = 0; row < height && start + row < static_cast<int>(display.size()); ++row) {
            const auto& line = display[start + row];
            int visible_end = std::min(width, cols);
            while (visible_end > 0) {
                const auto& tail = line[visible_end - 1];
                if (tail.ch != L' ' || tail.fg != 7 || tail.bg != 0 || tail.bold ||
                    tail.underline || tail.reverse || tail.continuation) break;
                --visible_end;
            }
            for (int col = 0; col < visible_end; ++col) {
                const auto& cell = line[col];
                if (cell.continuation) continue;
                int fg = cell.reverse ? cell.bg : cell.fg;
                int bg = cell.reverse ? cell.fg : cell.bg;
                int pair = 20 + (bg % 8) * 8 + (fg % 8);
                if (fg >= 8 || bg >= 8) {
                    if (fg < COLORS && bg < COLORS) {
                        auto key = std::make_pair(fg, bg);
                        auto found = dynamic_pairs.find(key);
                        if (found == dynamic_pairs.end() && 100 + static_cast<int>(dynamic_pairs.size()) < COLOR_PAIRS) {
                            int new_pair = 100 + static_cast<int>(dynamic_pairs.size());
                            init_pair(new_pair, static_cast<short>(fg), static_cast<short>(bg));
                            dynamic_pairs[key] = new_pair;
                            pair = new_pair;
                        } else if (found != dynamic_pairs.end()) pair = found->second;
                    }
                }
                if (sy + row < 0 || sy + row >= LINES || sx + col < 0 || sx + col >= COLS) continue;
                if (pair > 0 && pair < COLOR_PAIRS) attron(COLOR_PAIR(pair));
                if (cell.bold) attron(A_BOLD);
                if (cell.underline) attron(A_UNDERLINE);
                mvaddnwstr(sy + row, sx + col, &cell.ch, 1);
                if (cell.underline) attroff(A_UNDERLINE);
                if (cell.bold) attroff(A_BOLD);
                if (pair > 0 && pair < COLOR_PAIRS) attroff(COLOR_PAIR(pair));
            }
        }
    }

private:
    bool graphics = false;
    std::vector<std::vector<NativeCell>> normal_screen;
    std::deque<std::vector<NativeCell>> normal_history;
    int normal_x = 0, normal_y = 0;
};

class NativePty {
public:
    int master = -1;
    pid_t child = -1;
    mutable bool child_exited = false;
    std::string pending_utf8;

    bool start(int cols, int rows) {
        child_exited = false;
        pending_utf8.clear();
        winsize size{};
        size.ws_col = static_cast<unsigned short>(cols);
        size.ws_row = static_cast<unsigned short>(rows);
        child = forkpty(&master, nullptr, nullptr, &size);
        if (child < 0) return false;
        if (child == 0) {
            setenv("TERM", "xterm-256color", 1);
            setenv("PS1", "$ ", 1);
            setenv("PROMPT_COMMAND", "", 1);
            setenv("COLUMNS", std::to_string(cols).c_str(), 1);
            setenv("LINES", std::to_string(rows).c_str(), 1);
            setenv("NCURSES_NO_UTF8_ACS", "1", 1);
            const char* shell = getenv("SHELL");
            if (!shell || access(shell, X_OK) != 0) shell = "/bin/sh";
            std::string path(shell);
            if (path.size() >= 4 && path.substr(path.size() - 4) == "bash")
                execl(shell, shell, "--noprofile", "--norc", "-i", static_cast<char*>(nullptr));
            else execl(shell, shell, "-i", static_cast<char*>(nullptr));
            _exit(127);
        }
        int flags = fcntl(master, F_GETFL, 0);
        if (flags >= 0) fcntl(master, F_SETFL, flags | O_NONBLOCK);
        return true;
    }

    void resize(int cols, int rows) {
        if (master < 0) return;
        winsize size{};
        size.ws_col = static_cast<unsigned short>(cols);
        size.ws_row = static_cast<unsigned short>(rows);
        ioctl(master, TIOCSWINSZ, &size);
    }

    void send(const std::string& bytes) {
        if (master < 0) return;
        std::size_t offset = 0;
        while (offset < bytes.size()) {
            ssize_t n = ::write(master, bytes.data() + offset, bytes.size() - offset);
            if (n > 0) offset += static_cast<std::size_t>(n);
            else if (errno != EINTR) break;
        }
    }

    std::wstring poll() {
        char buffer[4096];
        for (int i = 0; i < 8; ++i) {
            ssize_t n = ::read(master, buffer, sizeof(buffer));
            if (n > 0) pending_utf8.append(buffer, static_cast<std::size_t>(n));
            else if (n == 0 || errno != EINTR) break;
        }
        std::wstring result;
        std::size_t pos = 0;
        while (pos < pending_utf8.size()) {
            unsigned char first = static_cast<unsigned char>(pending_utf8[pos]);
            std::size_t width = first < 0x80 ? 1 : (first & 0xe0) == 0xc0 ? 2 :
                                (first & 0xf0) == 0xe0 ? 3 : (first & 0xf8) == 0xf0 ? 4 : 1;
            if (pos + width > pending_utf8.size()) break;
            try { result += wide(pending_utf8.substr(pos, width)); }
            catch (...) { result += L'?'; }
            pos += width;
        }
        pending_utf8.erase(0, pos);
        return result;
    }

    bool exited() const {
        if (child < 0) return true;
        if (!child_exited) child_exited = waitpid(child, nullptr, WNOHANG) == child;
        return child_exited;
    }

    void stop() {
        if (child > 0) {
            if (!child_exited) { kill(child, SIGTERM); waitpid(child, nullptr, WNOHANG); }
            child = -1;
        }
        if (master >= 0) { close(master); master = -1; }
    }

    ~NativePty() { stop(); }
};
'''
