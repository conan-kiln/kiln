cmake_minimum_required(VERSION 3.15)
project(test_package)

find_package(BLAS CONFIG REQUIRED)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} BLAS::BLAS)

message(STATUS "CONAN_BLA_VENDOR: ${CONAN_BLA_VENDOR}")

if(NOT CONAN_BLA_VENDOR MATCHES "^(FLAME|Intel10)$")
    target_compile_definitions(${PROJECT_NAME} PRIVATE HAVE_F77BLAS)
endif()
