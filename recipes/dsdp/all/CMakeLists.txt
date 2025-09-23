cmake_minimum_required(VERSION 3.15)
project(DSDP LANGUAGES C)

set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS TRUE)

set(DSDPTIMER "NONE" CACHE STRING "Add timing support: NONE, DSDP_TIME, or DSDP_MS_TIME")
set_property(CACHE DSDPTIMER PROPERTY STRINGS NONE DSDP_TIME DSDP_MS_TIME)

if(DSDPTIMER STREQUAL "DSDP_TIME")
  add_compile_definitions(DSDP_TIME)
elseif(DSDPTIMER STREQUAL "DSDP_MS_TIME")
  add_compile_definitions(DSDP_MS_TIME)
endif()

file(GLOB_RECURSE DSDP_SOURCES CONFIGURE_DEPENDS "src/*.c")
add_library(dsdp ${DSDP_SOURCES})
target_include_directories(dsdp PUBLIC
    include
    src/solver
    src/sdp
)

find_package(LAPACK REQUIRED)
target_link_libraries(dsdp PUBLIC LAPACK::LAPACK)

include(GNUInstallDirs)
install(TARGETS dsdp
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
