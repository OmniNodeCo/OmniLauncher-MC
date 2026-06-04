#pragma once
#include <string>
#include <map>
#include <vector>
#include <variant>
#include <sstream>
#include <stdexcept>
#include <memory>
#include <algorithm>

namespace json {

class Value;
using Object = std::map<std::string, Value>;
using Array = std::vector<Value>;
using Null = std::nullptr_t;

class Value {
public:
    using Data = std::variant<Null, bool, double, std::string, Array, Object>;
    Data data;

    Value() : data(nullptr) {}
    Value(std::nullptr_t) : data(nullptr) {}
    Value(bool b) : data(b) {}
    Value(int i) : data((double)i) {}
    Value(double d) : data(d) {}
    Value(const char* s) : data(std::string(s)) {}
    Value(const std::string& s) : data(s) {}
    Value(std::string&& s) : data(std::move(s)) {}
    Value(const Array& a) : data(a) {}
    Value(Array&& a) : data(std::move(a)) {}
    Value(const Object& o) : data(o) {}
    Value(Object&& o) : data(std::move(o)) {}

    bool is_null() const { return std::holds_alternative<Null>(data); }
    bool is_bool() const { return std::holds_alternative<bool>(data); }
    bool is_number() const { return std::holds_alternative<double>(data); }
    bool is_string() const { return std::holds_alternative<std::string>(data); }
    bool is_array() const { return std::holds_alternative<Array>(data); }
    bool is_object() const { return std::holds_alternative<Object>(data); }

    bool as_bool() const { return std::get<bool>(data); }
    double as_number() const { return std::get<double>(data); }
    int as_int() const { return (int)std::get<double>(data); }
    const std::string& as_string() const { return std::get<std::string>(data); }
    const Array& as_array() const { return std::get<Array>(data); }
    const Object& as_object() const { return std::get<Object>(data); }
    Array& as_array() { return std::get<Array>(data); }
    Object& as_object() { return std::get<Object>(data); }

    const Value& operator[](const std::string& key) const {
        static Value null_val;
        if (!is_object()) return null_val;
        auto& obj = as_object();
        auto it = obj.find(key);
        return it != obj.end() ? it->second : null_val;
    }

    const Value& operator[](size_t idx) const {
        return as_array().at(idx);
    }

    bool has(const std::string& key) const {
        if (!is_object()) return false;
        return as_object().count(key) > 0;
    }

    size_t size() const {
        if (is_array()) return as_array().size();
        if (is_object()) return as_object().size();
        return 0;
    }
};

class Parser {
    const std::string& src;
    size_t pos = 0;

    void skip_ws() {
        while (pos < src.size() && (src[pos] == ' ' || src[pos] == '\t' || src[pos] == '\n' || src[pos] == '\r'))
            pos++;
    }

    char peek() { skip_ws(); return pos < src.size() ? src[pos] : 0; }
    char next() { skip_ws(); return pos < src.size() ? src[pos++] : 0; }

    std::string parse_string_val() {
        if (next() != '"') throw std::runtime_error("Expected '\"'");
        std::string result;
        while (pos < src.size() && src[pos] != '"') {
            if (src[pos] == '\\') {
                pos++;
                if (pos >= src.size()) break;
                switch (src[pos]) {
                    case '"': result += '"'; break;
                    case '\\': result += '\\'; break;
                    case '/': result += '/'; break;
                    case 'b': result += '\b'; break;
                    case 'f': result += '\f'; break;
                    case 'n': result += '\n'; break;
                    case 'r': result += '\r'; break;
                    case 't': result += '\t'; break;
                    case 'u': {
                        pos++;
                        std::string hex = src.substr(pos, 4);
                        pos += 3;
                        unsigned cp = std::stoul(hex, nullptr, 16);
                        if (cp < 0x80) result += (char)cp;
                        else if (cp < 0x800) {
                            result += (char)(0xC0 | (cp >> 6));
                            result += (char)(0x80 | (cp & 0x3F));
                        } else {
                            result += (char)(0xE0 | (cp >> 12));
                            result += (char)(0x80 | ((cp >> 6) & 0x3F));
                            result += (char)(0x80 | (cp & 0x3F));
                        }
                        break;
                    }
                    default: result += src[pos]; break;
                }
            } else {
                result += src[pos];
            }
            pos++;
        }
        pos++; // closing "
        return result;
    }

    Value parse_value() {
        char c = peek();
        if (c == '"') return Value(parse_string_val());
        if (c == '{') return parse_object();
        if (c == '[') return parse_array();
        if (c == 't') { pos += 4; return Value(true); }
        if (c == 'f') { pos += 5; return Value(false); }
        if (c == 'n') { pos += 4; return Value(); }
        // number
        skip_ws();
        size_t start = pos;
        if (src[pos] == '-') pos++;
        while (pos < src.size() && (std::isdigit(src[pos]) || src[pos] == '.' || src[pos] == 'e' || src[pos] == 'E' || src[pos] == '+' || src[pos] == '-')) {
            if ((src[pos] == 'e' || src[pos] == 'E' || src[pos] == '+' || src[pos] == '-') && pos == start) break;
            pos++;
        }
        return Value(std::stod(src.substr(start, pos - start)));
    }

    Value parse_object() {
        next(); // {
        Object obj;
        if (peek() == '}') { next(); return Value(std::move(obj)); }
        while (true) {
            std::string key = parse_string_val();
            next(); // :
            obj[key] = parse_value();
            char c = next();
            if (c == '}') break;
        }
        return Value(std::move(obj));
    }

    Value parse_array() {
        next(); // [
        Array arr;
        if (peek() == ']') { next(); return Value(std::move(arr)); }
        while (true) {
            arr.push_back(parse_value());
            char c = next();
            if (c == ']') break;
        }
        return Value(std::move(arr));
    }

public:
    Parser(const std::string& s) : src(s) {}
    Value parse() { return parse_value(); }
};

inline Value parse(const std::string& s) {
    Parser p(s);
    return p.parse();
}

inline std::string stringify(const Value& v, int indent = 0, int depth = 0) {
    std::string pad(depth * indent, ' ');
    std::string pad1((depth + 1) * indent, ' ');
    std::string nl = indent > 0 ? "\n" : "";
    std::string sep = indent > 0 ? " " : "";

    if (v.is_null()) return "null";
    if (v.is_bool()) return v.as_bool() ? "true" : "false";
    if (v.is_number()) {
        double d = v.as_number();
        if (d == (int64_t)d) return std::to_string((int64_t)d);
        std::ostringstream oss; oss << d; return oss.str();
    }
    if (v.is_string()) {
        std::string r = "\"";
        for (char c : v.as_string()) {
            switch (c) {
                case '"': r += "\\\""; break;
                case '\\': r += "\\\\"; break;
                case '\n': r += "\\n"; break;
                case '\r': r += "\\r"; break;
                case '\t': r += "\\t"; break;
                default: r += c;
            }
        }
        return r + "\"";
    }
    if (v.is_array()) {
        if (v.size() == 0) return "[]";
        std::string r = "[" + nl;
        for (size_t i = 0; i < v.as_array().size(); i++) {
            r += pad1 + stringify(v.as_array()[i], indent, depth + 1);
            if (i + 1 < v.as_array().size()) r += ",";
            r += nl;
        }
        return r + pad + "]";
    }
    if (v.is_object()) {
        if (v.size() == 0) return "{}";
        std::string r = "{" + nl;
        size_t i = 0;
        for (auto& [k, val] : v.as_object()) {
            r += pad1 + "\"" + k + "\":" + sep + stringify(val, indent, depth + 1);
            if (++i < v.as_object().size()) r += ",";
            r += nl;
        }
        return r + pad + "}";
    }
    return "null";
}

} // namespace json