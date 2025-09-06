# Replacement for https://github.com/nwh/lusol/blob/master/makefile
cmake_minimum_required(VERSION 3.15)
project(LUSOL LANGUAGES C Fortran)

set(CMAKE_C_STANDARD 99 CACHE STRING "C standard to conform to")
set(CMAKE_POSITION_INDEPENDENT_CODE ON CACHE BOOL "Build position independent code")
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS TRUE)

add_library(clusol
    src/lusol_util.f
    src/lusol6b.f
    src/lusol7b.f
    src/lusol8b.f
    src/lusol_precision.f90
    src/lusol.f90
    src/clusol.c
    src/clusol.h
)

include(GNUInstallDirs)
install(TARGETS clusol
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
install(FILES src/clusol.h DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
