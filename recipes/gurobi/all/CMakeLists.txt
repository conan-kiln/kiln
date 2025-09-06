cmake_minimum_required(VERSION 3.15)
project(gurobi_c++ CXX)

set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)

file(GLOB GUROBI_CXX_SRC src/cpp/*.cpp)
add_library(gurobi_c++ ${GUROBI_CXX_SRC})
target_include_directories(gurobi_c++ PRIVATE include)
target_link_libraries(gurobi_c++ PRIVATE ${C_LIB})
target_link_directories(gurobi_c++ PRIVATE lib)

install(TARGETS gurobi_c++
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)
install(FILES include/gurobi_c++.h DESTINATION include)
