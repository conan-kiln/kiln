#include <cupoch/geometry/pointcloud.h>
#include <cupoch/registration/registration.h>

#include <Eigen/Core>
#include <Eigen/Geometry>
#include <iostream>

int main() {
    using namespace cupoch;
    using namespace Eigen;
    const size_t size = 20;
    std::vector<Vector3f> points(size);
    for (int i = 0; i < size; ++i) {
        points[i] = Vector3f::Random() * 100.0f;
    }
    geometry::PointCloud source{points};
    geometry::PointCloud target{points};
    auto icp_result = registration::RegistrationICP(source, target, 1);
    std::cout << "cupoch::registration::RegistrationICP() ran successfully\n";
}
