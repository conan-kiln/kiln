find_package(Eigen3 REQUIRED)
find_package(OpenCV REQUIRED)
find_package(Sophus REQUIRED)
find_package(srrg_hbst REQUIRED)

set(OpenCV_LIBS opencv_core opencv_features2d)

add_definitions(-DSRRG_HBST_HAS_EIGEN)
add_definitions(-DSRRG_HBST_HAS_OPENCV)
add_definitions(-DSRRG_MERGE_DESCRIPTORS)
set(hbst_SOURCE_DIR ${srrg_hbst_INCLUDE_DIR})
