find_package(cuda-profiler-api REQUIRED)
find_package(argparse REQUIRED)
link_libraries(cuda-profiler-api::cuda-profiler-api argparse::argparse)
