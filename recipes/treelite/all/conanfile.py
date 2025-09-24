import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc_static_runtime

required_conan_version = ">=2.1"


class TreeliteConan(ConanFile):
    name = "treelite"
    description = "Universal model exchange and serialization format for decision tree forests"
    license = "Apache-2.0"
    homepage = "https://github.com/dmlc/treelite"
    topics = ("machine-learning", "decision-trees", "model-compiler", "xgboost", "lightgbm")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openmp": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("rapidjson/[*]")
        self.requires("nlohmann_json/[>=3.11.3 <4]")
        self.requires("mdspan/[>=0.6.0 <1]")
        if self.options.with_openmp:
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "cmake/ExternalLibs.cmake",
                        "FetchContent_GetProperties(mdspan)",
                        "find_package(mdspan REQUIRED)")
        replace_in_file(self, "CMakeLists.txt", "objtreelite rapidjson mdspan", "")
        replace_in_file(self, "CMakeLists.txt", "install(EXPORT", "message(TRACE #")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["Treelite_BUILD_STATIC_LIBS"] = not self.options.shared
        tc.cache_variables["Treelite_USE_DYNAMIC_MSVC_RUNTIME"] = not is_msvc_static_runtime(self)
        tc.cache_variables["USE_OPENMP"] = self.options.with_openmp
        tc.cache_variables["BUILD_CPP_TEST"] = False
        tc.cache_variables["BUILD_DOXYGEN"] = False
        tc.cache_variables["TEST_COVERAGE"] = False
        tc.cache_variables["DETECT_CONDA_ENV"] = False
        tc.cache_variables["mdspan_POPULATED"] = True
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        if not self.options.shared:
            rm(self, "*treelite.*", os.path.join(self.package_folder, "lib"))
            rm(self, "*treelite.dll", os.path.join(self.package_folder, "bin"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Treelite")
        self.cpp_info.set_property("cmake_target_name", "treelite::treelite")
        self.cpp_info.libs = ["treelite" if self.options.shared else "treelite_static"]
        self.cpp_info.requires = [
            "rapidjson::rapidjson",
            "nlohmann_json::nlohmann_json",
            "mdspan::mdspan",
        ]
        if self.options.with_openmp:
            self.cpp_info.requires.append("openmp::openmp")
            self.cpp_info.defines.append("TREELITE_OPENMP_SUPPORT")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "dl"])
