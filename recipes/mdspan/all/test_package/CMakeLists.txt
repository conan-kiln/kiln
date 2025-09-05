cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(mdspan REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE std::mdspan)

if(mdspan_VERSION VERSION_GREATER_EQUAL "0.7.0")
  target_compile_definitions(${PROJECT_NAME} PRIVATE "MDSPAN_STD")
endif()

if(MSVC)
  target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_20)
  target_compile_definitions(${PROJECT_NAME} PRIVATE "MDSPAN_CXX_STANDARD=20")
elseif(mdspan_VERSION VERSION_GREATER_EQUAL "0.6.0")
  target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_17)
  target_compile_definitions(${PROJECT_NAME} PRIVATE "MDSPAN_CXX_STANDARD=17")
else()
  target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_14)
  target_compile_definitions(${PROJECT_NAME} PRIVATE "MDSPAN_CXX_STANDARD=14")
endif()
