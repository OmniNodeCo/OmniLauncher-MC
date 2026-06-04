#pragma once
#include <string>
#include <vector>
#include "launcher.h"

class UI {
public:
    int run();

private:
#ifdef _WIN32
    void* hwnd_ = nullptr;
    void* version_combo_ = nullptr;
    void* username_edit_ = nullptr;
    void* play_button_ = nullptr;
    void* progress_bar_ = nullptr;
    void* status_label_ = nullptr;
    void* ram_slider_ = nullptr;
    void* ram_label_ = nullptr;
    void* tab_control_ = nullptr;
    void* offline_check_ = nullptr;
    void* java_path_edit_ = nullptr;
    void* jvm_args_edit_ = nullptr;
    void* snapshot_check_ = nullptr;

    Launcher launcher_;
    std::vector<VersionInfo> versions_;
    bool loading_ = false;

    static long long __stdcall WndProc(void* hwnd, unsigned int msg, unsigned long long wp, long long lp);
    void create_controls();
    void on_play();
    void on_refresh();
    void update_status(const std::string& text, int percent = -1);
    void populate_versions();
    void load_config_to_ui();
    void save_config_from_ui();
#endif
};