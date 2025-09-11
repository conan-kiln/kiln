cmake_minimum_required(VERSION 3.15)
project(conoptcpp CXX)

include_directories(include src/cpp)
link_directories(lib)

file(GLOB CXX_SOURCES src/cpp/*.cpp)
add_library(conoptcpp SHARED ${CXX_SOURCES})
set_target_properties(conoptcpp PROPERTIES
    VERSION ${VERSION}
    SOVERSION ${SOVERSION}
)
if(WIN32)
    set_target_properties(conoptcpp PROPERTIES OUTPUT_NAME conoptcpp${SOVERSION})
endif()
target_link_libraries(conoptcpp PRIVATE conopt)

include(GNUInstallDirs)
install(TARGETS conoptcpp
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
install(DIRECTORY include/
        DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
        FILES_MATCHING PATTERN *.hpp)
