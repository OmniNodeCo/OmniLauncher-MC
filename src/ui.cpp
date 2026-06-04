#include "ui.h"
#include "config.h"
#include "auth.h"
#include <thread>
#include <string>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#include <commdlg.h>
#include <shellapi.h>
#include <shlobj.h>
#include <commctrl.h>
#include <dwmapi.h>
#include <windowsx.h>

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "dwmapi.lib")
#pragma comment(lib, "comdlg32.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(linker, \
  "\"/manifestdependency:type='win32' "\
  "name='Microsoft.Windows.Common-Controls' "\
  "version='6.0.0.0' processorArchitecture='*' "\
  "publicKeyToken='6595b64144ccf1df' language='*'\"")

enum {
    ID_VERSION_COMBO  = 1001,
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

static const COLORREF BG_COLOR      = RGB(30,  30,  36);
static const COLORREF BG_CONTROL    = RGB(50,  50,  60);
static const COLORREF TEXT_COLOR    = RGB(230, 230, 235);
static const COLORREF TEXT_DIM      = RGB(170, 170, 180);
static const COLORREF ACCENT_COLOR  = RGB(76,  175, 80);
static const COLORREF ACCENT_HOVER  = RGB(56,  142, 60);
static const COLORREF BORDER_COLOR  = RGB(70,  70,  85);

static HBRUSH  g_bgBrush      = nullptr;
static HBRUSH  g_ctrlBrush    = nullptr;
static HFONT   g_mainFont     = nullptr;
static HFONT   g_titleFont    = nullptr;
static HFONT   g_smallFont    = nullptr;
static HFONT   g_btnFont      = nullptr;
static UI*     g_ui           = nullptr;

static std::wstring to_w(const std::string& s) {
    if (s.empty()) return {};
    int sz = MultiByteToWideChar(CP_UTF8, 0, s.c_str(), -1, nullptr, 0);
    std::wstring w(sz - 1, L'\0');
    MultiByteToWideChar(CP_UTF8, 0, s.c_str(), -1, &w[0], sz);
    return w;
}

static std::string from_w(const std::wstring& w) {
    if (w.empty()) return {};
    int sz = WideCharToMultiByte(CP_UTF8, 0, w.c_str(), -1, nullptr, 0, nullptr, nullptr);
    std::string s(sz - 1, '\0');
    WideCharToMultiByte(CP_UTF8, 0, w.c_str(), -1, &s[0], sz, nullptr, nullptr);
    return s;
}

static std::string get_edit_text(HWND h) {
    int len = GetWindowTextLengthW(h);
    if (len <= 0) return {};
    std::wstring buf(len + 1, L'\0');
    GetWindowTextW(h, &buf[0], len + 1);
    buf.resize(len);
    return from_w(buf);
}

static HFONT make_font(int size, int weight, const wchar_t* face) {
    return CreateFontW(size, 0, 0, 0, weight, 0, 0, 0,
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
        CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_DONTCARE, face);
}

static void init_gdi_resources() {
    if (!g_bgBrush)   g_bgBrush   = CreateSolidBrush(BG_COLOR);
    if (!g_ctrlBrush) g_ctrlBrush = CreateSolidBrush(BG_CONTROL);
    if (!g_mainFont)  g_mainFont  = make_font(16, FW_NORMAL, L"Segoe UI");
    if (!g_titleFont) g_titleFont = make_font(28, FW_BOLD,   L"Segoe UI");
    if (!g_smallFont) g_smallFont = make_font(13, FW_NORMAL, L"Segoe UI");
    if (!g_btnFont)   g_btnFont   = make_font(22, FW_BOLD,   L"Segoe UI");
}

void UI::create_controls() {
    HWND h = (HWND)hwnd_;
    const int W = 720;

    // Title bar
    int y = 14;
    HWND hTitle = CreateWindowW(L"STATIC", L"OMNILAUNCHER",
        WS_CHILD | WS_VISIBLE | SS_CENTER,
        0, y, W, 38, h, nullptr, nullptr, nullptr);
    SendMessageW(hTitle, WM_SETFONT, (WPARAM)g_titleFont, TRUE);
    y += 50;

    // Subtitle
    HWND hSub = CreateWindowW(L"STATIC", L"Minecraft Launcher by OmniNodeCo",
        WS_CHILD | WS_VISIBLE | SS_CENTER,
        0, y, W, 18, h, nullptr, nullptr, nullptr);
    SendMessageW(hSub, WM_SETFONT, (WPARAM)g_smallFont, TRUE);
    y += 32;

    // Username row
    HWND hUL = CreateWindowW(L"STATIC", L"Username",
        WS_CHILD | WS_VISIBLE, 40, y + 4, 80, 20, h, nullptr, nullptr, nullptr);
    SendMessageW(hUL, WM_SETFONT, (WPARAM)g_mainFont, TRUE);

    username_edit_ = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
        WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL,
        130, y, 220, 28, h, (HMENU)ID_USERNAME_EDIT, nullptr, nullptr);
    SendMessageW((HWND)username_edit_, WM_SETFONT, (WPARAM)g_mainFont, TRUE);
    SendMessageW((HWND)username_edit_, EM_SETLIMITTEXT, 16, 0);

    offline_check_ = CreateWindowW(L"BUTTON", L"Offline Mode",
        WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
        370, y + 4, 130, 22, h, (HMENU)ID_OFFLINE_CHECK, nullptr, nullptr);
    SendMessageW((HWND)offline_check_, WM_SETFONT, (WPARAM)g_mainFont, TRUE);
    y += 42;

    // Version row
    HWND hVL = CreateWindowW(L"STATIC", L"Version",
        WS_CHILD | WS_VISIBLE, 40, y + 4, 80, 20, h, nullptr, nullptr, nullptr);
    SendMessageW(hVL, WM_SETFONT, (WPARAM)g_mainFont, TRUE);

    version_combo_ = CreateWindowExW(0, L"COMBOBOX", L"",
        WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST | WS_VSCROLL,
        130, y, 220, 320, h, (HMENU)ID_VERSION_COMBO, nullptr, nullptr);
    SendMessageW((HWND)version_combo_, WM_SETFONT, (WPARAM)g_mainFont, TRUE);

    snapshot_check_ = CreateWindowW(L"BUTTON", L"Snapshots",
        WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
        370, y + 4, 100, 22, h, (HMENU)ID_SNAPSHOT_CHECK, nullptr, nullptr);
    SendMessageW((HWND)snapshot_check_, WM_SETFONT, (WPARAM)g_mainFont, TRUE);

    HWND hRef = CreateWindowW(L"BUTTON", L"Refresh",
        WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
        480, y, 80, 28, h, (HMENU)ID_REFRESH_BTN, nullptr, nullptr);
    SendMessageW(hRef, WM_SETFONT, (WPARAM)g_mainFont, TRUE);
    y += 42;

    // RAM row
    HWND hRL = CreateWindowW(L"STATIC", L"RAM",
        WS_CHILD | WS_VISIBLE, 40, y + 6, 80, 20, h, nullptr, nullptr, nullptr);
    SendMessageW(hRL, WM_SETFONT, (WPARAM)g_mainFont, TRUE);

    ram_slider_ = CreateWindowW(TRACKBAR_CLASSW, L"",
        WS_CHILD | WS_VISIBLE | TBS_AUTOTICKS | TBS_HORZ,
        125, y, 280, 30, h, (HMENU)ID_RAM_SLIDER, nullptr, nullptr);
    SendMessageW((HWND)ram_slider_, TBM_SETRANGE, TRUE, MAKELPARAM(1, 16));
    SendMessageW((HWND)ram_slider_, TBM_SETPOS, TRUE, 2);
    SendMessageW((HWND)ram_slider_, TBM_SETTICFREQ, 1, 0);

    ram_label_ = CreateWindowW(L"STATIC", L"2 GB",
        WS_CHILD | WS_VISIBLE, 415, y + 6, 80, 20, h, (HMENU)ID_RAM_LABEL, nullptr, nullptr);
    SendMessageW((HWND)ram_label_, WM_SETFONT, (WPARAM)g_mainFont, TRUE);
    y += 44;

    // Java row
    HWND hJL = CreateWindowW(L"STATIC", L"Java",
        WS_CHILD | WS_VISIBLE, 40, y + 4, 80, 20, h, nullptr, nullptr, nullptr);
    SendMessageW(hJL, WM_SETFONT, (WPARAM)g_mainFont, TRUE);

    java_path_edit_ = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
        WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL,
        125, y, 510, 28, h, (HMENU)ID_JAVA_EDIT, nullptr, nullptr);
    SendMessageW((HWND)java_path_edit_, WM_SETFONT, (WPARAM)g_smallFont, TRUE);

    HWND hBrowse = CreateWindowW(L"BUTTON", L"Browse",
        WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
        642, y, 50, 28, h, (HMENU)ID_BROWSE_JAVA_BTN, nullptr, nullptr);
    SendMessageW(hBrowse, WM_SETFONT, (WPARAM)g_smallFont, TRUE);
    y += 40;

    // JVM args row
    HWND hJVL = CreateWindowW(L"STATIC", L"JVM Args",
        WS_CHILD | WS_VISIBLE, 40, y + 4, 80, 20, h, nullptr, nullptr, nullptr);
    SendMessageW(hJVL, WM_SETFONT, (WPARAM)g_mainFont, TRUE);

    jvm_args_edit_ = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
        WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL,
        125, y, 567, 28, h, (HMENU)ID_JVM_EDIT, nullptr, nullptr);
    SendMessageW((HWND)jvm_args_edit_, WM_SETFONT, (WPARAM)g_smallFont, TRUE);
    y += 46;

    // Progress bar
    progress_bar_ = CreateWindowW(PROGRESS_CLASSW, L"",
        WS_CHILD | WS_VISIBLE | PBS_SMOOTH,
        40, y, 652, 14, h, (HMENU)ID_PROGRESS, nullptr, nullptr);
    SendMessageW((HWND)progress_bar_, PBM_SETRANGE, 0, MAKELPARAM(0, 100));
    SendMessageW((HWND)progress_bar_, PBM_SETBARCOLOR, 0, (LPARAM)ACCENT_COLOR);
    SendMessageW((HWND)progress_bar_, PBM_SETBKCOLOR, 0, (LPARAM)BG_CONTROL);
    y += 22;

    // Status label
    status_label_ = CreateWindowW(L"STATIC",
        L"Ready - click Refresh to load versions",
        WS_CHILD | WS_VISIBLE | SS_CENTER,
        40, y, 652, 18, h, (HMENU)ID_STATUS, nullptr, nullptr);
    SendMessageW((HWND)status_label_, WM_SETFONT, (WPARAM)g_smallFont, TRUE);
    y += 30;

    // PLAY button
    play_button_ = CreateWindowW(L"BUTTON", L"PLAY",
        WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON | BS_OWNERDRAW,
        196, y, 340, 54, h, (HMENU)ID_PLAY_BTN, nullptr, nullptr);
    y += 66;

    // Open folder button
    HWND hFolder = CreateWindowW(L"BUTTON", L"Open Data Folder",
        WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
        40, y, 150, 26, h, (HMENU)ID_FOLDER_BTN, nullptr, nullptr);
    SendMessageW(hFolder, WM_SETFONT, (WPARAM)g_smallFont, TRUE);
}

void UI::load_config_to_ui() {
    auto& cfg = Config::instance();

    SetWindowTextW((HWND)username_edit_, to_w(cfg.username).c_str());
    SendMessageW((HWND)offline_check_, BM_SETCHECK,
        cfg.offline_mode ? BST_CHECKED : BST_UNCHECKED, 0);

    int gb = cfg.ram_mb / 1024;
    gb = (gb < 1) ? 2 : (gb > 16) ? 16 : gb;
    SendMessageW((HWND)ram_slider_, TBM_SETPOS, TRUE, gb);
    SetWindowTextW((HWND)ram_label_, to_w(std::to_string(gb) + " GB").c_str());

    SetWindowTextW((HWND)java_path_edit_, to_w(cfg.java_path).c_str());
    SetWindowTextW((HWND)jvm_args_edit_, to_w(cfg.jvm_args).c_str());
}

void UI::save_config_from_ui() {
    auto& cfg = Config::instance();

    cfg.username     = get_edit_text((HWND)username_edit_);
    cfg.offline_mode = (SendMessageW((HWND)offline_check_, BM_GETCHECK, 0, 0) == BST_CHECKED);

    int gb = (int)SendMessageW((HWND)ram_slider_, TBM_GETPOS, 0, 0);
    cfg.ram_mb = gb * 1024;

    cfg.java_path = get_edit_text((HWND)java_path_edit_);
    cfg.jvm_args  = get_edit_text((HWND)jvm_args_edit_);

    int sel = (int)SendMessageW((HWND)version_combo_, CB_GETCURSEL, 0, 0);
    if (sel >= 0 && sel < (int)versions_.size())
        cfg.selected_version = versions_[sel].id;

    cfg.save();
}

void UI::populate_versions() {
    SendMessageW((HWND)version_combo_, CB_RESETCONTENT, 0, 0);
    bool show_snap = (SendMessageW((HWND)snapshot_check_, BM_GETCHECK, 0, 0) == BST_CHECKED);
    versions_ = launcher_.get_versions(!show_snap);

    int sel_idx = -1;
    for (size_t i = 0; i < versions_.size(); i++) {
        std::string label = versions_[i].id;
        if (versions_[i].type != "release")
            label += "  [" + versions_[i].type + "]";
        SendMessageW((HWND)version_combo_, CB_ADDSTRING, 0,
            (LPARAM)to_w(label).c_str());
        if (versions_[i].id == Config::instance().selected_version)
            sel_idx = (int)i;
    }
    SendMessageW((HWND)version_combo_, CB_SETCURSEL,
        (sel_idx >= 0) ? sel_idx : 0, 0);
}

void UI::update_status(const std::string& text, int percent) {
    SetWindowTextW((HWND)status_label_, to_w(text).c_str());
    if (percent >= 0)
        SendMessageW((HWND)progress_bar_, PBM_SETPOS, (WPARAM)percent, 0);
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
        MessageBoxW((HWND)hwnd_, L"Please enter a username.",
            L"OmniLauncher", MB_OK | MB_ICONWARNING);
        return;
    }

    auto auth = Auth::offline(cfg.username);
    if (!auth.success) {
        MessageBoxW((HWND)hwnd_, to_w(auth.error).c_str(),
            L"Auth Error", MB_OK | MB_ICONERROR);
        return;
    }
    cfg.uuid         = auth.uuid;
    cfg.access_token = auth.access_token;
    cfg.save();

    int sel = (int)SendMessageW((HWND)version_combo_, CB_GETCURSEL, 0, 0);
    if (sel < 0 || sel >= (int)versions_.size()) {
        MessageBoxW((HWND)hwnd_, L"Please select a version.",
            L"OmniLauncher", MB_OK | MB_ICONWARNING);
        return;
    }

    std::string version_id = versions_[sel].id;
    loading_ = true;
    EnableWindow((HWND)play_button_, FALSE);

    std::thread([this, version_id]() {
        launcher_.download_version(version_id, [this](const LaunchProgress& p) {
            std::string* msg = new std::string(p.stage);
            PostMessageW((HWND)hwnd_, WM_USER + 2,
                (WPARAM)p.percent, (LPARAM)msg);
        });

        bool ok = launcher_.launch_game(version_id, [this](const LaunchProgress& p) {
            std::string* msg = new std::string(p.stage);
            PostMessageW((HWND)hwnd_, WM_USER + 2,
                (WPARAM)p.percent, (LPARAM)msg);
        });

        PostMessageW((HWND)hwnd_, WM_USER + 3, ok ? 1 : 0, 0);
    }).detach();
}

LRESULT CALLBACK UI::WndProc(void* hwnd, unsigned int msg,
                              unsigned long long wp, long long lp) {
    HWND h = (HWND)hwnd;

    switch (msg) {

    case WM_ERASEBKGND: {
        RECT rc;
        GetClientRect(h, &rc);
        FillRect((HDC)wp, &rc, g_bgBrush);
        return 1;
    }

    case WM_CTLCOLORSTATIC: {
        HDC hdc = (HDC)wp;
        SetTextColor(hdc, TEXT_COLOR);
        SetBkColor(hdc, BG_COLOR);
        SetBkMode(hdc, TRANSPARENT);
        return (LRESULT)g_bgBrush;
    }

    case WM_CTLCOLOREDIT: {
        HDC hdc = (HDC)wp;
        SetTextColor(hdc, TEXT_COLOR);
        SetBkColor(hdc, BG_CONTROL);
        return (LRESULT)g_ctrlBrush;
    }

    case WM_CTLCOLORBTN: {
        HDC hdc = (HDC)wp;
        SetTextColor(hdc, TEXT_COLOR);
        SetBkColor(hdc, BG_COLOR);
        return (LRESULT)g_bgBrush;
    }

    case WM_CTLCOLORLISTBOX: {
        HDC hdc = (HDC)wp;
        SetTextColor(hdc, TEXT_COLOR);
        SetBkColor(hdc, BG_CONTROL);
        return (LRESULT)g_ctrlBrush;
    }

    case WM_DRAWITEM: {
        auto* dis = (DRAWITEMSTRUCT*)lp;
        if (dis->CtlID == ID_PLAY_BTN) {
            bool pressed  = (dis->itemState & ODS_SELECTED) != 0;
            bool disabled = (dis->itemState & ODS_DISABLED) != 0;

            COLORREF col;
            if (disabled)     col = RGB(80, 90, 80);
            else if (pressed) col = ACCENT_HOVER;
            else              col = ACCENT_COLOR;

            // Fill background
            HBRUSH bgBr = CreateSolidBrush(BG_COLOR);
            FillRect(dis->hDC, &dis->rcItem, bgBr);
            DeleteObject(bgBr);

            // Rounded button
            HBRUSH br = CreateSolidBrush(col);
            HRGN rgn = CreateRoundRectRgn(
                dis->rcItem.left, dis->rcItem.top,
                dis->rcItem.right, dis->rcItem.bottom, 16, 16);
            FillRgn(dis->hDC, rgn, br);
            DeleteObject(rgn);
            DeleteObject(br);

            SetTextColor(dis->hDC, RGB(255, 255, 255));
            SetBkMode(dis->hDC, TRANSPARENT);
            HFONT oldFont = (HFONT)SelectObject(dis->hDC, g_btnFont);

            wchar_t text[64] = {};
            GetWindowTextW(dis->hwndItem, text, 64);
            DrawTextW(dis->hDC, text, -1, &dis->rcItem,
                      DT_CENTER | DT_VCENTER | DT_SINGLELINE);

            SelectObject(dis->hDC, oldFont);
            return TRUE;
        }
        break;
    }

    case WM_HSCROLL: {
        if (g_ui && (HWND)lp == (HWND)g_ui->ram_slider_) {
            int gb = (int)SendMessageW((HWND)g_ui->ram_slider_, TBM_GETPOS, 0, 0);
            SetWindowTextW((HWND)g_ui->ram_label_,
                to_w(std::to_string(gb) + " GB").c_str());
        }
        break;
    }

    case WM_COMMAND: {
        int id = LOWORD(wp);
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
            wchar_t file[MAX_PATH] = {};
            OPENFILENAMEW ofn = {};
            ofn.lStructSize = sizeof(ofn);
            ofn.hwndOwner   = h;
            ofn.lpstrFilter =
                L"Java Executable\0javaw.exe;java.exe\0All Files\0*.*\0";
            ofn.lpstrFile   = file;
            ofn.nMaxFile    = MAX_PATH;
            ofn.Flags       = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST;
            ofn.lpstrTitle  = L"Select Java Executable";
            if (GetOpenFileNameW(&ofn))
                SetWindowTextW((HWND)g_ui->java_path_edit_, file);
            break;
        }

        case ID_FOLDER_BTN: {
            std::wstring dir = Config::instance().base_dir().wstring();
            ShellExecuteW(nullptr, L"open", dir.c_str(),
                          nullptr, nullptr, SW_SHOWNORMAL);
            break;
        }
        }
        break;
    }

    case WM_USER + 1: {
        g_ui->loading_ = false;
        EnableWindow((HWND)g_ui->play_button_, TRUE);
        if (wp) {
            g_ui->populate_versions();
            g_ui->update_status(
                "Versions loaded - " +
                std::to_string(g_ui->versions_.size()) + " available", 0);
        } else {
            g_ui->update_status(
                "Failed to fetch versions: " + g_ui->launcher_.last_error(), 0);
        }
        break;
    }

    case WM_USER + 2: {
        std::string* msg = reinterpret_cast<std::string*>(lp);
        if (msg) {
            g_ui->update_status(*msg, (int)wp);
            delete msg;
        }
        break;
    }

    case WM_USER + 3: {
        g_ui->loading_ = false;
        EnableWindow((HWND)g_ui->play_button_, TRUE);
        if (!wp) {
            std::string err = "Launch failed: " + g_ui->launcher_.last_error();
            g_ui->update_status(err, 0);
            MessageBoxW(h, to_w(err).c_str(), L"Error", MB_OK | MB_ICONERROR);
        } else {
            g_ui->update_status("Game launched!", 100);
        }
        break;
    }

    case WM_GETMINMAXINFO: {
        auto* mmi = (MINMAXINFO*)lp;
        mmi->ptMinTrackSize = {740, 560};
        mmi->ptMaxTrackSize = {740, 560};
        break;
    }

    case WM_DESTROY:
        if (g_ui) g_ui->save_config_from_ui();
        PostQuitMessage(0);
        return 0;
    }

    return DefWindowProcW(h, msg, wp, lp);
}

int UI::run() {
    g_ui = this;
    init_gdi_resources();

    INITCOMMONCONTROLSEX icc = {
        sizeof(icc),
        ICC_STANDARD_CLASSES | ICC_PROGRESS_CLASS | ICC_BAR_CLASSES
    };
    InitCommonControlsEx(&icc);

    WNDCLASSEXW wc   = {};
    wc.cbSize        = sizeof(wc);
    wc.lpfnWndProc   = (WNDPROC)WndProc;
    wc.hInstance     = GetModuleHandleW(nullptr);
    wc.lpszClassName = L"OmniLauncherWnd";
    wc.hCursor       = LoadCursorW(nullptr, IDC_ARROW);
    wc.hIcon         = LoadIconW(wc.hInstance, MAKEINTRESOURCEW(101));
    wc.hIconSm       = wc.hIcon;
    wc.hbrBackground = g_bgBrush;
    RegisterClassExW(&wc);

    RECT desk = {};
    SystemParametersInfoW(SPI_GETWORKAREA, 0, &desk, 0);
    int wx = (desk.right  - 740) / 2;
    int wy = (desk.bottom - 560) / 2;

    hwnd_ = CreateWindowExW(
        0,
        L"OmniLauncherWnd",
        L"OmniLauncher - Minecraft Launcher",
        WS_OVERLAPPEDWINDOW & ~WS_MAXIMIZEBOX & ~WS_THICKFRAME,
        wx, wy, 740, 560,
        nullptr, nullptr, wc.hInstance, nullptr);

    // Enable immersive dark mode (Windows 10 1809+)
    BOOL dark = TRUE;
    DwmSetWindowAttribute((HWND)hwnd_, 20, &dark, sizeof(dark));
    // Fallback attribute for older Win10 builds
    DwmSetWindowAttribute((HWND)hwnd_, 19, &dark, sizeof(dark));

    create_controls();
    load_config_to_ui();

    ShowWindow((HWND)hwnd_, SW_SHOW);
    UpdateWindow((HWND)hwnd_);

    on_refresh();

    MSG msg = {};
    while (GetMessageW(&msg, nullptr, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    return (int)msg.wParam;
}

#else

#include <gtk/gtk.h>

static GtkWidget* g_window       = nullptr;
static GtkWidget* g_username_e   = nullptr;
static GtkWidget* g_version_cb   = nullptr;
static GtkWidget* g_progress     = nullptr;
static GtkWidget* g_status_lbl   = nullptr;
static GtkWidget* g_ram_scale    = nullptr;
static GtkWidget* g_java_e       = nullptr;
static GtkWidget* g_jvm_e        = nullptr;
static GtkWidget* g_snapshot_chk = nullptr;

static Launcher  g_launcher;
static std::vector<VersionInfo> g_versions;
static bool      g_loading = false;

static void gtk_populate_versions() {
    gtk_combo_box_text_remove_all(GTK_COMBO_BOX_TEXT(g_version_cb));
    bool snap = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(g_snapshot_chk));
    g_versions = g_launcher.get_versions(!snap);

    int sel = -1;
    for (size_t i = 0; i < g_versions.size(); i++) {
        std::string label = g_versions[i].id;
        if (g_versions[i].type != "release")
            label += "  [" + g_versions[i].type + "]";
        gtk_combo_box_text_append_text(GTK_COMBO_BOX_TEXT(g_version_cb), label.c_str());
        if (g_versions[i].id == Config::instance().selected_version)
            sel = (int)i;
    }
    gtk_combo_box_set_active(GTK_COMBO_BOX(g_version_cb),
        (sel >= 0) ? sel : 0);
}

static gboolean cb_refresh_done(gpointer data) {
    g_loading = false;
    if (GPOINTER_TO_INT(data)) {
        gtk_populate_versions();
        gtk_label_set_text(GTK_LABEL(g_status_lbl), "Versions loaded");
    } else {
        gtk_label_set_text(GTK_LABEL(g_status_lbl), "Failed to fetch versions");
    }
    return FALSE;
}

static void on_refresh(GtkWidget*, gpointer) {
    if (g_loading) return;
    g_loading = true;
    gtk_label_set_text(GTK_LABEL(g_status_lbl), "Fetching versions...");
    std::thread([]() {
        bool ok = g_launcher.fetch_version_manifest();
        g_idle_add(cb_refresh_done, GINT_TO_POINTER(ok ? 1 : 0));
    }).detach();
}

static gboolean cb_launch_done(gpointer data) {
    g_loading = false;
    if (!GPOINTER_TO_INT(data))
        gtk_label_set_text(GTK_LABEL(g_status_lbl),
            ("Failed: " + g_launcher.last_error()).c_str());
    else
        gtk_label_set_text(GTK_LABEL(g_status_lbl), "Game launched!");
    return FALSE;
}

static void on_play(GtkWidget*, gpointer) {
    if (g_loading) return;

    std::string username = gtk_entry_get_text(GTK_ENTRY(g_username_e));
    auto auth = Auth::offline(username);
    if (!auth.success) {
        gtk_label_set_text(GTK_LABEL(g_status_lbl), auth.error.c_str());
        return;
    }

    auto& cfg        = Config::instance();
    cfg.username     = username;
    cfg.uuid         = auth.uuid;
    cfg.access_token = auth.access_token;
    cfg.ram_mb       = (int)gtk_range_get_value(GTK_RANGE(g_ram_scale)) * 1024;
    cfg.java_path    = gtk_entry_get_text(GTK_ENTRY(g_java_e));
    cfg.jvm_args     = gtk_entry_get_text(GTK_ENTRY(g_jvm_e));

    int sel = gtk_combo_box_get_active(GTK_COMBO_BOX(g_version_cb));
    if (sel < 0 || sel >= (int)g_versions.size()) return;
    std::string vid = g_versions[sel].id;
    cfg.selected_version = vid;
    cfg.save();

    g_loading = true;
    gtk_label_set_text(GTK_LABEL(g_status_lbl), "Downloading...");

    std::thread([vid]() {
        g_launcher.download_version(vid);
        bool ok = g_launcher.launch_game(vid);
        g_idle_add(cb_launch_done, GINT_TO_POINTER(ok ? 1 : 0));
    }).detach();
}

int UI::run() {
    gtk_init(nullptr, nullptr);

    GtkCssProvider* css = gtk_css_provider_new();
    gtk_css_provider_load_from_data(css,
        "window,box{background-color:#1e1e24}"
        "label{color:#e6e6eb;font-size:12pt}"
        "entry{background:#32323c;color:#e6e6eb;border:1px solid #46465a;"
            "border-radius:4px;padding:6px}"
        "combobox button{background:#32323c;color:#e6e6eb;border-radius:4px}"
        "button{background:#4CAF50;color:#fff;border-radius:6px;"
            "padding:8px 16px;font-weight:bold}"
        "button:hover{background:#388E3C}"
        "progressbar trough{background:#32323c;border-radius:4px;min-height:8px}"
        "progressbar progress{background:#4CAF50;border-radius:4px}"
        ".title{font-size:22pt;font-weight:bold;color:#fff}"
        ".subtitle{font-size:10pt;color:#aaaab4}",
        -1, nullptr);
    gtk_style_context_add_provider_for_screen(
        gdk_screen_get_default(),
        GTK_STYLE_PROVIDER(css),
        GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

    g_window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(g_window), "OmniLauncher - Minecraft Launcher");
    gtk_window_set_default_size(GTK_WINDOW(g_window), 720, 540);
    gtk_window_set_resizable(GTK_WINDOW(g_window), FALSE);
    g_signal_connect(g_window, "destroy", G_CALLBACK(gtk_main_quit), nullptr);

    GtkWidget* vbox = gtk_box_new(GTK_ORIENTATION_VERTICAL, 10);
    gtk_container_set_border_width(GTK_CONTAINER(vbox), 24);
    gtk_container_add(GTK_CONTAINER(g_window), vbox);

    GtkWidget* title = gtk_label_new("OMNILAUNCHER");
    gtk_style_context_add_class(gtk_widget_get_style_context(title), "title");
    gtk_box_pack_start(GTK_BOX(vbox), title, FALSE, FALSE, 2);

    GtkWidget* subtitle = gtk_label_new("Minecraft Launcher by OmniNodeCo");
    gtk_style_context_add_class(gtk_widget_get_style_context(subtitle), "subtitle");
    gtk_box_pack_start(GTK_BOX(vbox), subtitle, FALSE, FALSE, 0);

    GtkWidget* ur = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
    gtk_box_pack_start(GTK_BOX(ur), gtk_label_new("Username"), FALSE, FALSE, 0);
    g_username_e = gtk_entry_new();
    gtk_entry_set_max_length(GTK_ENTRY(g_username_e), 16);
    gtk_entry_set_text(GTK_ENTRY(g_username_e), Config::instance().username.c_str());
    gtk_box_pack_start(GTK_BOX(ur), g_username_e, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), ur, FALSE, FALSE, 4);

    GtkWidget* vr = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
    gtk_box_pack_start(GTK_BOX(vr), gtk_label_new("Version"), FALSE, FALSE, 0);
    g_version_cb = gtk_combo_box_text_new();
    gtk_box_pack_start(GTK_BOX(vr), g_version_cb, TRUE, TRUE, 0);
    g_snapshot_chk = gtk_check_button_new_with_label("Snapshots");
    g_signal_connect(g_snapshot_chk, "toggled",
        G_CALLBACK(+[](GtkWidget*, gpointer) { gtk_populate_versions(); }), nullptr);
    gtk_box_pack_start(GTK_BOX(vr), g_snapshot_chk, FALSE, FALSE, 0);
    GtkWidget* ref_btn = gtk_button_new_with_label("Refresh");
    g_signal_connect(ref_btn, "clicked", G_CALLBACK(on_refresh), nullptr);
    gtk_box_pack_start(GTK_BOX(vr), ref_btn, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), vr, FALSE, FALSE, 4);

    GtkWidget* rr = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
    gtk_box_pack_start(GTK_BOX(rr), gtk_label_new("RAM (GB)"), FALSE, FALSE, 0);
    g_ram_scale = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 1, 16, 1);
    gtk_range_set_value(GTK_RANGE(g_ram_scale), Config::instance().ram_mb / 1024);
    gtk_box_pack_start(GTK_BOX(rr), g_ram_scale, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), rr, FALSE, FALSE, 4);

    GtkWidget* jr = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
    gtk_box_pack_start(GTK_BOX(jr), gtk_label_new("Java"), FALSE, FALSE, 0);
    g_java_e = gtk_entry_new();
    gtk_entry_set_text(GTK_ENTRY(g_java_e), Config::instance().java_path.c_str());
    gtk_entry_set_placeholder_text(GTK_ENTRY(g_java_e), "Auto-detect");
    gtk_box_pack_start(GTK_BOX(jr), g_java_e, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), jr, FALSE, FALSE, 4);

    GtkWidget* jvr = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
    gtk_box_pack_start(GTK_BOX(jvr), gtk_label_new("JVM Args"), FALSE, FALSE, 0);
    g_jvm_e = gtk_entry_new();
    gtk_entry_set_text(GTK_ENTRY(g_jvm_e), Config::instance().jvm_args.c_str());
    gtk_box_pack_start(GTK_BOX(jvr), g_jvm_e, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), jvr, FALSE, FALSE, 4);

    g_progress = gtk_progress_bar_new();
    gtk_box_pack_start(GTK_BOX(vbox), g_progress, FALSE, FALSE, 6);

    g_status_lbl = gtk_label_new("Ready - click Refresh to load versions");
    gtk_box_pack_start(GTK_BOX(vbox), g_status_lbl, FALSE, FALSE, 0);

    GtkWidget* play = gtk_button_new_with_label("PLAY");
    g_signal_connect(play, "clicked", G_CALLBACK(on_play), nullptr);
    gtk_box_pack_start(GTK_BOX(vbox), play, FALSE, FALSE, 10);

    gtk_widget_show_all(g_window);
    on_refresh(nullptr, nullptr);
    gtk_main();
    return 0;
}

#endif