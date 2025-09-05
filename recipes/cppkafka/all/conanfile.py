import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class CppKafkaConan(ConanFile):
    name = "cppkafka"
    description = "Modern C++ Apache Kafka client library (wrapper for librdkafka)"
    license = "MIT"
    homepage = "https://github.com/mfontanini/cppkafka"
    topics = ("librdkafka", "kafka")
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

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/[^1.71.0]", transitive_headers=True, libs=False)
        self.requires("librdkafka/[^2.3.0]", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CPPKAFKA_BUILD_SHARED"] = self.options.shared
        tc.variables["CPPKAFKA_DISABLE_TESTS"] = True
        tc.variables["CPPKAFKA_DISABLE_EXAMPLES"] = True
        tc.variables["CPPKAFKA_RDKAFKA_STATIC_LIB"] = False # underlying logic is useless
        if Version(self.version) < "0.4.1" and self.settings.os == "Windows":
            tc.preprocessor_definitions["NOMINMAX"] = 1
        tc.generate()
        cd = CMakeDeps(self)
        cd.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "CppKafka")
        self.cpp_info.set_property("cmake_target_name", "CppKafka::cppkafka")
        self.cpp_info.set_property("pkg_config_name", "cppkafka")

        self.cpp_info.libs = ["cppkafka"]
        self.cpp_info.requires = ["boost::headers", "librdkafka::librdkafka"]
        if self.settings.os == "Windows":
            if not self.options.shared:
                self.cpp_info.system_libs = ["mswsock", "ws2_32"]
        elif self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
        if not self.options.shared:
            self.cpp_info.defines.append("CPPKAFKA_STATIC")
