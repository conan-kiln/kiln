import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class VoroppConan(ConanFile):
    name = "voropp"
    description = (
        "Voro++ is a open source software library for the computation of the "
        "Voronoi diagram, a widely-used tessellation that has applications in "
        "many scientific fields."
    )
    license = "BSD-3-Clause"
    topics = ("voro++", "voronoi-diagram", "tesselation")
    homepage = "http://math.lbl.gov/voro++"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    exports_sources = "CMakeLists.txt"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True, verify=False)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["VOROPP_SRC_DIR"] = self.source_folder.replace("\\", "/")
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, os.pardir))
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["voro++"]
