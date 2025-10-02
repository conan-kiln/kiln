cmake_minimum_required(VERSION 3.15)
project(getopt C)

set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS TRUE)

include_directories(
    src/misc
    src/internal
    src/
)

add_library(getopt
    src/misc/getopt.c
    src/misc/getopt_long.c
)

install(TARGETS getopt LIBRARY DESTINATION lib ARCHIVE DESTINATION lib RUNTIME DESTINATION bin)
install(FILES include/getopt.h DESTINATION include/getopt)
