cmake_minimum_required(VERSION 3.15)
project(easyexif)

set(CMAKE_CXX_STANDARD_REQUIRED True)
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)

add_library(easyexif exif.cpp)
target_include_directories(easyexif PUBLIC exif.h)
set_target_properties(easyexif PROPERTIES PUBLIC_HEADER exif.h)

include(GNUInstallDirs)
install(TARGETS easyexif
    PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/easyexif
)
