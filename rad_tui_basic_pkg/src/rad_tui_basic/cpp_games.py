"""Native callback adapters for the bundled Tic Tac Toe and Minesweeper games."""

import hashlib
import json


def _fingerprint(project):
    sources = [project.get('code', '')]
    sources += [(item.get('name_id'), item.get('code', ''))
                for item in project.get('controls', [])]

    def menus(items):
        for item in items or []:
            yield item.get('name'), item.get('code', '')
            yield from menus(item.get('sub', []))

    sources += list(menus(project.get('menus')))
    return hashlib.sha256(json.dumps(sources, ensure_ascii=False).encode()).hexdigest()


# Review each adapter when the corresponding JSON project's callbacks change.
TIC_TAC_TOE_FINGERPRINT = '4f6da9ba650103b7aa63be3793d090127318571622a332c4a984394bbe062924'
MINESWEEPER_FINGERPRINT = '6c9ec2753f398ac707c13ffa36e2634a0804048c9154d4fc1b58c9ca29a4b5b0'


def is_tic_tac_toe(project):
    names = {item.get('name_id') for item in project.get('controls', [])}
    return (len(project.get('controls', [])) == 11 and
            names == {'lbl_status', 'btn_reset', *(f'btn{i}' for i in range(9))} and
            _fingerprint(project) == TIC_TAC_TOE_FINGERPRINT)


def is_minesweeper(project):
    names = {item.get('name_id') for item in project.get('controls', [])}
    expected = {'face_txt', 'time_txt', 'timer1',
                *(f'b{row}_{col}' for row in range(10) for col in range(10))}
    return (len(project.get('controls', [])) == 103 and names == expected and
            _fingerprint(project) == MINESWEEPER_FINGERPRINT)


TIC_TAC_TOE_CPP = r'''
#include <array>
#include <random>

class NativeTicTacToe {
public:
    std::array<char, 9> board{};
    bool game_over = false;
    std::mt19937 random{std::random_device{}()};

    Control& control(const std::string& name) {
        auto item = std::find(control_names.begin(), control_names.end(), name);
        return controls[static_cast<std::size_t>(item - control_names.begin())];
    }

    void update_ui() {
        for (int index = 0; index < 9; ++index)
            control("btn" + std::to_string(index)).caption.assign(1, board[index]);
    }

    void reset() {
        board.fill(' ');
        game_over = false;
        control("lbl_status").caption = "Your turn (X)";
        update_ui();
    }

    static bool check_win(const std::array<char, 9>& cells, char player) {
        constexpr int wins[8][3] = {
            {0, 1, 2}, {3, 4, 5}, {6, 7, 8}, {0, 3, 6},
            {1, 4, 7}, {2, 5, 8}, {0, 4, 8}, {2, 4, 6},
        };
        for (const auto& line : wins)
            if (cells[line[0]] == player && cells[line[1]] == player &&
                cells[line[2]] == player) return true;
        return false;
    }

    bool full() const {
        return std::find(board.begin(), board.end(), ' ') == board.end();
    }

    void ai_move() {
        if (game_over) return;
        std::vector<int> empty;
        for (int index = 0; index < 9; ++index)
            if (board[index] == ' ') empty.push_back(index);
        if (empty.empty()) return;
        int move = -1;
        for (char player : {'O', 'X'}) {
            for (int candidate : empty) {
                auto trial = board;
                trial[candidate] = player;
                if (check_win(trial, player)) { move = candidate; break; }
            }
            if (move != -1) break;
        }
        if (move == -1) {
            std::uniform_int_distribution<std::size_t> choose(0, empty.size() - 1);
            move = empty[choose(random)];
        }
        board[move] = 'O';
        update_ui();
        if (check_win(board, 'O')) {
            control("lbl_status").caption = "AI Wins!";
            game_over = true;
        } else if (full()) {
            control("lbl_status").caption = "Draw!";
            game_over = true;
        } else control("lbl_status").caption = "Your turn (X)";
    }

    void player_move(int index) {
        if (index < 0 || index >= 9 || game_over || board[index] != ' ') return;
        board[index] = 'X';
        update_ui();
        if (check_win(board, 'X')) {
            control("lbl_status").caption = "You Win!";
            game_over = true;
        } else if (full()) {
            control("lbl_status").caption = "Draw!";
            game_over = true;
        } else {
            control("lbl_status").caption = "AI thinking...";
            ai_move();
        }
    }
};

static NativeTicTacToe tic_tac_toe;
static void native_start_hook() {}
static void native_tick_hook() {}
static void native_draw_hook() {}
static void native_cursor_hook() {}
static bool native_key_hook(wint_t) { return false; }
static bool native_mouse_hook(const MEVENT&) { return false; }
static void native_end_hook() {}
static void dispatch(const std::string& name) {
    if (name == "on_form_load" || name == "on_click_btn_reset") tic_tac_toe.reset();
    else if (name.size() == 13 && name.rfind("on_click_btn", 0) == 0 &&
             name.back() >= '0' && name.back() <= '8')
        tic_tac_toe.player_move(name.back() - '0');
}
'''


MINESWEEPER_CPP = r'''
#include <array>
#include <deque>
#include <numeric>
#include <random>

static void native_msgbox(const std::string& message);

class NativeMinesweeper {
public:
    std::array<std::array<bool, 10>, 10> bombs{};
    bool game_over = false;
    std::mt19937 random{std::random_device{}()};

    Control& control(const std::string& name) {
        auto item = std::find(control_names.begin(), control_names.end(), name);
        return controls[static_cast<std::size_t>(item - control_names.begin())];
    }

    Control& cell(int row, int col) {
        return control("b" + std::to_string(row) + "_" + std::to_string(col));
    }

    void start() {
        for (auto& row : bombs) row.fill(false);
        std::array<int, 100> positions{};
        std::iota(positions.begin(), positions.end(), 0);
        std::shuffle(positions.begin(), positions.end(), random);
        for (int index = 0; index < 10; ++index)
            bombs[positions[index] / 10][positions[index] % 10] = true;
        game_over = false;
    }

    int adjacent(int row, int col) const {
        int count = 0;
        for (int dr = -1; dr <= 1; ++dr)
            for (int dc = -1; dc <= 1; ++dc) {
                int next_row = row + dr, next_col = col + dc;
                if (next_row >= 0 && next_row < 10 && next_col >= 0 && next_col < 10 &&
                    bombs[next_row][next_col]) ++count;
            }
        return count;
    }

    void reveal(int row, int col) {
        if (row < 0 || row >= 10 || col < 0 || col >= 10) return;
        auto& button = cell(row, col);
        if (button.caption != "" && button.caption != "F") return;
        if (bombs[row][col]) {
            control("face_txt").caption = "(T_T)";
            button.caption = "*";
            button.bg_color = 15;
            native_msgbox("game over");
            game_over = true;
            return;
        }
        control("face_txt").caption = "(^_^)";
        std::deque<std::pair<int, int>> queue{{row, col}};
        while (!queue.empty()) {
            auto [current_row, current_col] = queue.front();
            queue.pop_front();
            auto& current = cell(current_row, current_col);
            if (current.caption != "" && current.caption != "F") continue;
            int count = adjacent(current_row, current_col);
            if (count > 0) current.caption = std::to_string(count);
            else {
                current.caption = "-";
                for (int dr = -1; dr <= 1; ++dr)
                    for (int dc = -1; dc <= 1; ++dc) {
                        if (dr == 0 && dc == 0) continue;
                        int next_row = current_row + dr, next_col = current_col + dc;
                        if (next_row >= 0 && next_row < 10 && next_col >= 0 && next_col < 10 &&
                            cell(next_row, next_col).caption.empty())
                            queue.emplace_back(next_row, next_col);
                    }
            }
        }
    }

    void flag(int row, int col) {
        auto& button = cell(row, col);
        button.caption = button.caption == "F" ? "" : "F";
    }

    void tick() {
        if (game_over) { running = false; return; }
        auto& timer = control("time_txt");
        timer.caption = std::to_string(std::stoi(timer.caption) + 1);
    }
};

static NativeMinesweeper minesweeper;
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
    if (name == "on_form_load") { minesweeper.start(); return; }
    if (name == "on_tick_timer1") { minesweeper.tick(); return; }
    const std::string prefixes[] = {
        "button_down_b", "on_button_up_b", "on_right_click_b", "on_click_b"
    };
    for (int event = 0; event < 4; ++event) {
        const auto& prefix = prefixes[event];
        if (name.rfind(prefix, 0) != 0) continue;
        std::string position = name.substr(prefix.size());
        if (position.size() != 3 || position[1] != '_' ||
            position[0] < '0' || position[0] > '9' ||
            position[2] < '0' || position[2] > '9') return;
        int row = position[0] - '0', col = position[2] - '0';
        if (event == 0) minesweeper.control("face_txt").caption = "(.O.)";
        else if (event == 2) minesweeper.flag(row, col);
        else minesweeper.reveal(row, col);
        return;
    }
}
'''


def tic_tac_toe_cpp(project):
    if not is_tic_tac_toe(project):
        raise ValueError('Tic Tac Toe project does not match the native adapter.')
    return TIC_TAC_TOE_CPP


def minesweeper_cpp(project):
    if not is_minesweeper(project):
        raise ValueError('Minesweeper project does not match the native adapter.')
    return MINESWEEPER_CPP
