cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(nanoeigenpy REQUIRED CONFIG)

nanobind_add_module(test_package NB_STATIC test_package.cpp)
target_link_libraries(test_package PRIVATE nanoeigenpy::nanoeigenpy_headers)
