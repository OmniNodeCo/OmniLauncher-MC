#include "http_client.h"
#include <fstream>
#include <sstream>

#ifdef _WIN32
#include <windows.h>
#include <winhttp.h>
#pragma comment(lib, "winhttp.lib")

struct UrlParts {
    std::wstring host;
    std::wstring path;
    bool https = true;
    int port = 443;
};

static std::wstring to_wide(const std::string& s) {
    if (s.empty()) return {};
    int sz = MultiByteToWideChar(CP_UTF8, 0, s.c_str(), (int)s.size(), nullptr, 0);
    std::wstring w(sz, 0);
    MultiByteToWideChar(CP_UTF8, 0, s.c_str(), (int)s.size(), &w[0], sz);
    return w;
}

static std::string from_wide(const std::wstring& w) {
    if (w.empty()) return {};
    int sz = WideCharToMultiByte(CP_UTF8, 0, w.c_str(), (int)w.size(), nullptr, 0, nullptr, nullptr);
    std::string s(sz, 0);
    WideCharToMultiByte(CP_UTF8, 0, w.c_str(), (int)w.size(), &s[0], sz, nullptr, nullptr);
    return s;
}

static UrlParts parse_url(const std::string& url) {
    UrlParts parts;
    std::wstring wurl = to_wide(url);
    URL_COMPONENTS uc = {};
    uc.dwStructSize = sizeof(uc);
    wchar_t host[256] = {}, path[2048] = {};
    uc.lpszHostName = host;
    uc.dwHostNameLength = 256;
    uc.lpszUrlPath = path;
    uc.dwUrlPathLength = 2048;
    WinHttpCrackUrl(wurl.c_str(), 0, 0, &uc);
    parts.host = host;
    parts.path = path;
    parts.https = (uc.nScheme == INTERNET_SCHEME_HTTPS);
    parts.port = uc.nPort;
    return parts;
}

static std::string winhttp_request(const std::string& url, const std::string& method, const std::string& body, const std::string& content_type, const std::filesystem::path& file_dest, ProgressCallback progress) {
    auto parts = parse_url(url);
    HINTERNET session = WinHttpOpen(L"OmniLauncher/1.0", WINHTTP_ACCESS_TYPE_DEFAULT_PROXY, nullptr, nullptr, 0);
    if (!session) return {};

    HINTERNET connect = WinHttpConnect(session, parts.host.c_str(), parts.port, 0);
    if (!connect) { WinHttpCloseHandle(session); return {}; }

    DWORD flags = parts.https ? WINHTTP_FLAG_SECURE : 0;
    HINTERNET request = WinHttpOpenRequest(connect, to_wide(method).c_str(), parts.path.c_str(), nullptr, nullptr, nullptr, flags);
    if (!request) { WinHttpCloseHandle(connect); WinHttpCloseHandle(session); return {}; }

    // Add headers
    std::wstring headers;
    if (!content_type.empty()) {
        headers = L"Content-Type: " + to_wide(content_type);
    }

    BOOL sent;
    if (body.empty()) {
        sent = WinHttpSendRequest(request, headers.empty() ? WINHTTP_NO_ADDITIONAL_HEADERS : headers.c_str(),
            headers.empty() ? 0 : (DWORD)headers.size(), WINHTTP_NO_REQUEST_DATA, 0, 0, 0);
    } else {
        sent = WinHttpSendRequest(request, headers.empty() ? WINHTTP_NO_ADDITIONAL_HEADERS : headers.c_str(),
            headers.empty() ? 0 : (DWORD)headers.size(), (void*)body.c_str(), (DWORD)body.size(), (DWORD)body.size(), 0);
    }

    if (!sent || !WinHttpReceiveResponse(request, nullptr)) {
        WinHttpCloseHandle(request); WinHttpCloseHandle(connect); WinHttpCloseHandle(session);
        return {};
    }

    // Get content length
    DWORD content_length = 0;
    DWORD cl_size = sizeof(content_length);
    WinHttpQueryHeaders(request, WINHTTP_QUERY_CONTENT_LENGTH | WINHTTP_QUERY_FLAG_NUMBER, nullptr, &content_length, &cl_size, nullptr);

    // Check for redirect (3xx) - WinHttp follows automatically by default

    std::string result;
    std::ofstream fout;
    if (!file_dest.empty()) {
        std::filesystem::create_directories(file_dest.parent_path());
        fout.open(file_dest, std::ios::binary);
    }

    char buf[8192];
    DWORD bytes_read;
    size_t total_read = 0;
    while (WinHttpReadData(request, buf, sizeof(buf), &bytes_read) && bytes_read > 0) {
        total_read += bytes_read;
        if (fout.is_open()) {
            fout.write(buf, bytes_read);
        } else {
            result.append(buf, bytes_read);
        }
        if (progress) {
            progress({content_length, total_read});
        }
    }

    WinHttpCloseHandle(request);
    WinHttpCloseHandle(connect);
    WinHttpCloseHandle(session);
    return result;
}

std::string HttpClient::get(const std::string& url) {
    return winhttp_request(url, "GET", "", "", "", nullptr);
}

std::string HttpClient::post(const std::string& url, const std::string& body, const std::string& content_type) {
    return winhttp_request(url, "POST", body, content_type, "", nullptr);
}

bool HttpClient::download(const std::string& url, const std::filesystem::path& dest, ProgressCallback progress) {
    winhttp_request(url, "GET", "", "", dest, progress);
    return std::filesystem::exists(dest) && std::filesystem::file_size(dest) > 0;
}

#else
// Linux: use libcurl
#include <curl/curl.h>

static size_t write_string_cb(void* ptr, size_t size, size_t nmemb, void* userdata) {
    auto* str = (std::string*)userdata;
    str->append((char*)ptr, size * nmemb);
    return size * nmemb;
}

static size_t write_file_cb(void* ptr, size_t size, size_t nmemb, void* userdata) {
    auto* f = (std::ofstream*)userdata;
    f->write((char*)ptr, size * nmemb);
    return size * nmemb;
}

std::string HttpClient::get(const std::string& url) {
    CURL* curl = curl_easy_init();
    if (!curl) return {};
    std::string result;
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_string_cb);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &result);
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_USERAGENT, "OmniLauncher/1.0");
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 1L);
    curl_easy_perform(curl);
    curl_easy_cleanup(curl);
    return result;
}

std::string HttpClient::post(const std::string& url, const std::string& body, const std::string& content_type) {
    CURL* curl = curl_easy_init();
    if (!curl) return {};
    std::string result;
    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, ("Content-Type: " + content_type).c_str());
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_string_cb);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &result);
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_perform(curl);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    return result;
}

bool HttpClient::download(const std::string& url, const std::filesystem::path& dest, ProgressCallback progress) {
    std::filesystem::create_directories(dest.parent_path());
    CURL* curl = curl_easy_init();
    if (!curl) return false;
    std::ofstream f(dest, std::ios::binary);
    if (!f.is_open()) { curl_easy_cleanup(curl); return false; }
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_file_cb);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &f);
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_USERAGENT, "OmniLauncher/1.0");
    CURLcode res = curl_easy_perform(curl);
    curl_easy_cleanup(curl);
    f.close();
    return res == CURLE_OK;
}
#endif