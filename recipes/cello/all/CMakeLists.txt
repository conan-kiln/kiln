# A rewrite of https://github.com/orangeduck/Cello/blob/master/Makefile
cmake_minimum_required(VERSION 3.15)
project(Cello VERSION 2.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 99 CACHE STRING "")
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON)  # GNU99

file(GLOB_RECURSE CELLO_SOURCES "src/*.c")
add_library(Cello ${CELLO_SOURCES})

target_include_directories(Cello PUBLIC include)

if(NOT CMAKE_BUILD_TYPE STREQUAL Debug)
    target_compile_definitions(Cello PRIVATE CELLO_NDEBUG CELLO_NSTRACE)
endif()

find_package(Threads REQUIRED)
target_link_libraries(Cello PUBLIC Threads::Threads)

include(CheckLibraryExists)
check_library_exists(m pow "" LIBM)
target_link_libraries(Cello PUBLIC $<$<BOOL:${LIBM}>:m>)

if(CMAKE_SYSTEM_NAME STREQUAL "FreeBSD")
    find_library(EXECINFO_LIB execinfo)
    if(EXECINFO_LIB AND CMAKE_BUILD_TYPE STREQUAL Debug)
        target_link_libraries(Cello PRIVATE ${EXECINFO_LIB})
    else()
        target_compile_definitions(Cello PRIVATE CELLO_NSTRACE)
    endif()
elseif(WIN32)
    if(CMAKE_BUILD_TYPE STREQUAL Debug)
        target_link_libraries(Cello PRIVATE DbgHelp)
    endif()
endif()

include(GNUInstallDirs)
install(TARGETS Cello
    EXPORT CelloTargets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
install(FILES include/Cello.h
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)
