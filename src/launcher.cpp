#include "launcher.h"
#include "http_client.h"
#include "config.h"
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <map>

#ifdef _WIN32
#include <windows.h>
#include <shlwapi.h>
#else
#include <unistd.h>
#include <sys/wait.h>
#endif

namespace fs = std::filesystem;

static const char* VERSION_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json";
static const char* RESOURCES_URL = "https://resources.download.minecraft.net/";

bool Launcher::fetch_version_manifest() {
    std::string data = HttpClient::get(VERSION_MANIFEST_URL);
    if (data.empty()) {
        error_ = "Failed to fetch version manifest";
        return false;
    }

    try {
        manifest_ = json::parse(data);
        versions_.clear();
        if (manifest_.has("versions")) {
            for (auto& v : manifest_["versions"].as_array()) {
                VersionInfo vi;
                vi.id = v["id"].as_string();
                vi.type = v["type"].as_string();
                vi.url = v["url"].as_string();
                if (v.has("releaseTime")) vi.release_time = v["releaseTime"].as_string();
                versions_.push_back(vi);
            }
        }
        return true;
    } catch (const std::exception& e) {
        error_ = std::string("Failed to parse manifest: ") + e.what();
        return false;
    }
}

std::vector<VersionInfo> Launcher::get_versions(bool releases_only) const {
    if (!releases_only) return versions_;
    std::vector<VersionInfo> filtered;
    for (auto& v : versions_) {
        if (v.type == "release") filtered.push_back(v);
    }
    return filtered;
}

std::string Launcher::get_os_name() {
#ifdef _WIN32
    return "windows";
#elif defined(__APPLE__)
    return "osx";
#else
    return "linux";
#endif
}

bool Launcher::is_library_allowed(const json::Value& lib) {
    if (!lib.has("rules")) return true;

    bool allowed = false;
    for (auto& rule : lib["rules"].as_array()) {
        std::string action = rule["action"].as_string();
        if (rule.has("os")) {
            std::string os_name = rule["os"]["name"].as_string();
            if (os_name == get_os_name()) {
                allowed = (action == "allow");
            }
        } else {
            allowed = (action == "allow");
        }
    }
    return allowed;
}

bool Launcher::download_client_jar(const json::Value& vj, LaunchProgressCallback progress) {
    if (!vj.has("downloads") || !vj["downloads"].has("client")) {
        error_ = "No client download info";
        return false;
    }

    std::string url = vj["downloads"]["client"]["url"].as_string();
    std::string id = vj["id"].as_string();
    fs::path jar_path = Config::instance().versions_dir() / id / (id + ".jar");

    if (fs::exists(jar_path)) return true;

    if (progress) progress({"Downloading client...", 0});

    return HttpClient::download(url, jar_path, [&](const DownloadProgress& dp) {
        if (progress && dp.total > 0) {
            progress({"Downloading client...", (int)(dp.current * 100 / dp.total)});
        }
    });
}

bool Launcher::download_libraries(const json::Value& vj, LaunchProgressCallback progress) {
    if (!vj.has("libraries")) return true;

    auto& libs = vj["libraries"].as_array();
    int total = (int)libs.size();
    int current = 0;

    for (auto& lib : libs) {
        current++;
        if (!is_library_allowed(lib)) continue;

        if (lib.has("downloads") && lib["downloads"].has("artifact")) {
            auto& artifact = lib["downloads"]["artifact"];
            std::string url = artifact["url"].as_string();
            std::string path = artifact["path"].as_string();
            fs::path dest = Config::instance().libraries_dir() / path;

            if (!fs::exists(dest)) {
                if (progress) {
                    std::string name = lib.has("name") ? lib["name"].as_string() : path;
                    progress({"Libraries: " + name, current * 100 / total});
                }
                HttpClient::download(url, dest);
            }
        }
    }
    return true;
}

bool Launcher::download_assets(const json::Value& vj, LaunchProgressCallback progress) {
    if (!vj.has("assetIndex")) return true;

    std::string index_id = vj["assetIndex"]["id"].as_string();
    std::string index_url = vj["assetIndex"]["url"].as_string();
    fs::path index_path = Config::instance().assets_dir() / "indexes" / (index_id + ".json");

    if (!fs::exists(index_path)) {
        if (progress) progress({"Downloading asset index...", 0});
        HttpClient::download(index_url, index_path);
    }

    std::ifstream f(index_path);
    std::string content((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    f.close();
    if (content.empty()) return false;

    try {
        auto index = json::parse(content);
        if (!index.has("objects")) return true;

        auto& objects = index["objects"].as_object();
        int total = (int)objects.size();
        int current = 0;

        for (auto& [name, obj] : objects) {
            current++;
            std::string hash = obj["hash"].as_string();
            std::string prefix = hash.substr(0, 2);
            fs::path dest = Config::instance().assets_dir() / "objects" / prefix / hash;

            if (!fs::exists(dest)) {
                if (progress && current % 50 == 0) {
                    progress({"Assets: " + std::to_string(current) + "/" + std::to_string(total),
                              current * 100 / total});
                }
                std::string url = std::string(RESOURCES_URL) + prefix + "/" + hash;
                HttpClient::download(url, dest);
            }
        }
    } catch (...) {
        return false;
    }
    return true;
}

bool Launcher::download_version(const std::string& version_id, LaunchProgressCallback progress) {
    std::string version_url;
    for (auto& v : versions_) {
        if (v.id == version_id) {
            version_url = v.url;
            break;
        }
    }
    if (version_url.empty()) {
        error_ = "Version not found: " + version_id;
        return false;
    }

    fs::path version_dir = Config::instance().versions_dir() / version_id;
    fs::path json_path = version_dir / (version_id + ".json");

    if (!fs::exists(json_path)) {
        if (progress) progress({"Downloading version info...", 0});
        fs::create_directories(version_dir);
        HttpClient::download(version_url, json_path);
    }

    std::ifstream f(json_path);
    std::string content((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    f.close();

    json::Value vj;
    try {
        vj = json::parse(content);
    } catch (...) {
        error_ = "Failed to parse version JSON";
        return false;
    }

    if (!download_client_jar(vj, progress)) return false;
    if (!download_libraries(vj, progress)) return false;
    if (!download_assets(vj, progress)) return false;

    if (progress) progress({"Ready!", 100});
    return true;
}

std::string Launcher::build_classpath(const json::Value& vj) {
    std::string cp;
#ifdef _WIN32
    char sep = ';';
#else
    char sep = ':';
#endif

    if (vj.has("libraries")) {
        for (auto& lib : vj["libraries"].as_array()) {
            if (!is_library_allowed(lib)) continue;
            if (lib.has("downloads") && lib["downloads"].has("artifact")) {
                std::string path = lib["downloads"]["artifact"]["path"].as_string();
                fs::path full = Config::instance().libraries_dir() / path;
                if (fs::exists(full)) {
                    if (!cp.empty()) cp += sep;
                    cp += full.string();
                }
            }
        }
    }

    std::string id = vj["id"].as_string();
    fs::path client = Config::instance().versions_dir() / id / (id + ".jar");
    if (!cp.empty()) cp += sep;
    cp += client.string();

    return cp;
}

std::string Launcher::resolve_main_class(const json::Value& vj) {
    if (vj.has("mainClass")) return vj["mainClass"].as_string();
    return "net.minecraft.client.main.Main";
}

std::vector<std::string> Launcher::build_game_args(const json::Value& vj) {
    auto& cfg = Config::instance();
    std::vector<std::string> args;

    std::string id = vj["id"].as_string();
    std::string asset_index = vj.has("assetIndex") ? vj["assetIndex"]["id"].as_string() : id;
    std::string version_type = vj.has("type") ? vj["type"].as_string() : "release";

    std::map<std::string, std::string> vars = {
        {"${auth_player_name}",  cfg.username},
        {"${version_name}",      id},
        {"${game_directory}",    cfg.base_dir().string()},
        {"${assets_root}",       cfg.assets_dir().string()},
        {"${assets_index_name}", asset_index},
        {"${auth_uuid}",         cfg.uuid},
        {"${auth_access_token}", cfg.access_token.empty() ? "0" : cfg.access_token},
        {"${user_type}",         "legacy"},
        {"${version_type}",      version_type},
        {"${user_properties}",   "{}"},
        {"${resolution_width}",  "854"},
        {"${resolution_height}", "480"},
        {"${auth_session}",      "token:" + (cfg.access_token.empty() ? "0" : cfg.access_token)},
        {"${game_assets}",       cfg.assets_dir().string()},
    };

    auto replace_vars = [&](std::string s) {
        for (auto& [k, v] : vars) {
            size_t pos;
            while ((pos = s.find(k)) != std::string::npos)
                s.replace(pos, k.size(), v);
        }
        return s;
    };

    if (vj.has("arguments") && vj["arguments"].has("game")) {
        for (auto& arg : vj["arguments"]["game"].as_array()) {
            if (arg.is_string()) {
                args.push_back(replace_vars(arg.as_string()));
            }
            // skip rule-based conditional args (objects) for simplicity
        }
    } else if (vj.has("minecraftArguments")) {
        std::string mc_args = replace_vars(vj["minecraftArguments"].as_string());
        std::istringstream iss(mc_args);
        std::string tok;
        while (iss >> tok) args.push_back(tok);
    }

    return args;
}

std::string Launcher::find_java() {
    auto& cfg = Config::instance();
    if (!cfg.java_path.empty() && fs::exists(cfg.java_path))
        return cfg.java_path;

#ifdef _WIN32
    // Check JAVA_HOME first
    const char* java_home = std::getenv("JAVA_HOME");
    if (java_home) {
        fs::path jp = fs::path(java_home) / "bin" / "javaw.exe";
        if (fs::exists(jp)) return jp.string();
        jp = fs::path(java_home) / "bin" / "java.exe";
        if (fs::exists(jp)) return jp.string();
    }

    // Check common install paths
    std::vector<std::string> search_dirs = {
        "C:\\Program Files\\Java",
        "C:\\Program Files\\Eclipse Adoptium",
        "C:\\Program Files\\Microsoft",
        "C:\\Program Files\\Zulu",
        "C:\\Program Files\\BellSoft",
        "C:\\Program Files (x86)\\Java",
    };
    for (auto& dir : search_dirs) {
        if (!fs::exists(dir)) continue;
        for (auto& entry : fs::directory_iterator(dir)) {
            fs::path javaw = entry.path() / "bin" / "javaw.exe";
            if (fs::exists(javaw)) return javaw.string();
        }
    }
    return "javaw";
#else
    const char* java_home = std::getenv("JAVA_HOME");
    if (java_home) {
        fs::path jp = fs::path(java_home) / "bin" / "java";
        if (fs::exists(jp)) return jp.string();
    }
    return "java";
#endif
}

bool Launcher::launch_game(const std::string& version_id, LaunchProgressCallback progress) {
    fs::path json_path = Config::instance().versions_dir() / version_id / (version_id + ".json");
    if (!fs::exists(json_path)) {
        error_ = "Version not downloaded";
        return false;
    }

    std::ifstream f(json_path);
    std::string content((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    f.close();

    json::Value vj;
    try {
        vj = json::parse(content);
    } catch (...) {
        error_ = "Failed to parse version JSON";
        return false;
    }

    if (progress) progress({"Building launch command...", 50});

    std::string java       = find_java();
    std::string classpath  = build_classpath(vj);
    std::string main_class = resolve_main_class(vj);
    auto game_args         = build_game_args(vj);
    auto& cfg              = Config::instance();

    // natives directory
    fs::path natives_dir = Config::instance().versions_dir() / version_id / "natives";
    fs::create_directories(natives_dir);

    std::vector<std::string> cmd;
    cmd.push_back(java);
    cmd.push_back("-Xmx" + std::to_string(cfg.ram_mb) + "m");
    cmd.push_back("-Xms256m");
    cmd.push_back("-Djava.library.path=" + natives_dir.string());
    cmd.push_back("-Dfile.encoding=UTF-8");

    if (!cfg.jvm_args.empty()) {
        std::istringstream iss(cfg.jvm_args);
        std::string tok;
        while (iss >> tok) cmd.push_back(tok);
    }

    cmd.push_back("-cp");
    cmd.push_back(classpath);
    cmd.push_back(main_class);
    for (auto& a : game_args) cmd.push_back(a);

    if (progress) progress({"Launching Minecraft " + version_id + "...", 90});

#ifdef _WIN32
    // Build quoted command line
    std::string cmdline;
    for (size_t i = 0; i < cmd.size(); i++) {
        if (i > 0) cmdline += " ";
        // Quote any argument containing spaces
        if (cmd[i].find(' ') != std::string::npos) {
            cmdline += "\"" + cmd[i] + "\"";
        } else {
            cmdline += cmd[i];
        }
    }

    // Convert to wide string
    int wsz = MultiByteToWideChar(CP_UTF8, 0, cmdline.c_str(), -1, nullptr, 0);
    std::vector<wchar_t> wcmd(wsz);
    MultiByteToWideChar(CP_UTF8, 0, cmdline.c_str(), -1, wcmd.data(), wsz);

    std::wstring wdir = Config::instance().base_dir().wstring();

    STARTUPINFOW si = {};
    si.cb = sizeof(si);
    PROCESS_INFORMATION pi = {};

    if (CreateProcessW(nullptr, wcmd.data(), nullptr, nullptr,
                       FALSE, CREATE_NO_WINDOW, nullptr,
                       wdir.c_str(), &si, &pi)) {
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        if (progress) progress({"Game launched!", 100});
        return true;
    }

    DWORD err = GetLastError();
    error_ = "Failed to launch process (error " + std::to_string(err) + ")";
    return false;
#else
    pid_t pid = fork();
    if (pid == 0) {
        std::vector<char*> argv;
        for (auto& s : cmd) argv.push_back(const_cast<char*>(s.c_str()));
        argv.push_back(nullptr);
        if (chdir(Config::instance().base_dir().c_str()) != 0) {}
        execvp(argv[0], argv.data());
        _exit(1);
    } else if (pid > 0) {
        if (progress) progress({"Game launched!", 100});
        return true;
    }
    error_ = "Failed to fork process";
    return false;
#endif
}