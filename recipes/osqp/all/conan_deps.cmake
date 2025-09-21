find_package(qdldl REQUIRED)
find_package(AMD REQUIRED)
link_libraries(qdldl::qdldl SuiteSparse::AMD)
