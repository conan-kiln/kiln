find_package(Eigen3 REQUIRED)
find_package(OpenCV REQUIRED)
find_package(TBB REQUIRED)
find_package(fmt REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(Pangolin REQUIRED)
find_package(opengv REQUIRED)
find_package(magic_enum REQUIRED)

if(BASALT_BUILD_TOOLS)
  find_package(CLI11 REQUIRED)
endif()

set(BASALT_PANGO_TARGETS Pangolin::Pangolin)
