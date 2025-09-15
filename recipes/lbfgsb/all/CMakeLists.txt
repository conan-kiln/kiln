cmake_minimum_required(VERSION 3.15)
project(lbfgsb Fortran)

add_library(lbfgsb
    lbfgsb.f
    timer.f
    blas.f
    linpack.f
)

install(TARGETS lbfgsb ARCHIVE DESTINATION lib LIBRARY DESTINATION lib RUNTIME DESTINATION bin)
