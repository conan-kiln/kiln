cmake_minimum_required(VERSION 3.5)
project(KnitroC++ CXX)

set(CMAKE_CXX_STANDARD 11 CACHE STRING "")
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS TRUE)
set(CMAKE_POSITION_INDEPENDENT_CODE TRUE)

find_package(OpenMP REQUIRED)
link_libraries(OpenMP::OpenMP_CXX)

include_directories(include)
include_directories(../../include)
link_directories(../../lib)

file(GLOB INTERFACE_SOURCES src/*.cpp)
add_library(knitrocpp ${INTERFACE_SOURCES})
set_target_properties(knitrocpp PROPERTIES
    VERSION ${VERSION}
    SOVERSION ${SOVERSION}
)

if(WIN32)
  target_link_libraries(knitrocpp knitro${KN_RELEASE})
  if(MSVC)
    target_compile_options(knitrocpp PRIVATE /EHsc /Zc:__cplusplus)
  endif()
elseif(APPLE)
  if(BUILD_SHARED_LIBS)
    target_link_libraries(knitrocpp libknitro.dylib)
  else()
    target_link_libraries(knitrocpp libknitro.a c++ iomp5)
  endif()
else()
  if(BUILD_SHARED_LIBS)
    target_link_libraries(knitrocpp libknitro.so)
  else()
    target_link_libraries(knitrocpp libknitro.a pthread m dl rt iomp5 stdc++ gcc_s)
  endif()
endif()
target_link_libraries(knitrocpp ${CMAKE_DL_LIBS})

install(TARGETS knitrocpp
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)
install(DIRECTORY include/ DESTINATION include)
