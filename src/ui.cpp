#include "ui.h"
#include "config.h"
#include "auth.h"
#include <thread>

#ifdef _WIN32
#include <windows.h>
#include <commctrl.h>
#include <dwmapi.h>
#include <windowsx.h>

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "dwmapi.lib")
#pragma comment(linker, "\"/manifestdependency:type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='*' publicKeyToken='6595b64144ccf1df' language='*'\"")

// Control IDs
enum {
    ID_VERSION_COMBO = 1001,
    ID_USERNAME_EDIT,
    ID_PLAY_BTN,
    ID_PROGRESS,
    ID_STATUS,
    ID_RAM_SLIDER,
    ID_RAM_LABEL,
    ID_TAB,
    ID_OFFLINE_CHECK,
    ID_JAVA_EDIT,
    ID_JVM_EDIT,
    ID_SNAPSHOT_CHECK,
    ID_REFRESH_BTN,
    ID_BROWSE_JAVA_BTN,
    ID_FOLDER_BTN,
};

// Colors
static COLORREF BG_COLOR = RGB(30, 30, 36);
static COLORREF BG_LIGHTER = RGB(42, 42, 50);
static COLORREF BG_CONTROL = RGB(50, 50, 60);
static COLORREF TEXT_COLOR = RGB(220, 220, 230);
static COLORREF ACCENT_COLOR = RGB(76, 175, 80);
static COLORREF ACCENT_HOVER = RGB(56, 142, 60);
static COLORREF BORDER_COLOR = RGB(60, 60, 72);

static HBRUSH bg_brush = nullptr;
static HBRUSH bg_lighter_brush = nullptr;
static HBRUSH bg_control_brush = nullptr;
static HFONT main_font = nullptr;
static HFONT title_font = nullptr;
static HFONT small_font = nullptr;

static UI* g_ui = nullptr;

static void init_gdi() {
    if (!bg_brush) bg_brush = CreateSolidBrush(BG_COLOR);
    if (!bg_lighter_brush) bg_lighter_brush = CreateSolidBrush(BG_LIGHTER);
    if (!bg_control_brush) bg_control_brush = CreateSolidBrush(BG_CONTROL);
    if (!main_font) main_font = CreateFontW(16, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Segoe UI");
    if (!title_font) title_font = CreateFontW(28, 0, 0, 0, FW_BOLD, 0, 0, 0, DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Segoe UI");
    if (!small_font) small_font = CreateFontW(13, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Segoe UI");
}

static std::wstring to_w(const std::string& s) {
    if (s.empty()) return {};
    int sz = MultiByteToWideChar(CP_UTF8, 0, s.c_str(), -1, nullptr, 0);
    std::wstring w(sz - 1, 0);
    MultiByteToWideChar(CP_UTF8, 0, s.c_str(), -1, &w[0], sz);
    return w;
}

static std::string from_w(const std::wstring& w) {
    if (w.empty()) return {};
    int sz = WideCharToMultiByte(CP_UTF8, 0, w.c_str(), -1, nullptr, 0, nullptr, nullptr);
    std::string s(sz - 1, 0);
    WideCharToMultiByte(CP_UTF8, 0, w.c_str(), -1, &s[0], sz, nullptr, nullptr);
    return s;
}

static std::string get_edit_text(HWND h) {
    int len = GetWindowTextLengthW(h);
    if (len == 0) return {};
    std::wstring buf(len + 1, 0);
    GetWindowTextW(h, &buf[0], len + 1);
    buf.resize(len);
    return from_w(buf);
}

void UI::create_controls() {
    HWND h = (HWND)hwnd_;
    int W = 700, y = 20;

    // Title
    HWND title = CreateWindowW(L"STATIC", L"⬡ OmniLauncher", WS_CHILD | WS_VISIBLE | SS_CENTER,
        0, y, W, 40, h, nullptr, nullptr, nullptr);
    SendMessageW(title, WM_SETFONT, (WPARAM)title_font, TRUE);
    y += 55;

    // Username
    CreateWindowW(L"STATIC", L"Username:", WS_CHILD | WS_VISIBLE,
        30, y, 80, 24, h, nullptr, nullptr, nullptr);
    username_edit_ = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL,
        120, y - 2, 200, 26, h, (HMENU)ID_USERNAME_EDIT, nullptr, nullptr);
    SendMessageW((HWND)username_edit_, WM_SETFONT, (WPARAM)main_font, TRUE);
    SendMessageW((HWND)username_edit_, EM_SETLIMITTEXT, 16, 0);

    // Offline checkbox
    offline_check_ = CreateWindowW(L"BUTTON", L"Offline Mode", WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
        340, y, 130, 24, h, (HMENU)ID_OFFLINE_CHECK, nullptr, nullptr);
    SendMessageW((HWND)offline_check_, WM_SETFONT, (WPARAM)main_font, TRUE);
    y += 40;

    // Version
    CreateWindowW(L"STATIC", L"Version:", WS_CHILD | WS_VISIBLE,
        30, y, 80, 24, h, nullptr, nullptr, nullptr);
    version_combo_ = CreateWindowExW(0, L"COMBOBOX", L"", WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST | WS_VSCROLL,
        120, y - 2, 200, 300, h, (HMENU)ID_VERSION_COMBO, nullptr, nullptr);
    SendMessageW((HWND)version_combo_, WM_SETFONT, (WPARAM)main_font, TRUE);

    // Show snapshots checkbox
    snapshot_check_ = CreateWindowW(L"BUTTON", L"Show Snapshots", WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
        340, y, 140, 24, h, (HMENU)ID_SNAPSHOT_CHECK, nullptr, nullptr);
    SendMessageW((HWND)snapshot_check_, WM_SETFONT, (WPARAM)main_font, TRUE);

    // Refresh button
    CreateWindowW(L"BUTTON", L"↻", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
        500, y - 2, 30, 26, h, (HMENU)ID_REFRESH_BTN, nullptr, nullptr);
    y += 40;

    // RAM slider
    CreateWindowW(L"STATIC", L"RAM:", WS_CHILD | WS_VISIBLE,
        30, y, 50, 24, h, nullptr, nullptr, nullptr);
    ram_slider_ = CreateWindowW(TRACKBAR_CLASSW, L"", WS_CHILD | WS_VISIBLE | TBS_AUTOTICKS,
        85, y - 2, 250, 30, h, (HMENU)ID_RAM_SLIDER, nullptr, nullptr);
    SendMessageW((HWND)ram_slider_, TBM_SETRANGE, TRUE, MAKELPARAM(1, 16));
    SendMessageW((HWND)ram_slider_, TBM_SETPOS, TRUE, 2);
    SendMessageW((HWND)ram_slider_, TBM_SETTICFREQ, 1, 0);

    ram_label_ = CreateWindowW(L"STATIC", L"2 GB", WS_CHILD | WS_VISIBLE,
        345, y, 60, 24, h, (HMENU)ID_RAM_LABEL, nullptr, nullptr);
    SendMessageW((HWND)ram_label_, WM_SETFONT, (WPARAM)main_font, TRUE);
    y += 40;

    // Java Path
    CreateWindowW(L"STATIC", L"Java:", WS_CHILD | WS_VISIBLE,
        30, y, 50, 24, h, nullptr, nullptr, nullptr);
    java_path_edit_ = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL,
        85, y - 2, 480, 26, h, (HMENU)ID_JAVA_EDIT, nullptr, nullptr);
    SendMessageW((HWND)java_path_edit_, WM_SETFONT, (WPARAM)small_font, TRUE);
    
    CreateWindowW(L"BUTTON", L"...", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
        575, y - 2, 30, 26, h, (HMENU)ID_BROWSE_JAVA_BTN, nullptr, nullptr);
    y += 35;

    // JVM Args
    CreateWindowW(L"STATIC", L"JVM:", WS_CHILD | WS_VISIBLE,
        30, y, 50, 24, h, nullptr, nullptr, nullptr);
    jvm_args_edit_ = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL,
        85, y - 2, 520, 26, h, (HMENU)ID_JVM_EDIT, nullptr, nullptr);
    SendMessageW((HWND)jvm_args_edit_, WM_SETFONT, (WPARAM)small_font, TRUE);
    y += 45;

    // Progress bar
    progress_bar_ = CreateWindowW(PROGRESS_CLASSW, L"", WS_CHILD | WS_VISIBLE | PBS_SMOOTH,
        30, y, 640, 20, h, (HMENU)ID_PROGRESS, nullptr, nullptr);
    SendMessageW((HWND)progress_bar_, PBM_SETRANGE, 0, MAKELPARAM(0, 100));
    SendMessageW((HWND)progress_bar_, PBM_SETBARCOLOR, 0, (LPARAM)ACCENT_COLOR);
    SendMessageW((HWND)progress_bar_, PBM_SETBKCOLOR, 0, (LPARAM)BG_CONTROL);
    y += 30;

    // Status label
    status_label_ = CreateWindowW(L"STATIC", L"Ready - Click Refresh to load versions", WS_CHILD | WS_VISIBLE | SS_CENTER,
        30, y, 640, 20, h, (HMENU)ID_STATUS, nullptr, nullptr);
    SendMessageW((HWND)status_label_, WM_SETFONT, (WPARAM)small_font, TRUE);
    y += 35;

    // Play button
    play_button_ = CreateWindowW(L"BUTTON", L"▶  PLAY", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON | BS_OWNERDRAW,
        200, y, 300, 50, h, (HMENU)ID_PLAY_BTN, nullptr, nullptr);

    // Open folder button
    CreateWindowW(L"BUTTON", L"📂 Open Data Folder", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
        30, y + 60, 150, 28, h, (HMENU)ID_FOLDER_BTN, nullptr, nullptr);

    // Set all static fonts
    EnumChildWindows(h, [](HWND child, LPARAM) -> BOOL {
        wchar_t cls[64];
        GetClassNameW(child, cls, 64);
        if (wcscmp(cls, L"Static") == 0) {
            HFONT f = (HFONT)SendMessageW(child, WM_GETFONT, 0, 0);
            if (!f) SendMessageW(child, WM_SETFONT, (WPARAM)main_font, TRUE);
        }
        return TRUE;
    }, 0);
}

void UI::load_config_to_ui() {
    auto& cfg = Config::instance();
    SetWindowTextW((HWND)username_edit_, to_w(cfg.username).c_str());
    SendMessageW((HWND)offline_check_, BM_SETCHECK, cfg.offline_mode ? BST_CHECKED : BST_UNCHECKED, 0);
    
    int gb = cfg.ram_mb / 1024;
    if (gb < 1) gb = 2;
    if (gb > 16) gb = 16;
    SendMessageW((HWND)ram_slider_, TBM_SETPOS, TRUE, gb);
    SetWindowTextW((HWND)ram_label_, to_w(std::to_string(gb) + " GB").c_str());
    
    SetWindowTextW((HWND)java_path_edit_, to_w(cfg.java_path).c_str());
    SetWindowTextW((HWND)jvm_args_edit_, to_w(cfg.jvm_args).c_str());
}

void UI::save_config_from_ui() {
    auto& cfg = Config::instance();
    cfg.username = get_edit_text((HWND)username_edit_);
    cfg.offline_mode = SendMessageW((HWND)offline_check_, BM_GETCHECK, 0, 0) == BST_CHECKED;
    
    int gb = (int)SendMessageW((HWND)ram_slider_, TBM_GETPOS, 0, 0);
    cfg.ram_mb = gb * 1024;
    
    cfg.java_path = get_edit_text((HWND)java_path_edit_);
    cfg.jvm_args = get_edit_text((HWND)jvm_args_edit_);

    // Get selected version
    int sel = (int)SendMessageW((HWND)version_combo_, CB_GETCURSEL, 0, 0);
    if (sel >= 0 && sel < (int)versions_.size()) {
        cfg.selected_version = versions_[sel].id;
    }

    cfg.save();
}

void UI::populate_versions() {
    SendMessageW((HWND)version_combo_, CB_RESETCONTENT, 0, 0);
    bool show_snapshots = SendMessageW((HWND)snapshot_check_, BM_GETCHECK, 0, 0) == BST_CHECKED;
    versions_ = launcher_.get_versions(!show_snapshots);
    
    int select_idx = -1;
    for (size_t i = 0; i < versions_.size(); i++) {
        std::string label = versions_[i].id;
        if (versions_[i].type != "release") label += " [" + versions_[i].type + "]";
        SendMessageW((HWND)version_combo_, CB_ADDSTRING, 0, (LPARAM)to_w(label).c_str());
        if (versions_[i].id == Config::instance().selected_version) {
            select_idx = (int)i;
        }
    }
    if (select_idx >= 0) {
        SendMessageW((HWND)version_combo_, CB_SETCURSEL, select_idx, 0);
    } else if (!versions_.empty()) {
        SendMessageW((HWND)version_combo_, CB_SETCURSEL, 0, 0);
    }
}

void UI::update_status(const std::string& text, int percent) {
    SetWindowTextW((HWND)status_label_, to_w(text).c_str());
    if (percent >= 0) {
        SendMessageW((HWND)progress_bar_, PBM_SETPOS, percent, 0);
    }
}

void UI::on_refresh() {
    if (loading_) return;
    loading_ = true;
    EnableWindow((HWND)play_button_, FALSE);
    update_status("Fetching version list...", 0);

    std::thread([this]() {
        bool ok = launcher_.fetch_version_manifest();
        PostMessageW((HWND)hwnd_, WM_USER + 1, ok ? 1 : 0, 0);
    }).detach();
}

void UI::on_play() {
    if (loading_) return;
    
    save_config_from_ui();
    auto& cfg = Config::instance();

    if (cfg.username.empty()) {
        MessageBoxW((HWND)hwnd_, L"Please enter a username", L"OmniLauncher", MB_OK | MB_ICONWARNING);
        return;
    }

    // Auth
    auto auth = Auth::offline(cfg.username);
    if (!auth.success) {
        MessageBoxW((HWND)hwnd_, to_w(auth.error).c_str(), L"Auth Error", MB_OK | MB_ICONERROR);
        return;
    }
    cfg.uuid = auth.uuid;
    cfg.access_token = auth.access_token;
    cfg.save();

    int sel = (int)SendMessageW((HWND)version_combo_, CB_GETCURSEL, 0, 0);
    if (sel < 0 || sel >= (int)versions_.size()) {
        MessageBoxW((HWND)hwnd_, L"Please select a version", L"OmniLauncher", MB_OK | MB_ICONWARNING);
        return;
    }

    std::string version_id = versions_[sel].id;
    loading_ = true;
    EnableWindow((HWND)play_button_, FALSE);

    std::thread([this, version_id]() {
        launcher_.download_version(version_id, [this](const LaunchProgress& p) {
            PostMessageW((HWND)hwnd_, WM_USER + 2, 0, 0);
            // We need to pass data; use a simpler approach
            update_status(p.stage, p.percent);
        });
        
        bool ok = launcher_.launch_game(version_id, [this](const LaunchProgress& p) {
            update_status(p.stage, p.percent);
        });

        PostMessageW((HWND)hwnd_, WM_USER + 3, ok ? 1 : 0, 0);
    }).detach();
}

LRESULT CALLBACK UI::WndProc(void* hwnd, unsigned int msg, unsigned long long wp, long long lp) {
    switch (msg) {
    case WM_CREATE:
        return 0;

    case WM_CTLCOLORSTATIC:
    case WM_CTLCOLOREDIT: {
        HDC hdc = (HDC)wp;
        SetTextColor(hdc, TEXT_COLOR);
        SetBkColor(hdc, msg == WM_CTLCOLOREDIT ? BG_CONTROL : BG_COLOR);
        return (LRESULT)(msg == WM_CTLCOLOREDIT ? bg_control_brush : bg_brush);
    }

    case WM_CTLCOLORBTN: {
        HDC hdc = (HDC)wp;
        SetTextColor(hdc, TEXT_COLOR);
        SetBkColor(hdc, BG_COLOR);
        return (LRESULT)bg_brush;
    }

    case WM_CTLCOLORLISTBOX: {
        HDC hdc = (HDC)wp;
        SetTextColor(hdc, TEXT_COLOR);
        SetBkColor(hdc, BG_CONTROL);
        return (LRESULT)bg_control_brush;
    }

    case WM_ERASEBKGND: {
        RECT rc;
        GetClientRect((HWND)hwnd, &rc);
        FillRect((HDC)wp, &rc, bg_brush);
        return 1;
    }

    case WM_DRAWITEM: {
        auto* dis = (DRAWITEMSTRUCT*)lp;
        if (dis->CtlID == ID_PLAY_BTN) {
            bool hover = (dis->itemState & ODS_SELECTED);
            HBRUSH br = CreateSolidBrush(hover ? ACCENT_HOVER : ACCENT_COLOR);
            
            // Rounded rect
            HRGN rgn = CreateRoundRectRgn(dis->rcItem.left, dis->rcItem.top, dis->rcItem.right, dis->rcItem.bottom, 12, 12);
            FillRgn(dis->hDC, rgn, br);
            DeleteObject(rgn);
            DeleteObject(br);

            SetTextColor(dis->hDC, RGB(255, 255, 255));
            SetBkMode(dis->hDC, TRANSPARENT);
            SelectObject(dis->hDC, title_font);
            
            wchar_t text[64];
            GetWindowTextW(dis->hwndItem, text, 64);
            DrawTextW(dis->hDC, text, -1, &dis->rcItem, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
            return TRUE;
        }
        break;
    }

    case WM_HSCROLL: {
        if ((HWND)lp == (HWND)g_ui->ram_slider_) {
            int gb = (int)SendMessageW((HWND)g_ui->ram_slider_, TBM_GETPOS, 0, 0);
            SetWindowTextW((HWND)g_ui->ram_label_, to_w(std::to_string(gb) + " GB").c_str());
        }
        break;
    }

    case WM_COMMAND: {
        int id = LOWORD(wp);
        int code = HIWORD(wp);
        
        switch (id) {
        case ID_PLAY_BTN:
            g_ui->on_play();
            break;
        case ID_REFRESH_BTN:
            g_ui->on_refresh();
            break;
        case ID_SNAPSHOT_CHECK:
            g_ui->populate_versions();
            break;
        case ID_BROWSE_JAVA_BTN: {
            OPENFILENAMEW ofn = {};
            wchar_t file[MAX_PATH] = {};
            ofn.lStructSize = sizeof(ofn);
            ofn.hwndOwner = (HWND)hwnd;
            ofn.lpstrFilter = L"Java Executable\0javaw.exe;java.exe\0All Files\0*.*\0";
            ofn.lpstrFile = file;
            ofn.nMaxFile = MAX_PATH;
            ofn.Flags = OFN_FILEMUSTEXIST;
            if (GetOpenFileNameW(&ofn)) {
                SetWindowTextW((HWND)g_ui->java_path_edit_, file);
            }
            break;
        }
        case ID_FOLDER_BTN: {
            std::wstring dir = Config::instance().base_dir().wstring();
            ShellExecuteW(nullptr, L"open", dir.c_str(), nullptr, nullptr, SW_SHOWNORMAL);
            break;
        }
        }
        break;
    }

    case WM_USER + 1: { // Version fetch complete
        g_ui->loading_ = false;
        EnableWindow((HWND)g_ui->play_button_, TRUE);
        if (wp) {
            g_ui->populate_versions();
            g_ui->update_status("Versions loaded - " + std::to_string(g_ui->versions_.size()) + " available", 0);
        } else {
            g_ui->update_status("Failed to fetch versions: " + g_ui->launcher_.last_error(), 0);
        }
        break;
    }

    case WM_USER + 3: { // Launch complete
        g_ui->loading_ = false;
        EnableWindow((HWND)g_ui->play_button_, TRUE);
        if (!wp) {
            g_ui->update_status("Launch failed: " + g_ui->launcher_.last_error(), 0);
            MessageBoxW((HWND)hwnd, to_w("Launch failed: " + g_ui->launcher_.last_error()).c_str(), L"Error", MB_OK | MB_ICONERROR);
        }
        break;
    }

    case WM_DESTROY:
        g_ui->save_config_from_ui();
        PostQuitMessage(0);
        return 0;

    case WM_GETMINMAXINFO: {
        auto* mmi = (MINMAXINFO*)lp;
        mmi->ptMinTrackSize = {720, 530};
        mmi->ptMaxTrackSize = {720, 530};
        break;
    }
    }
    return DefWindowProcW((HWND)hwnd, msg, wp, lp);
}

int UI::run() {
    g_ui = this;
    init_gdi();

    INITCOMMONCONTROLSEX icc = {sizeof(icc), ICC_STANDARD_CLASSES | ICC_PROGRESS_CLASS | ICC_BAR_CLASSES};
    InitCommonControlsEx(&icc);

    WNDCLASSEXW wc = {};
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = (WNDPROC)WndProc;
    wc.hInstance = GetModuleHandleW(nullptr);
    wc.lpszClassName = L"OmniLauncherClass";
    wc.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    wc.hIcon = LoadIconW(wc.hInstance, MAKEINTRESOURCEW(101));
    wc.hIconSm = wc.hIcon;
    wc.hbrBackground = bg_brush;
    RegisterClassExW(&wc);

    RECT desk;
    SystemParametersInfoW(SPI_GETWORKAREA, 0, &desk, 0);
    int sx = (desk.right - 720) / 2;
    int sy = (desk.bottom - 530) / 2;

    hwnd_ = CreateWindowExW(
        0, L"OmniLauncherClass", L"OmniLauncher - Minecraft Launcher",
        WS_OVERLAPPEDWINDOW & ~WS_MAXIMIZEBOX & ~WS_THICKFRAME,
        sx, sy, 720, 530,
        nullptr, nullptr, wc.hInstance, nullptr);

    // Enable dark title bar (Windows 10+)
    BOOL dark = TRUE;
    DwmSetWindowAttribute((HWND)hwnd_, 20, &dark, sizeof(dark)); // DWMWA_USE_IMMERSIVE_DARK_MODE

    create_controls();
    load_config_to_ui();

    ShowWindow((HWND)hwnd_, SW_SHOW);
    UpdateWindow((HWND)hwnd_);

    // Auto-refresh
    on_refresh();

    MSG msg;
    while (GetMessageW(&msg, nullptr, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    return (int)msg.wParam;
}

#else
// Linux GTK3 implementation
#include <gtk/gtk.h>

static GtkWidget* window_ = nullptr;
static GtkWidget* username_entry_ = nullptr;
static GtkWidget* version_combo_ = nullptr;
static GtkWidget* progress_bar_ = nullptr;
static GtkWidget* status_label_ = nullptr;
static GtkWidget* ram_scale_ = nullptr;
static GtkWidget* ram_label_ = nullptr;
static GtkWidget* java_entry_ = nullptr;
static GtkWidget* jvm_entry_ = nullptr;
static GtkWidget* snapshot_check_ = nullptr;

static Launcher g_launcher;
static std::vector<VersionInfo> g_versions;
static bool g_loading = false;

static void populate_versions_gtk() {
    gtk_combo_box_text_remove_all(GTK_COMBO_BOX_TEXT(version_combo_));
    bool show_snap = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(snapshot_check_));
    g_versions = g_launcher.get_versions(!show_snap);
    int sel = -1;
    for (size_t i = 0; i < g_versions.size(); i++) {
        std::string label = g_versions[i].id;
        if (g_versions[i].type != "release") label += " [" + g_versions[i].type + "]";
        gtk_combo_box_text_append_text(GTK_COMBO_BOX_TEXT(version_combo_), label.c_str());
        if (g_versions[i].id == Config::instance().selected_version) sel = (int)i;
    }
    if (sel >= 0) gtk_combo_box_set_active(GTK_COMBO_BOX(version_combo_), sel);
    else if (!g_versions.empty()) gtk_combo_box_set_active(GTK_COMBO_BOX(version_combo_), 0);
}

static gboolean on_refresh_done(gpointer data) {
    bool ok = GPOINTER_TO_INT(data);
    g_loading = false;
    if (ok) {
        populate_versions_gtk();
        gtk_label_set_text(GTK_LABEL(status_label_), "Versions loaded");
    } else {
        gtk_label_set_text(GTK_LABEL(status_label_), "Failed to fetch versions");
    }
    return FALSE;
}

static void on_refresh_click(GtkWidget*, gpointer) {
    if (g_loading) return;
    g_loading = true;
    gtk_label_set_text(GTK_LABEL(status_label_), "Fetching versions...");
    std::thread([]() {
        bool ok = g_launcher.fetch_version_manifest();
        g_idle_add(on_refresh_done, GINT_TO_POINTER(ok));
    }).detach();
}

static gboolean on_launch_done(gpointer data) {
    bool ok = GPOINTER_TO_INT(data);
    g_loading = false;
    if (!ok) {
        gtk_label_set_text(GTK_LABEL(status_label_), ("Failed: " + g_launcher.last_error()).c_str());
    }
    return FALSE;
}

static void on_play_click(GtkWidget*, gpointer) {
    if (g_loading) return;

    std::string username = gtk_entry_get_text(GTK_ENTRY(username_entry_));
    auto auth = Auth::offline(username);
    if (!auth.success) {
        gtk_label_set_text(GTK_LABEL(status_label_), auth.error.c_str());
        return;
    }

    auto& cfg = Config::instance();
    cfg.username = username;
    cfg.uuid = auth.uuid;
    cfg.access_token = auth.access_token;
    cfg.ram_mb = (int)gtk_range_get_value(GTK_RANGE(ram_scale_)) * 1024;
    cfg.java_path = gtk_entry_get_text(GTK_ENTRY(java_entry_));
    cfg.jvm_args = gtk_entry_get_text(GTK_ENTRY(jvm_entry_));

    int sel = gtk_combo_box_get_active(GTK_COMBO_BOX(version_combo_));
    if (sel < 0 || sel >= (int)g_versions.size()) return;
    std::string vid = g_versions[sel].id;
    cfg.selected_version = vid;
    cfg.save();

    g_loading = true;
    gtk_label_set_text(GTK_LABEL(status_label_), "Downloading...");

    std::thread([vid]() {
        g_launcher.download_version(vid, [](const LaunchProgress& p) {
            g_idle_add([](gpointer d) -> gboolean {
                return FALSE;
            }, nullptr);
        });
        bool ok = g_launcher.launch_game(vid);
        g_idle_add(on_launch_done, GINT_TO_POINTER(ok));
    }).detach();
}

int UI::run() {
    gtk_init(nullptr, nullptr);

    // CSS for dark theme
    GtkCssProvider* css = gtk_css_provider_new();
    gtk_css_provider_load_from_data(css,
        "window { background-color: #1e1e24; }"
        "label { color: #dcdce6; }"
        "entry { background-color: #32323c; color: #dcdce6; border: 1px solid #3c3c48; }"
        "button { background-color: #4CAF50; color: white; border-radius: 6px; padding: 8px 16px; }"
        "button:hover { background-color: #388E3C; }"
        "combobox button { background-color: #32323c; color: #dcdce6; }"
        "scale { color: #4CAF50; }"
        "progressbar trough { background-color: #32323c; } progressbar progress { background-color: #4CAF50; }",
        -1, nullptr);
    gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),
        GTK_STYLE_PROVIDER(css), GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

    window_ = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(window_), "OmniLauncher - Minecraft Launcher");
    gtk_window_set_default_size(GTK_WINDOW(window_), 700, 500);
    gtk_window_set_resizable(GTK_WINDOW(window_), FALSE);
    g_signal_connect(window_, "destroy", G_CALLBACK(gtk_main_quit), nullptr);

    GtkWidget* vbox = gtk_box_new(GTK_ORIENTATION_VERTICAL, 10);
    gtk_container_set_border_width(GTK_CONTAINER(vbox), 20);
    gtk_container_add(GTK_CONTAINER(window_), vbox);

    // Title
    GtkWidget* title = gtk_label_new("⬡ OmniLauncher");
    PangoAttrList* attrs = pango_attr_list_new();
    pango_attr_list_insert(attrs, pango_attr_size_new(24 * PANGO_SCALE));
    pango_attr_list_insert(attrs, pango_attr_weight_new(PANGO_WEIGHT_BOLD));
    gtk_label_set_attributes(GTK_LABEL(title), attrs);
    pango_attr_list_unref(attrs);
    gtk_box_pack_start(GTK_BOX(vbox), title, FALSE, FALSE, 5);

    // Username row
    GtkWidget* urow = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
    gtk_box_pack_start(GTK_BOX(urow), gtk_label_new("Username:"), FALSE, FALSE, 0);
    username_entry_ = gtk_entry_new();
    gtk_entry_set_max_length(GTK_ENTRY(username_entry_), 16);
    gtk_entry_set_text(GTK_ENTRY(username_entry_), Config::instance().username.c_str());
    gtk_box_pack_start(GTK_BOX(urow), username_entry_, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), urow, FALSE, FALSE, 0);

    // Version row
    GtkWidget* vrow = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
    gtk_box_pack_start(GTK_BOX(vrow), gtk_label_new("Version:"), FALSE, FALSE, 0);
    version_combo_ = gtk_combo_box_text_new();
    gtk_box_pack_start(GTK_BOX(vrow), version_combo_, TRUE, TRUE, 0);
    snapshot_check_ = gtk_check_button_new_with_label("Snapshots");
    g_signal_connect(snapshot_check_, "toggled", G_CALLBACK(+[](GtkWidget*, gpointer) { populate_versions_gtk(); }), nullptr);
    gtk_box_pack_start(GTK_BOX(vrow), snapshot_check_, FALSE, FALSE, 0);
    GtkWidget* refresh_btn = gtk_button_new_with_label("↻");
    g_signal_connect(refresh_btn, "clicked", G_CALLBACK(on_refresh_click), nullptr);
    gtk_box_pack_start(GTK_BOX(vrow), refresh_btn, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), vrow, FALSE, FALSE, 0);

    // RAM
    GtkWidget* rrow = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
    gtk_box_pack_start(GTK_BOX(rrow), gtk_label_new("RAM (GB):"), FALSE, FALSE, 0);
    ram_scale_ = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 1, 16, 1);
    gtk_range_set_value(GTK_RANGE(ram_scale_), Config::instance().ram_mb / 1024);
    gtk_box_pack_start(GTK_BOX(rrow), ram_scale_, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), rrow, FALSE, FALSE, 0);

    // Java
    GtkWidget* jrow = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
    gtk_box_pack_start(GTK_BOX(jrow), gtk_label_new("Java:"), FALSE, FALSE, 0);
    java_entry_ = gtk_entry_new();
    gtk_entry_set_text(GTK_ENTRY(java_entry_), Config::instance().java_path.c_str());
    gtk_entry_set_placeholder_text(GTK_ENTRY(java_entry_), "Auto-detect");
    gtk_box_pack_start(GTK_BOX(jrow), java_entry_, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), jrow, FALSE, FALSE, 0);

    // JVM args
    GtkWidget* jvrow = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
    gtk_box_pack_start(GTK_BOX(jvrow), gtk_label_new("JVM Args:"), FALSE, FALSE, 0);
    jvm_entry_ = gtk_entry_new();
    gtk_entry_set_text(GTK_ENTRY(jvm_entry_), Config::instance().jvm_args.c_str());
    gtk_box_pack_start(GTK_BOX(jvrow), jvm_entry_, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), jvrow, FALSE, FALSE, 0);

    // Progress
    progress_bar_ = gtk_progress_bar_new();
    gtk_box_pack_start(GTK_BOX(vbox), progress_bar_, FALSE, FALSE, 5);

    // Status
    status_label_ = gtk_label_new("Ready - Click ↻ to load versions");
    gtk_box_pack_start(GTK_BOX(vbox), status_label_, FALSE, FALSE, 0);

    // Play button
    GtkWidget* play_btn = gtk_button_new_with_label("▶  PLAY");
    g_signal_connect(play_btn, "clicked", G_CALLBACK(on_play_click), nullptr);
    gtk_box_pack_start(GTK_BOX(vbox), play_btn, FALSE, FALSE, 10);

    gtk_widget_show_all(window_);

    // Auto-refresh
    on_refresh_click(nullptr, nullptr);

    gtk_main();
    return 0;
}

#endif