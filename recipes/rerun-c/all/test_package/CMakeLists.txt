cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C CXX)

find_package(rerun_c REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE rerun_c)
