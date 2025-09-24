cmake_minimum_required(VERSION 3.18)
project(test_package LANGUAGES CUDA CXX)

find_package(GPUTreeShap REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cu)
target_link_libraries(${PROJECT_NAME} PRIVATE GPUTreeShap::GPUTreeShap)
set_target_properties(${PROJECT_NAME} PROPERTIES LINKER_LANGUAGE CXX)
