/* Downloadable, browser-loadable tic-tac-toe logic. The RAD-TUI form in
 * tic-tac-toe.json supplies the screen; these exports supply the game state.
 * Keep this module free of Emscripten JS glue so WebAssembly.instantiate works
 * directly on the bytes downloaded by Future Browser. */
#include <stdint.h>

static char board[9];
static int status;
static uint32_t random_state = 1;

static int wins(const char *cells, char player) {
    static const int lines[8][3] = {
        {0,1,2}, {3,4,5}, {6,7,8}, {0,3,6},
        {1,4,7}, {2,5,8}, {0,4,8}, {2,4,6}
    };
    for (int i = 0; i < 8; ++i)
        if (cells[lines[i][0]] == player && cells[lines[i][1]] == player &&
            cells[lines[i][2]] == player) return 1;
    return 0;
}

static int full(void) {
    for (int i = 0; i < 9; ++i) if (board[i] == ' ') return 0;
    return 1;
}

void ttt_seed(uint32_t seed) { random_state = seed ? seed : 1; }

void ttt_reset(void) {
    for (int i = 0; i < 9; ++i) board[i] = ' ';
    status = 0;
}

int ttt_cell(int index) { return index >= 0 && index < 9 ? board[index] : 0; }
int ttt_status_code(void) { return status; }

void ttt_move(int index) {
    if (index < 0 || index >= 9 || status || board[index] != ' ') return;
    board[index] = 'X';
    if (wins(board, 'X')) { status = 1; return; }
    if (full()) { status = 3; return; }

    int empty[9], count = 0, move = -1;
    for (int i = 0; i < 9; ++i) if (board[i] == ' ') empty[count++] = i;
    for (int player = 0; player < 2 && move < 0; ++player) {
        char mark = player ? 'X' : 'O';
        for (int j = 0; j < count; ++j) {
            int candidate = empty[j];
            board[candidate] = mark;
            int winning = wins(board, mark);
            board[candidate] = ' ';
            if (winning) { move = candidate; break; }
        }
    }
    if (move < 0) {
        random_state = random_state * 1664525u + 1013904223u;
        move = empty[random_state % (uint32_t)count];
    }
    board[move] = 'O';
    if (wins(board, 'O')) status = 2;
    else if (full()) status = 3;
}
