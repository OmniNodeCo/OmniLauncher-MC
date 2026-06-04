#pragma once
#include <string>
#include <functional>
#include <filesystem>
#include <cstddef>

struct DownloadProgress {
    size_t total;
    size_t current;
};

using ProgressCallback = std::function<void(const DownloadProgress&)>;

class HttpClient {
public:
    static std::string get(const std::string& url);
    static std::string post(const std::string& url,
                            const std::string& body,
                            const std::string& content_type = "application/json");
    static bool download(const std::string& url,
                         const std::filesystem::path& dest,
                         ProgressCallback progress = nullptr);
};