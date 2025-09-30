cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CUDA CXX)

find_package(moderngpu REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cu)
target_link_libraries(${PROJECT_NAME} PRIVATE moderngpu::moderngpu)
set_target_properties(${PROJECT_NAME} PROPERTIES LINKER_LANGUAGE CXX)
