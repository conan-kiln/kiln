cmake_minimum_required(VERSION 3.15)
project(mikktspace LANGUAGES C)

add_library(mikktspace mikktspace.c)
set_target_properties(mikktspace PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS ON)

include(CheckFunctionExists)
check_function_exists(pow HAVE_MATH_SYSTEM)
if(NOT HAVE_MATH_SYSTEM)
    target_link_libraries(mikktspace PRIVATE m)
endif()

install(TARGETS mikktspace
    RUNTIME DESTINATION bin
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)
install(FILES mikktspace.h DESTINATION include)
