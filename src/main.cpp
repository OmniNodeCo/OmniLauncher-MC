#include "config.h"
#include "ui.h"

#ifdef _WIN32
#include <windows.h>
int WINAPI wWinMain(HINSTANCE, HINSTANCE, LPWSTR, int) {
#else
int main(int argc, char* argv[]) {
#endif
    Config::instance().init();
    
    UI ui;
    return ui.run();
}