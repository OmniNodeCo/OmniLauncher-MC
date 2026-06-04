cmake_minimum_required(VERSION 3.20)
project(OmniLauncher VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(WIN32)
    set(CMAKE_WIN32_EXECUTABLE ON)
endif()

set(SOURCES
    src/main.cpp
    src/launcher.cpp
    src/http_client.cpp
    src/auth.cpp
    src/ui.cpp
    src/config.cpp
)

if(WIN32)
    list(APPEND SOURCES src/resource.rc)
endif()

add_executable(OmniLauncher ${SOURCES})

if(WIN32)
    target_link_libraries(OmniLauncher PRIVATE
        winhttp
        comctl32
        gdi32
        user32
        shell32
        ole32
        comdlg32
        advapi32
        shlwapi
        dwmapi
        uxtheme
    )
    target_compile_definitions(OmniLauncher PRIVATE
        UNICODE
        _UNICODE
        WIN32_LEAN_AND_MEAN
        NOMINMAX
    )
    target_compile_options(OmniLauncher PRIVATE /wd4005)
elseif(UNIX AND NOT APPLE)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(GTK3  REQUIRED gtk+-3.0)
    pkg_check_modules(CURL  REQUIRED libcurl)
    target_include_directories(OmniLauncher PRIVATE
        ${GTK3_INCLUDE_DIRS}
        ${CURL_INCLUDE_DIRS}
    )
    target_link_libraries(OmniLauncher PRIVATE
        ${GTK3_LIBRARIES}
        ${CURL_LIBRARIES}
        pthread
    )
    target_compile_options(OmniLauncher PRIVATE ${GTK3_CFLAGS_OTHER})
endif()

install(TARGETS OmniLauncher DESTINATION bin)