cmake_minimum_required(VERSION 3.15)
project(tinyfiledialogs C)

set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS TRUE)

add_library(tinyfiledialogs tinyfiledialogs.c)

install(TARGETS tinyfiledialogs ARCHIVE DESTINATION lib LIBRARY DESTINATION lib RUNTIME DESTINATION bin)
install(FILES tinyfiledialogs.h DESTINATION include/tinyfiledialogs)
