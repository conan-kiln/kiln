cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(ignition-math6 REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} ignition-math6::ignition-math6)
