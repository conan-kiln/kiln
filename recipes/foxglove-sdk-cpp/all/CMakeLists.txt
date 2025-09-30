cmake_minimum_required(VERSION 3.15)
project(foxglove-sdk CXX)

find_package(foxglove-sdk-c REQUIRED)
find_package(websocketpp REQUIRED)
find_package(asio REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(tl-expected REQUIRED)

file(GLOB_RECURSE foxglove_cpp_srcs "foxglove/src/*.cpp" )
add_library(foxglove_cpp "${foxglove_cpp_srcs}")
target_include_directories(foxglove_cpp PUBLIC foxglove/include)

target_link_libraries(foxglove_cpp PUBLIC
  foxglove-sdk-c::foxglove-sdk-c
  websocketpp::websocketpp
  asio::asio
  nlohmann_json::nlohmann_json
  tl::expected
)

install(TARGETS foxglove_cpp
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)
install(DIRECTORY foxglove/include/ DESTINATION include)
