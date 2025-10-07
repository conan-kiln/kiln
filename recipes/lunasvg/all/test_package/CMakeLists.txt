cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(lunasvg REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE lunasvg::lunasvg)

if (lunasvg_VERSION VERSION_LESS "3.0.0")
    target_compile_definitions(${PROJECT_NAME} PRIVATE LUNASVG_BEFORE_3_0_0)
endif()
