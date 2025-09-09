cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX CUDA)

find_package(cuvs REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cu)
target_link_libraries(${PROJECT_NAME} PRIVATE cuvs::cuvs)
