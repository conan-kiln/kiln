find_package(RapidJSON REQUIRED)
find_package(tclap REQUIRED)
link_libraries(
    rapidjson
    tclap::tclap
)
if(ENABLE_DARTS)
    find_package(darts REQUIRED)
    link_libraries(darts::darts)
endif()
