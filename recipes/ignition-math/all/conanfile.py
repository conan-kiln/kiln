import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class IgnitionMathConan(ConanFile):
    name = "ignition-math"
    description = "Math classes and functions for robot applications"
    license = "Apache-2.0"
    homepage = "https://gazebosim.org/libs/math"
    topics = ("ignition", "math", "robotics", "gazebo")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_swig": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_swig": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/3.4.0", transitive_headers=True)
        self.requires("pybind11/[^2]", visible=False)

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("ignition-cmake/[^2.17.1]")
        self.tool_requires("cpython/[^3]")
        if self.options.enable_swig:
            self.tool_requires("swig/[^4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, "src/ruby/CMakeLists.txt", "${SWIG_USE_FILE}", "UseSWIG")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = False
        tc.cache_variables["SKIP_SWIG"] = not self.options.enable_swig
        tc.generate()
        deps = CMakeDeps(self)
        deps.build_context_activated.append("ignition-cmake")
        deps.build_context_build_modules.append("ignition-cmake")
        deps.build_context_activated.append("swig")
        deps.build_context_build_modules.append("swig")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        # Remove MS runtime files
        for dll_pattern_to_remove in ["concrt*.dll", "msvcp*.dll", "vcruntime*.dll"]:
            rm(self, dll_pattern_to_remove, os.path.join(self.package_folder, "bin"), recursive=True)

    def package_info(self):
        major = Version(self.version).major
        libname = f"ignition-math{major}"
        self.cpp_info.set_property("cmake_file_name", libname)
        self.cpp_info.set_property("cmake_target_name", f"{libname}::{libname}-all")

        main_component = self.cpp_info.components[libname]
        main_component.set_property("cmake_target_name", f"{libname}::{libname}")
        main_component.set_property("pkg_config_name", libname)
        main_component.libs = [libname]
        main_component.includedirs.append(f"include/ignition/math{major}")
        main_component.resdirs = ["share"]
        main_component.requires = ["eigen::eigen"]

        eigen3_component = self.cpp_info.components["eigen3"]
        eigen3_component.set_property("cmake_target_name", f"{libname}::{libname}-eigen3")
        eigen3_component.set_property("pkg_config_name", f"{libname}-eigen3")
        eigen3_component.includedirs.append(f"include/ignition/math{major}")
        eigen3_component.requires = [libname, "eigen::eigen"]

        self.runenv_info.prepend_path("PYTHONPATH", os.path.join(self.package_folder, "lib", "python", "ignition"))
