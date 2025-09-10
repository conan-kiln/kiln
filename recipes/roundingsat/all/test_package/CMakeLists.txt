cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(roundingsat REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE roundingsat::roundingsat)
if(RS_OLD_API)
    target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_17)
else()
    target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_20)
endif()
