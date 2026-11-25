"""Native callbacks for the bundled Future Browser project."""

import hashlib
import json


FUTUREBROWSER_FINGERPRINT = '4ba974b374fc5f13e4d1729e055e3396719c8f70757e5ae9a30dc96b3784ad05'


def is_futurebrowser(project):
    controls = project.get('controls', [])
    sources = [project.get('code', '')]
    sources += [(item.get('name_id'), item.get('code', '')) for item in controls]
    fingerprint = hashlib.sha256(json.dumps(sources, ensure_ascii=False).encode()).hexdigest()
    return (len(controls) == 3 and
            {item.get('name_id') for item in controls} == {'lbl_url', 'txt_url', 'btn_go'} and
            fingerprint == FUTUREBROWSER_FINGERPRINT)


FUTUREBROWSER_CPP = r'''
#include <cerrno>
#include <cctype>
#include <cstring>
#include <filesystem>
#include <fcntl.h>
#include <sys/wait.h>
#include <unistd.h>

static void native_msgbox(const std::string& message);

class NativeFutureBrowser {
public:
    Control& c(const std::string& name) {
        auto item = std::find(control_names.begin(), control_names.end(), name);
        return controls[static_cast<std::size_t>(item - control_names.begin())];
    }

    void layout() {
        form_x = form_y = 0;
        form_w = std::max(3, COLS);
        form_h = std::max(3, LINES);
        auto& label = c("lbl_url");
        label.x = 2; label.y = 1;
        label.w = std::max(1, form_w - 4); label.h = 1;
        auto& input = c("txt_url");
        input.x = 2; input.y = 3;
        input.w = std::max(1, form_w - 4); input.h = 1;
        auto& go = c("btn_go");
        go.w = std::min(7, form_w); go.h = 3;
        go.x = std::max(0, (form_w - go.w) / 2); go.y = 5;
    }

    static bool valid_url(const std::string& url) {
        std::size_t scheme = url.rfind("https://", 0) == 0 ? 8 :
                             url.rfind("http://", 0) == 0 ? 7 : 0;
        if (!scheme) return false;
        std::size_t slash = url.find_first_of("/?#", scheme);
        if (slash == std::string::npos || url[slash] != '/' || slash == scheme) return false;
        std::size_t end = url.find_first_of("?#", slash);
        std::string path = url.substr(slash, end == std::string::npos ? end : end - slash);
        return path.size() >= 4 && path.compare(path.size() - 4, 4, ".bin") == 0;
    }

    static std::filesystem::path runner_path() {
        char executable[4096];
        ssize_t size = readlink("/proc/self/exe", executable, sizeof(executable) - 1);
        auto directory = size > 0
            ? std::filesystem::path(std::string(executable, static_cast<std::size_t>(size))).parent_path()
            : std::filesystem::current_path();
        while (!directory.empty()) {
            auto candidate = directory / "run-downloaded-bin.sh";
            if (std::filesystem::is_regular_file(candidate)) return candidate;
            auto parent = directory.parent_path();
            if (parent == directory) break;
            directory = parent;
        }
        return {};
    }

    static int probe(const std::string& url, std::string& response) {
        int pipes[2];
        if (pipe(pipes) != 0) return -1;
        pid_t child = fork();
        if (child == 0) {
            close(pipes[0]);
            dup2(pipes[1], STDERR_FILENO);
            close(pipes[1]);
            int sink = open("/dev/null", O_WRONLY);
            if (sink >= 0) { dup2(sink, STDOUT_FILENO); close(sink); }
            execlp("wget", "wget", "--spider", "--server-response",
                   "--timeout=10", "--tries=1", "--", url.c_str(),
                   static_cast<char*>(nullptr));
            _exit(127);
        }
        close(pipes[1]);
        if (child < 0) { close(pipes[0]); return -1; }
        char buffer[4096];
        ssize_t count;
        while ((count = read(pipes[0], buffer, sizeof(buffer))) > 0)
            if (response.size() < 65536) response.append(buffer, static_cast<std::size_t>(count));
        close(pipes[0]);
        int status = 0;
        while (waitpid(child, &status, 0) < 0) if (errno != EINTR) return -1;
        return WIFEXITED(status) ? WEXITSTATUS(status) : -1;
    }

    void browse() {
        std::string url = c("txt_url").caption;
        while (!url.empty() && std::isspace(static_cast<unsigned char>(url.front()))) url.erase(0, 1);
        while (!url.empty() && std::isspace(static_cast<unsigned char>(url.back()))) url.pop_back();
        if (!valid_url(url)) {
            native_msgbox("Enter an HTTP(S) URL ending in .bin");
            return;
        }
        std::string response;
        int result = probe(url, response);
        if (result != 0) {
            native_msgbox(response.find(" 404") != std::string::npos
                              ? "404 not found" : "Cannot access URL");
            return;
        }
        auto runner = runner_path();
        if (runner.empty()) { native_msgbox("Download runner not found"); return; }

        def_prog_mode();
        endwin();
        pid_t child = fork();
        int status = 0;
        if (child == 0) {
            if (chdir(runner.parent_path().c_str()) != 0) _exit(127);
            execl(runner.c_str(), runner.c_str(), url.c_str(), static_cast<char*>(nullptr));
            _exit(127);
        }
        if (child < 0) status = 127 << 8;
        else while (waitpid(child, &status, 0) < 0) if (errno != EINTR) break;
        reset_prog_mode();
        curs_set(0);
        clearok(stdscr, TRUE);
        if (!WIFEXITED(status) || WEXITSTATUS(status) != 0)
            native_msgbox("Download or app exited with code " +
                          std::to_string(WIFEXITED(status) ? WEXITSTATUS(status) : 1));
    }
};

static NativeFutureBrowser futurebrowser;
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
    if (name == "on_form_load" || name == "on_form_resize") futurebrowser.layout();
    else if (name == "on_enter_txt_url" || name == "on_form_enter" ||
             name == "on_click_btn_go") futurebrowser.browse();
}
'''


def futurebrowser_cpp(project):
    if not is_futurebrowser(project):
        raise ValueError('Future Browser project does not match the native adapter.')
    return FUTUREBROWSER_CPP
