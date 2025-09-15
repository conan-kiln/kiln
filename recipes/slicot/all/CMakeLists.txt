cmake_minimum_required(VERSION 3.16)
project(slicot LANGUAGES Fortran)

find_package(BLAS REQUIRED)
find_package(LAPACK REQUIRED)

file(GLOB SLICOT_SOURCES "src/*.f")
add_library(slicot ${SLICOT_SOURCES})
target_link_libraries(slicot PUBLIC lpkaux ${LAPACK_LIBRARIES} ${BLAS_LIBRARIES})
set_target_properties(slicot PROPERTIES
    VERSION ${SLICOT_VERSION}
    SOVERSION ${SLICOT_VERSION_MAJOR}
)

file(GLOB LPKAUX_SOURCES "src_aux/*.f")
add_library(lpkaux ${LPKAUX_SOURCES})
target_link_libraries(lpkaux PUBLIC ${LAPACK_LIBRARIES} ${BLAS_LIBRARIES})
set_target_properties(lpkaux PROPERTIES
    VERSION ${SLICOT_VERSION}
    SOVERSION ${SLICOT_VERSION_MAJOR}
)

include(GNUInstallDirs)
install(TARGETS slicot lpkaux
    EXPORT SLICOTTargets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
