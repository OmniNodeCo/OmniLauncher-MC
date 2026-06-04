#include "config.h"
#include <fstream>
#include <cstdlib>

#ifdef _WIN32
#include <windows.h>
#include <shlobj.h>
#else
#include <unistd.h>
#include <pwd.h>
#endif

Config& Config::instance() {
    static Config cfg;
    return cfg;
}

fs::path Config::base_dir() const { return base_dir_; }
fs::path Config::versions_dir() const { return base_dir_ / "versions"; }
fs::path Config::assets_dir() const { return base_dir_ / "assets"; }
fs::path Config::libraries_dir() const { return base_dir_ / "libraries"; }
fs::path Config::instances_dir() const { return base_dir_ / "instances"; }
fs::path Config::config_file() const { return base_dir_ / "config.json"; }

void Config::init() {
#ifdef _WIN32
    wchar_t* appdata = nullptr;
    if (SHGetKnownFolderPath(FOLDERID_RoamingAppData, 0, nullptr, &appdata) == S_OK) {
        base_dir_ = fs::path(appdata) / ".omnilauncher";
        CoTaskMemFree(appdata);
    } else {
        base_dir_ = fs::path(std::getenv("APPDATA")) / ".omnilauncher";
    }
#elif defined(__APPLE__)
    const char* home = std::getenv("HOME");
    if (!home) home = getpwuid(getuid())->pw_dir;
    base_dir_ = fs::path(home) / "Library" / "Application Support" / ".omnilauncher";
#else
    const char* home = std::getenv("HOME");
    if (!home) home = getpwuid(getuid())->pw_dir;
    // XDG_DATA_HOME or default
    const char* xdg = std::getenv("XDG_DATA_HOME");
    if (xdg && xdg[0]) {
        base_dir_ = fs::path(xdg) / ".omnilauncher";
    } else {
        base_dir_ = fs::path(home) / ".omnilauncher";
    }
#endif

    fs::create_directories(base_dir_);
    fs::create_directories(versions_dir());
    fs::create_directories(assets_dir());
    fs::create_directories(libraries_dir());
    fs::create_directories(instances_dir());
    fs::create_directories(assets_dir() / "indexes");
    fs::create_directories(assets_dir() / "objects");

    load();
}

void Config::load() {
    auto path = config_file();
    if (!fs::exists(path)) {
        save();
        return;
    }
    std::ifstream f(path);
    std::string content((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    if (content.empty()) return;

    try {
        auto v = json::parse(content);
        if (v.has("username")) username = v["username"].as_string();
        if (v.has("uuid")) uuid = v["uuid"].as_string();
        if (v.has("access_token")) access_token = v["access_token"].as_string();
        if (v.has("selected_version")) selected_version = v["selected_version"].as_string();
        if (v.has("ram_mb")) ram_mb = v["ram_mb"].as_int();
        if (v.has("java_path")) java_path = v["java_path"].as_string();
        if (v.has("jvm_args")) jvm_args = v["jvm_args"].as_string();
        if (v.has("offline_mode")) offline_mode = v["offline_mode"].as_bool();
    } catch (...) {}
}

void Config::save() {
    json::Object obj;
    obj["username"] = username;
    obj["uuid"] = uuid;
    obj["access_token"] = access_token;
    obj["selected_version"] = selected_version;
    obj["ram_mb"] = ram_mb;
    obj["java_path"] = java_path;
    obj["jvm_args"] = jvm_args;
    obj["offline_mode"] = offline_mode;

    std::ofstream f(config_file());
    f << json::stringify(json::Value(std::move(obj)), 2);
}