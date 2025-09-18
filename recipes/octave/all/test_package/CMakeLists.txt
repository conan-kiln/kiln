cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(PkgConfig REQUIRED)
pkg_check_modules(OCTAVE REQUIRED IMPORTED_TARGET octave)

add_library(hello MODULE hello.cpp)
target_link_libraries(hello PRIVATE PkgConfig::OCTAVE)
set_target_properties(hello PROPERTIES
  PREFIX ""
  SUFFIX ".oct"
)
