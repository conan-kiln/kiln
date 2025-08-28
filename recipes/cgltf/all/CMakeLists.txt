cmake_minimum_required(VERSION 3.15)
project(cgltf C)

add_library(cgltf cgltf.c cgltf_write.c)
set_property(TARGET cgltf PROPERTY C_STANDARD 99)
set_property(TARGET cgltf PROPERTY WINDOWS_EXPORT_ALL_SYMBOLS ON)

install(TARGETS cgltf
    RUNTIME DESTINATION bin
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)
install(FILES cgltf.h cgltf_write.h DESTINATION include)
