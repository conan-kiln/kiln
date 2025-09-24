cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C CXX)

find_package(foxglove-sdk-c REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE foxglove-sdk-c::foxglove-sdk-c)
