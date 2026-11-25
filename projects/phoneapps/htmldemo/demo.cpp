// Browser core for FutureShell. The calculator and game rules follow
// the native exports in ../calc.cpp, ../tic-tac-toe.cpp, and ../ms.cpp.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <deque>
#include <iomanip>
#include <numeric>
#include <random>
#include <sstream>
#include <string>
#include <vector>

#include "shell_catalog.h"

#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#else
#define EMSCRIPTEN_KEEPALIVE
#endif

namespace {
std::string output;
std::string shell_directory_name;
std::string shell_output_text;
std::string shell_target_name;
int shell_action_code = 0; // 0: show output; 1: Home; 2: open app; 3: clear

std::string trim(std::string value) {
    const auto first = value.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) return "";
    const auto last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

std::string shell_parent() {
    const auto slash = shell_directory_name.rfind('/');
    return slash == std::string::npos ? "" : shell_directory_name.substr(0, slash);
}

void run_shell_command(const std::string& command, const std::string& date) {
    shell_output_text.clear();
    shell_target_name.clear();
    shell_action_code = 0;
    if (command.empty()) return;
    if (command == "./DT/DT.bin" || command == "DT" || command == "home") {
        shell_action_code = 1;
        return;
    }
    const auto space = command.find_first_of(" \t");
    const std::string verb = command.substr(0, space);
    const std::string arg = space == std::string::npos ? "" : trim(command.substr(space + 1));
    if (verb == "bash" && arg == "--version")
        shell_output_text = "Sample bash clone for futureshell web demo";
    else if (verb == "help")
        shell_output_text = "help ls pwd cd <folder> open <app> clear echo <text> date";
    else if (verb == "pwd")
        shell_output_text = "/phoneapps/DT/DTF" + (shell_directory_name.empty() ? "" : "/" + shell_directory_name);
    else if (verb == "ls") {
        for (const auto& entry : shell_entries) {
            if (shell_directory_name != entry.parent) continue;
            if (!shell_output_text.empty()) shell_output_text += "  ";
            shell_output_text += std::string(entry.name) + (entry.folder ? "/" : ".bin");
        }
    } else if (verb == "cd") {
        if (arg == "..") shell_directory_name = shell_parent();
        else if (arg == "/") shell_directory_name.clear();
        else {
            bool found = false;
            for (const auto& entry : shell_entries) {
                if (entry.folder && shell_directory_name == entry.parent && arg == entry.name) {
                    shell_directory_name = entry.path;
                    found = true;
                    break;
                }
            }
            if (!found) { shell_output_text = "No such folder: " + arg; return; }
        }
        shell_output_text = "DTF" + (shell_directory_name.empty() ? "" : "/" + shell_directory_name);
    } else if (verb == "echo") shell_output_text = arg;
    else if (verb == "date") shell_output_text = date;
    else if (verb == "clear") shell_action_code = 3;
    else {
        const std::string requested = verb == "open" ? arg : verb;
        for (const auto& entry : shell_entries) {
            if (entry.folder) continue;
            if (requested == entry.name || requested == std::string(entry.name) + ".bin") {
                shell_action_code = 2;
                shell_target_name = entry.path;
                return;
            }
        }
        shell_output_text = "Command not found: " + command;
    }
}

struct Calculator {
    std::string value = "0";
    char operation = 0;
    double stored = 0;
    bool fresh = true;

    void reset() { value = "0"; operation = 0; stored = 0; fresh = true; }
    void clear_entry() { value = "0"; fresh = true; }
    void digit(char ch) {
        if (fresh || value == "0" || value == "Error") { value.assign(1, ch); fresh = false; }
        else if (value.size() < 18) value += ch;
    }
    void dot() {
        if (fresh) { value = "0."; fresh = false; }
        else if (value.find('.') == std::string::npos) value += '.';
    }
    void equals() {
        if (!operation) return;
        double second = 0;
        try { second = std::stod(value); }
        catch (...) { value = "Error"; operation = 0; fresh = true; return; }
        double answer = 0;
        switch (operation) {
            case '+': answer = stored + second; break;
            case '-': answer = stored - second; break;
            case '*': answer = stored * second; break;
            case '/':
                if (second == 0) { value = "Cannot divide by zero"; operation = 0; fresh = true; return; }
                answer = stored / second; break;
        }
        std::ostringstream stream;
        stream << std::setprecision(12) << answer;
        value = stream.str().substr(0, 18);
        operation = 0;
        fresh = true;
    }
    void press(const std::string& key) {
        if (key == "C") reset();
        else if (key == "CE") clear_entry();
        else if (key == ".") dot();
        else if (key == "=") equals();
        else if (key.size() == 1 && key[0] >= '0' && key[0] <= '9') digit(key[0]);
        else if (key.size() == 1 && std::string("+-*/").find(key[0]) != std::string::npos) {
            if (!fresh && operation) equals();
            try { stored = std::stod(value); }
            catch (...) { reset(); return; }
            operation = key[0];
            fresh = true;
        }
    }
} calculator;

struct TicTacToe {
    std::array<char, 9> board{};
    std::string status;
    bool over = false;
    std::mt19937 random{std::random_device{}()};

    void reset() { board.fill(' '); status = "Your turn (X)"; over = false; }
    static bool wins(const std::array<char, 9>& cells, char player) {
        constexpr int lines[8][3] = {
            {0,1,2}, {3,4,5}, {6,7,8}, {0,3,6},
            {1,4,7}, {2,5,8}, {0,4,8}, {2,4,6}
        };
        for (const auto& line : lines)
            if (cells[line[0]] == player && cells[line[1]] == player &&
                cells[line[2]] == player) return true;
        return false;
    }
    bool full() const { return std::find(board.begin(), board.end(), ' ') == board.end(); }
    void move(int index) {
        if (index < 0 || index >= 9 || over || board[index] != ' ') return;
        board[index] = 'X';
        if (wins(board, 'X')) { status = "You Win!"; over = true; return; }
        if (full()) { status = "Draw!"; over = true; return; }
        std::vector<int> empty;
        for (int i = 0; i < 9; ++i) if (board[i] == ' ') empty.push_back(i);
        int choice = -1;
        for (char player : {'O', 'X'}) {
            for (int i : empty) {
                auto trial = board;
                trial[i] = player;
                if (wins(trial, player)) { choice = i; break; }
            }
            if (choice >= 0) break;
        }
        if (choice < 0) choice = empty[std::uniform_int_distribution<int>(0, static_cast<int>(empty.size()) - 1)(random)];
        board[choice] = 'O';
        if (wins(board, 'O')) { status = "AI Wins!"; over = true; }
        else if (full()) { status = "Draw!"; over = true; }
        else status = "Your turn (X)";
    }
} tic_tac_toe;

struct Minesweeper {
    std::array<bool, 100> bombs{};
    std::array<char, 100> shown{};
    std::string status = "playing";
    int seconds = 0;
    std::mt19937 random{std::random_device{}()};

    void reset() {
        bombs.fill(false);
        shown.fill('.');
        std::array<int, 100> positions{};
        std::iota(positions.begin(), positions.end(), 0);
        std::shuffle(positions.begin(), positions.end(), random);
        for (int i = 0; i < 10; ++i) bombs[positions[i]] = true;
        status = "playing";
        seconds = 0;
    }
    int adjacent(int position) const {
        int row = position / 10, col = position % 10, count = 0;
        for (int dr = -1; dr <= 1; ++dr)
            for (int dc = -1; dc <= 1; ++dc) {
                int nr = row + dr, nc = col + dc;
                if (nr >= 0 && nr < 10 && nc >= 0 && nc < 10 && bombs[nr * 10 + nc]) ++count;
            }
        return count;
    }
    void reveal(int position) {
        if (position < 0 || position >= 100 || status != "playing" || shown[position] != '.') return;
        if (bombs[position]) {
            shown[position] = '*';
            status = "game over";
            return;
        }
        std::deque<int> queue{position};
        while (!queue.empty()) {
            int current = queue.front(); queue.pop_front();
            if (shown[current] != '.') continue;
            int count = adjacent(current);
            shown[current] = count ? static_cast<char>('0' + count) : '-';
            if (count) continue;
            int row = current / 10, col = current % 10;
            for (int dr = -1; dr <= 1; ++dr)
                for (int dc = -1; dc <= 1; ++dc) {
                    int nr = row + dr, nc = col + dc;
                    if (nr >= 0 && nr < 10 && nc >= 0 && nc < 10 &&
                        shown[nr * 10 + nc] == '.') queue.push_back(nr * 10 + nc);
                }
        }
        int hidden_safe = 0;
        for (int i = 0; i < 100; ++i) if (!bombs[i] && shown[i] == '.') ++hidden_safe;
        if (!hidden_safe) status = "You Win!";
    }
    void flag(int position) {
        if (position < 0 || position >= 100 || status != "playing") return;
        if (shown[position] == '.') shown[position] = 'F';
        else if (shown[position] == 'F') shown[position] = '.';
    }
} minesweeper;
}

extern "C" {
EMSCRIPTEN_KEEPALIVE const char* demo_version() { return "FutureShell WebAssembly 1"; }
EMSCRIPTEN_KEEPALIVE const char* shell_boot() {
    shell_directory_name.clear();
    shell_output_text = "Welcome to FutureShell";
    shell_target_name.clear();
    shell_action_code = 0;
    return shell_output_text.c_str();
}
EMSCRIPTEN_KEEPALIVE void shell_run(const char* command, const char* date, const char* directory) {
    shell_directory_name = directory ? directory : "";
    run_shell_command(trim(command ? command : ""), date ? date : "");
}
EMSCRIPTEN_KEEPALIVE const char* shell_output() { return shell_output_text.c_str(); }
EMSCRIPTEN_KEEPALIVE int shell_action() { return shell_action_code; }
EMSCRIPTEN_KEEPALIVE const char* shell_target() { return shell_target_name.c_str(); }
EMSCRIPTEN_KEEPALIVE const char* shell_directory() { return shell_directory_name.c_str(); }
EMSCRIPTEN_KEEPALIVE void calc_reset() { calculator.reset(); }
EMSCRIPTEN_KEEPALIVE const char* calc_press(const char* key) {
    calculator.press(key ? key : "");
    return calculator.value.c_str();
}
EMSCRIPTEN_KEEPALIVE const char* calc_display() { return calculator.value.c_str(); }
EMSCRIPTEN_KEEPALIVE void ttt_reset() { tic_tac_toe.reset(); }
EMSCRIPTEN_KEEPALIVE void ttt_move(int index) { tic_tac_toe.move(index); }
EMSCRIPTEN_KEEPALIVE const char* ttt_board() {
    output.assign(tic_tac_toe.board.begin(), tic_tac_toe.board.end());
    return output.c_str();
}
EMSCRIPTEN_KEEPALIVE const char* ttt_status() { return tic_tac_toe.status.c_str(); }
EMSCRIPTEN_KEEPALIVE void ms_reset() { minesweeper.reset(); }
EMSCRIPTEN_KEEPALIVE void ms_reveal(int position) { minesweeper.reveal(position); }
EMSCRIPTEN_KEEPALIVE void ms_flag(int position) { minesweeper.flag(position); }
EMSCRIPTEN_KEEPALIVE const char* ms_board() {
    output.assign(minesweeper.shown.begin(), minesweeper.shown.end());
    return output.c_str();
}
EMSCRIPTEN_KEEPALIVE const char* ms_status() { return minesweeper.status.c_str(); }
EMSCRIPTEN_KEEPALIVE int ms_seconds() { return minesweeper.seconds; }
EMSCRIPTEN_KEEPALIVE void ms_tick() { if (minesweeper.status == "playing") ++minesweeper.seconds; }
}
