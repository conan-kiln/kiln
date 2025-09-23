cmake_minimum_required(VERSION 3.18)
project(test_package LANGUAGES CUDA)

find_package(tiny-cuda-nn REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cu)
target_link_libraries(${PROJECT_NAME} PRIVATE tiny-cuda-nn::tiny-cuda-nn)
