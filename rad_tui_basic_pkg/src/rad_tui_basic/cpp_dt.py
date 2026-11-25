"""Native C++ adapter for the checked-in DT desktop project."""

import hashlib
import json


def _fingerprint(project):
    sources = [project.get('code', '')]
    sources += [(item.get('name_id'), item.get('code', ''))
                for item in project.get('controls', [])]
    return hashlib.sha256(json.dumps(sources, ensure_ascii=False).encode()).hexdigest()


# The native adapter must be reviewed whenever DT's Python callbacks change.
DT_FINGERPRINT = 'e478d84cb4c55fb0d6d7fcd5b6cc79e54be55add53d6aa6b033579876fb2a81a'


def is_dt(project):
    names = {item.get('name_id') for item in project.get('controls', [])}
    return (len(names) == 7 and
            {'btn_back', 'btn_refresh', 'lbl_path', 'btn_prev',
             'btn_next', 'lbl_page', 'dt_timer'} <= names and
            _fingerprint(project) == DT_FINGERPRINT)


DT_CPP = r'''
#include <cerrno>
#include <cctype>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <sys/ioctl.h>
#include <sys/wait.h>
#include <unistd.h>

class NativeDesktop {
public:
    std::filesystem::path root, current;
    std::vector<std::filesystem::path> entries;
    std::size_t fixed_controls = 0;
    int page = 0;
    std::string status;

    Control& c(const std::string& name) {
        auto item = std::find(control_names.begin(), control_names.end(), name);
        return controls[static_cast<std::size_t>(item - control_names.begin())];
    }

    static std::string lower(std::string value) {
        for (char& ch : value)
            ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
        return value;
    }

    static bool is_program(const std::filesystem::path& path) {
        return lower(path.extension().string()) == ".bin";
    }

    static std::string icon_for(const std::filesystem::path& path,
                                const std::string& fallback = "⚡") {
        auto stem_icon = path;
        stem_icon.replace_extension(".icons");
        for (const auto& candidate : {stem_icon, std::filesystem::path(path.string() + ".icons")}) {
            std::ifstream input(candidate);
            std::string icon;
            if (input >> icon) return icon;
        }
        return fallback;
    }

    void start() {
        char executable[4096];
        ssize_t length = readlink("/proc/self/exe", executable, sizeof(executable) - 1);
        auto directory = length > 0
            ? std::filesystem::path(std::string(executable, static_cast<std::size_t>(length))).parent_path()
            : std::filesystem::current_path();
        root = directory / "DTF";
        current = root;
        fixed_controls = controls.size();
        std::error_code error;
        std::filesystem::create_directories(root / "tools", error);
        if (!error) std::filesystem::create_directories(root / "games", error);
        if (error) status = "Cannot create DTF: " + error.message();
        std::cout << "\033]777;rad-tui;hide-keyboard\007" << std::flush;
        scan();
    }

    void layout() {
        form_x = form_y = 0;
        form_w = std::max(3, COLS);
        form_h = std::max(3, LINES);
        int width = form_w, height = form_h;
        int nav_width = std::min(11, std::max(6, width / 4));
        auto& back = c("btn_back");
        back.x = 0; back.y = 0; back.w = nav_width; back.h = 1;
        auto& refresh_button = c("btn_refresh");
        refresh_button.x = nav_width; refresh_button.y = 0;
        refresh_button.w = nav_width; refresh_button.h = 1;
        auto& path_label = c("lbl_path");
        path_label.x = std::min(width - 1, 2 * nav_width + 1);
        path_label.y = 0; path_label.w = std::max(1, width - path_label.x); path_label.h = 1;
        std::error_code error;
        auto relative = std::filesystem::relative(current, root, error);
        path_label.caption = error || relative.empty() || relative == "."
            ? "DTF" : "DTF/" + relative.string();

        int row_height = height >= 18 ? 3 : 1;
        int columns = std::max(1, std::min(4, width / 20));
        int grid_width = std::min(width, columns * 20);
        int grid_left = (width - grid_width) / 2;
        int tile_width = grid_width / columns;
        int rows = std::max(1, (height - 3) / row_height);
        int page_size = columns * rows;
        int last_page = std::max(0, (static_cast<int>(entries.size()) - 1) / page_size);
        page = std::min(page, last_page);
        for (std::size_t index = fixed_controls; index < controls.size(); ++index)
            controls[index].x = -50;
        int first = page * page_size;
        int end = std::min(static_cast<int>(entries.size()), first + page_size);
        for (int index = first; index < end; ++index) {
            int slot = index - first;
            auto& button = controls[fixed_controls + static_cast<std::size_t>(index)];
            button.x = grid_left + (slot % columns) * tile_width;
            button.y = 2 + (slot / columns) * row_height;
            button.w = tile_width; button.h = row_height;
        }
        int footer_y = height - 1;
        auto& previous = c("btn_prev");
        previous.x = page > 0 ? 0 : -50;
        previous.y = footer_y; previous.w = nav_width; previous.h = 1;
        auto& next = c("btn_next");
        next.x = page < last_page ? width - nav_width : -50;
        next.y = footer_y; next.w = nav_width; next.h = 1;
        auto& page_label = c("lbl_page");
        page_label.x = nav_width; page_label.y = footer_y;
        page_label.w = std::max(1, width - 2 * nav_width); page_label.h = 1;
        page_label.caption = status.empty()
            ? std::to_string(entries.size()) + " items  •  page " + std::to_string(page + 1) + "/" + std::to_string(last_page + 1)
            : status;
    }

    void scan() {
        controls.resize(fixed_controls);
        control_names.resize(fixed_controls);
        focused = pressed_control = -1;
        entries.clear();
        std::vector<std::filesystem::path> folders, programs;
        std::error_code error;
        std::filesystem::directory_iterator item(current, error), end;
        for (; !error && item != end; item.increment(error)) {
            auto path = item->path();
            std::error_code type_error;
            bool directory = std::filesystem::is_directory(path, type_error);
            if (directory && !std::filesystem::is_symlink(path, type_error))
                folders.push_back(path);
            else if (std::filesystem::is_regular_file(path, type_error) && is_program(path))
                programs.push_back(path);
        }
        auto by_name = [](const auto& left, const auto& right) {
            return lower(left.filename().string()) < lower(right.filename().string());
        };
        std::sort(folders.begin(), folders.end(), by_name);
        std::sort(programs.begin(), programs.end(), by_name);
        entries.insert(entries.end(), folders.begin(), folders.end());
        entries.insert(entries.end(), programs.begin(), programs.end());
        if (error) status = "Cannot open folder: " + error.message();
        Control template_button = c("btn_back");
        for (std::size_t index = 0; index < entries.size(); ++index) {
            const auto& path = entries[index];
            std::error_code type_error;
            bool directory = std::filesystem::is_directory(path, type_error);
            Control button = template_button;
            button.type = 3;
            button.x = -50; button.y = 0; button.w = button.h = 1;
            button.caption = directory ? icon_for(path, "🗂️") + " " + path.filename().string()
                                       : icon_for(path) + " " + path.stem().string();
            controls.push_back(button);
            control_names.push_back("dt_entry_" + std::to_string(index));
        }
        layout();
    }

    void open(std::size_t index) {
        if (index >= entries.size()) return;
        const auto path = entries[index];
        std::error_code error;
        if (std::filesystem::is_directory(path, error) && !std::filesystem::is_symlink(path, error)) {
            current = path;
            page = 0; status.clear(); scan();
        } else if (std::filesystem::is_regular_file(path, error) && is_program(path)) {
            launch(path);
        }
    }

    void launch(const std::filesystem::path& path) {
        def_prog_mode();
        endwin();
        pid_t child = fork();
        int result = 0;
        if (child == 0) {
            if (chdir(path.parent_path().c_str()) != 0) _exit(127);
            execl(path.c_str(), path.filename().c_str(), static_cast<char*>(nullptr));
            _exit(127);
        }
        if (child < 0) {
            status = "Cannot run " + path.filename().string() + ": " + std::strerror(errno);
        } else if (waitpid(child, &result, 0) < 0) {
            status = "Cannot wait for " + path.filename().string();
        } else if (!WIFEXITED(result) || WEXITSTATUS(result) != 0) {
            status = path.filename().string() + " exited with code " +
                     std::to_string(WIFEXITED(result) ? WEXITSTATUS(result) : 128 + WTERMSIG(result));
        } else status.clear();
        reset_prog_mode();
        curs_set(0);
        clearok(stdscr, TRUE);
        scan();
    }

    void back() {
        if (current != root) {
            current = current.parent_path();
            page = 0; status.clear(); scan();
        }
    }
};

static NativeDesktop dt;
static void native_start_hook() {}
static void native_tick_hook() {
    winsize size{};
    if (ioctl(STDIN_FILENO, TIOCGWINSZ, &size) == 0 && size.ws_row && size.ws_col &&
        (size.ws_row != LINES || size.ws_col != COLS))
        resizeterm(size.ws_row, size.ws_col);
}
static void native_draw_hook() {}
static void native_cursor_hook() {}
static bool native_key_hook(wint_t key) {
    if (key == KEY_BACKSPACE || key == 127) { dt.back(); return true; }
    return false;
}
static bool native_mouse_hook(const MEVENT&) { return false; }
static void native_end_hook() {}
static void dispatch(const std::string& name) {
    if (name == "on_form_load") dt.start();
    else if (name == "on_form_resize" || name == "on_tick_dt_timer") dt.layout();
    else if (name == "on_click_btn_back") dt.back();
    else if (name == "on_click_btn_refresh") { dt.status.clear(); dt.scan(); }
    else if (name == "on_click_btn_prev") { if (dt.page > 0) --dt.page; dt.layout(); }
    else if (name == "on_click_btn_next") { ++dt.page; dt.layout(); }
    else if (name.rfind("on_click_dt_entry_", 0) == 0)
        dt.open(static_cast<std::size_t>(std::atoi(name.c_str() + 18)));
}
'''


def dt_cpp(project):
    if not is_dt(project):
        raise ValueError('DT project does not match the native adapter.')
    return DT_CPP
