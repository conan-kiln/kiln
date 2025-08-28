cmake_minimum_required(VERSION 3.15)
project(smolv LANGUAGES CXX)

add_library(smolv src/source/smolv.cpp)

install(TARGETS smolv
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)
install(FILES src/source/smolv.h DESTINATION include)
