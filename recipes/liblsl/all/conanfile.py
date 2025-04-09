import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class LiblslConan(ConanFile):
    name = "liblsl"
    description = "Lab Streaming Layer is a C++ library for multi-modal " \
                  "time-synched data transmission over the local network"
    license = "MIT"
    topics = ("labstreaminglayer", "lsl", "network", "stream", "signal",
              "transmission")
    homepage = "https://github.com/sccn/liblsl"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _min_cppstd(self):
        return "14"

    @property
    def _compilers_minimum_version(self):
        return {
            "msvc": "191",
            "gcc": "5",
            "clang": "3.5",
            "apple-clang": "10",
        }

    def requirements(self):
        self.requires("boost/1.86.0")
        self.requires("pugixml/1.13")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support.",
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
            destination=self.source_folder, strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LSL_BUILD_STATIC"] = not self.options.shared
        tc.variables["LSL_BUNDLED_BOOST"] = False
        tc.variables["LSL_BUNDLED_PUGIXML"] = False
        tc.variables["lslgitrevision"] = "v" + self.version
        tc.variables["lslgitbranch"] = "master"
        tc.generate()
        cd = CMakeDeps(self)
        cd.generate()

    def _patch_sources(self):
        if not self.options.shared:
            # Do not force PIC
            replace_in_file(
                self,
                os.path.join(self.source_folder, "CMakeLists.txt"),
                "set(CMAKE_POSITION_INDEPENDENT_CODE ON)",
                ""
            )

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        rm(self, "lslver*", os.path.join(self.package_folder, "bin"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "LSL")
        self.cpp_info.set_property("cmake_target_name", "LSL::lsl")
        self.cpp_info.requires = ["boost::boost", "pugixml::pugixml"]
        self.cpp_info.libs = ["lsl"]
        self.cpp_info.defines = ["LSLNOAUTOLINK"]
        if not self.options.shared:
            self.cpp_info.defines.append("LIBLSL_STATIC")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["iphlpapi", "winmm", "mswsock", "ws2_32"]
