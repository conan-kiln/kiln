cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(skarupke-flat-hash-map REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE skarupke-flat-hash-map::skarupke-flat-hash-map)
