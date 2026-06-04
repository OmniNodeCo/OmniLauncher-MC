#pragma once
#include <string>

struct AuthResult {
    bool success = false;
    std::string username;
    std::string uuid;
    std::string access_token;
    std::string error;
};

class Auth {
public:
    static AuthResult offline(const std::string& username);
    static std::string generate_offline_uuid(const std::string& username);
};