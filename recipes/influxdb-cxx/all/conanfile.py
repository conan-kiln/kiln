import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"

class InfluxdbCxxConan(ConanFile):
    name = "influxdb-cxx"
    description = "InfluxDB C++ client library."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/offa/influxdb-cxx"
    topics = ("influxdb", "influxdb-client")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "library"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_boost": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_boost": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("cpr/[^1.10.4]")
        if self.options.with_boost:
            self.requires("boost/[^1.71.0 <1.88]", options={"with_system": True})

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        # BUILD_SHARED_LIBS is defined explicitly in CMakeLists.txt
        tc.cache_variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.cache_variables["INFLUXCXX_TESTING"] = False
        tc.cache_variables["INFLUXCXX_WITH_BOOST"] = self.options.with_boost
        if self.options.shared:
            # See https://github.com/offa/influxdb-cxx/issues/194
            # Feedback pending: https://github.com/offa/influxdb-cxx/pull/245
            tc.preprocessor_definitions["InfluxDB_EXPORTS"] = 1
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "InfluxDB")
        self.cpp_info.set_property("cmake_target_name", "InfluxData::InfluxDB")
        self.cpp_info.libs = ["InfluxDB"]
