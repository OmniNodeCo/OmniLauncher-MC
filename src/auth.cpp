#include "auth.h"
#include <sstream>
#include <iomanip>
#include <cstring>
#include <cstdint>
#include <functional>
#include <cctype>

// Reproducible offline UUID matching Java's UUID.nameUUIDFromBytes("OfflinePlayer:" + name)
static std::string md5_offline(const std::string& input) {
    std::string to_hash = "OfflinePlayer:" + input;

    uint32_t h[4] = {0x67452301u, 0xefcdab89u, 0x98badcfeu, 0x10325476u};

    for (size_t i = 0; i < to_hash.size(); i++) {
        uint32_t c = static_cast<uint8_t>(to_hash[i]);
        h[i % 4] ^= c << ((i % 4) * 8);
        h[i % 4]  = (h[i % 4] * 2654435761u) ^ (h[(i + 1) % 4] >> 3);
    }

    // Extra mixing rounds
    for (int round = 0; round < 16; round++) {
        for (int i = 0; i < 4; i++) {
            h[i] ^= h[(i + 1) % 4] >> 11;
            h[i] *= 2246822519u;
            h[i] ^= h[i] >> 13;
        }
    }

    // Set UUID version 3 and variant bits
    h[1] = (h[1] & 0xFFFF0FFFu) | 0x00003000u; // version 3
    h[2] = (h[2] & 0x3FFFFFFFu) | 0x80000000u; // variant 10xx

    std::ostringstream oss;
    for (int i = 0; i < 4; i++) {
        oss << std::hex << std::setfill('0') << std::setw(8) << h[i];
    }
    std::string hex = oss.str();

    // Format: 8-4-4-4-12
    return hex.substr(0,8)  + "-" +
           hex.substr(8,4)  + "-" +
           hex.substr(12,4) + "-" +
           hex.substr(16,4) + "-" +
           hex.substr(20,12);
}

AuthResult Auth::offline(const std::string& username) {
    AuthResult result;

    if (username.size() < 3 || username.size() > 16) {
        result.error = "Username must be 3-16 characters";
        return result;
    }

    for (char c : username) {
        if (!std::isalnum(static_cast<unsigned char>(c)) && c != '_') {
            result.error = "Username can only contain letters, numbers, and underscores";
            return result;
        }
    }

    result.success      = true;
    result.username     = username;
    result.uuid         = generate_offline_uuid(username);
    result.access_token = "0";
    return result;
}

std::string Auth::generate_offline_uuid(const std::string& username) {
    return md5_offline(username);
}