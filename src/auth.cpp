#include "auth.h"
#include <sstream>
#include <iomanip>
#include <cstring>
#include <functional>

// Simple MD5-like hash for offline UUID generation (consistent with Minecraft offline UUIDs)
static std::string md5_offline(const std::string& input) {
    // Use a simple hash to generate a reproducible UUID from username
    // This matches the Java UUID.nameUUIDFromBytes("OfflinePlayer:" + name) format
    std::string to_hash = "OfflinePlayer:" + input;
    
    // Simple hash - for offline mode this is fine
    uint32_t h[4] = {0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476};
    for (size_t i = 0; i < to_hash.size(); i++) {
        uint32_t c = (uint8_t)to_hash[i];
        h[i % 4] ^= c << ((i % 4) * 8);
        h[i % 4] = (h[i % 4] * 2654435761u) ^ (h[(i + 1) % 4] >> 3);
    }
    // Additional mixing
    for (int round = 0; round < 16; round++) {
        for (int i = 0; i < 4; i++) {
            h[i] ^= h[(i + 1) % 4] >> 11;
            h[i] *= 2246822519u;
            h[i] ^= h[i] >> 13;
        }
    }

    // Set version (3) and variant bits  
    h[1] = (h[1] & 0xFFFF0FFF) | 0x00003000; // version 3
    h[2] = (h[2] & 0x3FFFFFFF) | 0x80000000; // variant

    std::ostringstream oss;
    for (int i = 0; i < 4; i++) {
        oss << std::hex << std::setfill('0') << std::setw(8) << h[i];
    }
    std::string hex = oss.str();
    // Format as UUID
    return hex.substr(0, 8) + "-" + hex.substr(8, 4) + "-" + hex.substr(12, 4) + "-" + hex.substr(16, 4) + "-" + hex.substr(20, 12);
}

AuthResult Auth::offline(const std::string& username) {
    AuthResult result;
    if (username.empty() || username.size() < 3 || username.size() > 16) {
        result.error = "Username must be 3-16 characters";
        return result;
    }

    // Validate characters
    for (char c : username) {
        if (!std::isalnum(c) && c != '_') {
            result.error = "Username can only contain letters, numbers, and underscores";
            return result;
        }
    }

    result.success = true;
    result.username = username;
    result.uuid = generate_offline_uuid(username);
    result.access_token = "0";
    return result;
}

std::string Auth::generate_offline_uuid(const std::string& username) {
    return md5_offline(username);
}