#pragma once
#include <string>
#include <filesystem>
#include "json.h"

namespace fs = std::filesystem;

class Config {
public:
    static Config& instance();

    fs::path base_dir() const;
    fs::path versions_dir() const;
    fs::path assets_dir() const;
    fs::path libraries_dir() const;
    fs::path instances_dir() const;
    fs::path config_file() const;

    void init();
    void load();
    void save();

    std::string username;
    std::string uuid;
    std::string access_token;
    std::string selected_version;
    int ram_mb = 2048;
    std::string java_path;
    std::string jvm_args;
    bool offline_mode = true;

private:
    Config() = default;
    fs::path base_dir_;
};