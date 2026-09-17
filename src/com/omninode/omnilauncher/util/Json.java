package com.omninode.omnilauncher.util;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Minimal, dependency-free JSON parser and serializer.
 *
 * Parsing produces: Map&lt;String,Object&gt; (insertion ordered), List&lt;Object&gt;,
 * String, Long/Double, Boolean or null.
 */
public final class Json {

    private Json() {}

    /* ------------------------------------------------------------------ */
    /* Parsing                                                             */
    /* ------------------------------------------------------------------ */

    public static Object parse(String text) {
        Parser p = new Parser(text);
        Object value = p.parseValue();
        p.skipWhitespace();
        if (!p.atEnd()) throw p.error("Trailing characters after JSON value");
        return value;
    }

    @SuppressWarnings("unchecked")
    public static Map<String, Object> parseObject(String text) {
        Object o = parse(text);
        if (!(o instanceof Map)) throw new IllegalArgumentException("Expected JSON object, got " + typeName(o));
        return (Map<String, Object>) o;
    }

    @SuppressWarnings("unchecked")
    public static List<Object> parseArray(String text) {
        Object o = parse(text);
        if (!(o instanceof List)) throw new IllegalArgumentException("Expected JSON array, got " + typeName(o));
        return (List<Object>) o;
    }

    private static final class Parser {
        private final String s;
        private int i;

        Parser(String s) { this.s = s; }

        boolean atEnd() { return i >= s.length(); }

        RuntimeException error(String msg) {
            int line = 1, col = 1;
            for (int k = 0; k < Math.min(i, s.length()); k++) {
                if (s.charAt(k) == '\n') { line++; col = 1; } else col++;
            }
            return new IllegalArgumentException("JSON error at line " + line + ", column " + col + ": " + msg);
        }

        void skipWhitespace() {
            while (i < s.length()) {
                char c = s.charAt(i);
                if (c == ' ' || c == '\t' || c == '\n' || c == '\r') i++;
                else break;
            }
        }

        char peek() {
            if (atEnd()) throw error("Unexpected end of input");
            return s.charAt(i);
        }

        char next() {
            char c = peek();
            i++;
            return c;
        }

        void expect(char c) {
            char got = next();
            if (got != c) throw error("Expected '" + c + "' but found '" + got + "'");
        }

        Object parseValue() {
            skipWhitespace();
            char c = peek();
            switch (c) {
                case '{': return parseObj();
                case '[': return parseArr();
                case '"': return parseStr();
                case 't': expectWord("true"); return Boolean.TRUE;
                case 'f': expectWord("false"); return Boolean.FALSE;
                case 'n': expectWord("null"); return null;
                default:
                    if (c == '-' || (c >= '0' && c <= '9')) return parseNum();
                    throw error("Unexpected character '" + c + "'");
            }
        }

        void expectWord(String word) {
            if (i + word.length() > s.length() || !s.regionMatches(i, word, 0, word.length()))
                throw error("Invalid literal, expected '" + word + "'");
            i += word.length();
        }

        Map<String, Object> parseObj() {
            expect('{');
            Map<String, Object> map = new LinkedHashMap<>();
            skipWhitespace();
            if (peek() == '}') { i++; return map; }
            while (true) {
                skipWhitespace();
                if (peek() != '"') throw error("Expected string key in object");
                String key = parseStr();
                skipWhitespace();
                expect(':');
                map.put(key, parseValue());
                skipWhitespace();
                char c = next();
                if (c == '}') return map;
                if (c != ',') throw error("Expected ',' or '}' in object, found '" + c + "'");
            }
        }

        List<Object> parseArr() {
            expect('[');
            List<Object> list = new ArrayList<>();
            skipWhitespace();
            if (peek() == ']') { i++; return list; }
            while (true) {
                list.add(parseValue());
                skipWhitespace();
                char c = next();
                if (c == ']') return list;
                if (c != ',') throw error("Expected ',' or ']' in array, found '" + c + "'");
            }
        }

        String parseStr() {
            expect('"');
            StringBuilder sb = new StringBuilder();
            while (true) {
                if (atEnd()) throw error("Unterminated string");
                char c = s.charAt(i++);
                if (c == '"') return sb.toString();
                if (c == '\\') {
                    if (atEnd()) throw error("Unterminated escape");
                    char e = s.charAt(i++);
                    switch (e) {
                        case '"': sb.append('"'); break;
                        case '\\': sb.append('\\'); break;
                        case '/': sb.append('/'); break;
                        case 'b': sb.append('\b'); break;
                        case 'f': sb.append('\f'); break;
                        case 'n': sb.append('\n'); break;
                        case 'r': sb.append('\r'); break;
                        case 't': sb.append('\t'); break;
                        case 'u':
                            if (i + 4 > s.length()) throw error("Bad unicode escape");
                            sb.append((char) Integer.parseInt(s.substring(i, i + 4), 16));
                            i += 4;
                            break;
                        default: throw error("Bad escape '\\" + e + "'");
                    }
                } else {
                    sb.append(c);
                }
            }
        }

        Object parseNum() {
            int start = i;
            if (peek() == '-') i++;
            while (!atEnd()) {
                char c = s.charAt(i);
                if ((c >= '0' && c <= '9') || c == '+' || c == '-' || c == '.' || c == 'e' || c == 'E') i++;
                else break;
            }
            String num = s.substring(start, i);
            if (num.isEmpty() || num.equals("-")) throw error("Invalid number");
            if (num.indexOf('.') < 0 && num.indexOf('e') < 0 && num.indexOf('E') < 0) {
                try {
                    return Long.parseLong(num);
                } catch (NumberFormatException ignored) {
                    return Double.parseDouble(num);
                }
            }
            return Double.parseDouble(num);
        }
    }

    /* ------------------------------------------------------------------ */
    /* Serialization                                                       */
    /* ------------------------------------------------------------------ */

    public static String write(Object value) {
        StringBuilder sb = new StringBuilder();
        writeValue(sb, value);
        return sb.toString();
    }

    private static void writeValue(StringBuilder sb, Object v) {
        if (v == null) { sb.append("null"); return; }
        if (v instanceof String s) { writeString(sb, s); return; }
        if (v instanceof Boolean b) { sb.append(b ? "true" : "false"); return; }
        if (v instanceof Double d) {
            if (d == Math.floor(d) && !d.isInfinite() && Math.abs(d) < 9.2e18) sb.append((long) (double) d);
            else sb.append(d);
            return;
        }
        if (v instanceof Float f) { writeValue(sb, (double) f); return; }
        if (v instanceof Number n) { sb.append(n); return; }
        if (v instanceof Map<?, ?> m) {
            sb.append('{');
            boolean first = true;
            for (Map.Entry<?, ?> e : m.entrySet()) {
                if (!first) sb.append(',');
                first = false;
                writeString(sb, String.valueOf(e.getKey()));
                sb.append(':');
                writeValue(sb, e.getValue());
            }
            sb.append('}');
            return;
        }
        if (v instanceof List<?> l) {
            sb.append('[');
            boolean first = true;
            for (Object o : l) {
                if (!first) sb.append(',');
                first = false;
                writeValue(sb, o);
            }
            sb.append(']');
            return;
        }
        if (v instanceof Object[] arr) {
            writeValue(sb, Collections.unmodifiableList(java.util.Arrays.asList(arr)));
            return;
        }
        writeString(sb, v.toString());
    }

    private static void writeString(StringBuilder sb, String s) {
        sb.append('"');
        for (int k = 0; k < s.length(); k++) {
            char c = s.charAt(k);
            switch (c) {
                case '"': sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n"); break;
                case '\r': sb.append("\\r"); break;
                case '\t': sb.append("\\t"); break;
                case '\b': sb.append("\\b"); break;
                case '\f': sb.append("\\f"); break;
                default:
                    if (c < 0x20) sb.append(String.format("\\u%04x", (int) c));
                    else sb.append(c);
            }
        }
        sb.append('"');
    }

    /* ------------------------------------------------------------------ */
    /* Typed accessors for parsed structures                               */
    /* ------------------------------------------------------------------ */

    private static String typeName(Object o) {
        if (o == null) return "null";
        if (o instanceof Map) return "object";
        if (o instanceof List) return "array";
        return o.getClass().getSimpleName();
    }

    public static Map<String, Object> map(Map<String, Object> m, String key) {
        Object o = m == null ? null : m.get(key);
        if (o == null) return null;
        if (o instanceof Map) return (Map<String, Object>) o;
        throw new IllegalArgumentException("Field '" + key + "' is not an object (" + typeName(o) + ")");
    }

    public static List<Object> arr(Map<String, Object> m, String key) {
        Object o = m == null ? null : m.get(key);
        if (o == null) return null;
        if (o instanceof List) return (List<Object>) o;
        throw new IllegalArgumentException("Field '" + key + "' is not an array (" + typeName(o) + ")");
    }

    public static String str(Map<String, Object> m, String key) { return str(m, key, null); }

    public static String str(Map<String, Object> m, String key, String def) {
        Object o = m == null ? null : m.get(key);
        return o == null ? def : String.valueOf(o);
    }

    public static long num(Map<String, Object> m, String key, long def) {
        Object o = m == null ? null : m.get(key);
        if (o instanceof Number n) return n.longValue();
        return def;
    }

    public static double dbl(Map<String, Object> m, String key, double def) {
        Object o = m == null ? null : m.get(key);
        if (o instanceof Number n) return n.doubleValue();
        return def;
    }

    public static boolean bool(Map<String, Object> m, String key, boolean def) {
        Object o = m == null ? null : m.get(key);
        if (o instanceof Boolean b) return b;
        return def;
    }

    /** Converts element to Map if possible (null-safe). */
    @SuppressWarnings("unchecked")
    public static Map<String, Object> asMap(Object o) {
        if (o instanceof Map) return (Map<String, Object>) o;
        return null;
    }

    /** Converts element to List if possible (null-safe). */
    @SuppressWarnings("unchecked")
    public static List<Object> asList(Object o) {
        if (o instanceof List) return (List<Object>) o;
        return null;
    }
}
