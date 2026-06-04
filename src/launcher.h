#pragma once
#include <string>
#include <vector>
#include <functional>
#include <map>
#include "json.h"

struct VersionInfo {
    std::string id;
    std::string type;
    std::string url;
    std::string release_time;
};

struct LaunchProgress {
    std::string stage;
    int percent;
};

using LaunchProgressCallback = std::function<void(const LaunchProgress&)>;

class Launcher {
public:
    bool fetch_version_manifest();
    std::vector<VersionInfo> get_versions(bool releases_only = true) const;
    bool download_version(const std::string& version_id, LaunchProgressCallback progress = nullptr);
    bool launch_game(const std::string& version_id, LaunchProgressCallback progress = nullptr);
    std::string last_error() const { return error_; }

private:
    json::Value manifest_;
    std::vector<VersionInfo> versions_;
    std::string error_;

    bool download_libraries(const json::Value& version_json, LaunchProgressCallback progress);
    bool download_assets(const json::Value& version_json, LaunchProgressCallback progress);
    bool download_client_jar(const json::Value& version_json, LaunchProgressCallback progress);
    std::string build_classpath(const json::Value& version_json);
    std::string resolve_main_class(const json::Value& version_json);
    std::vector<std::string> build_game_args(const json::Value& version_json);
    bool is_library_allowed(const json::Value& lib);
    std::string get_os_name();
    std::string find_java();
};