import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, check_max_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import *
from conan.tools.microsoft import is_msvc_static_runtime

required_conan_version = ">=2.1"


class LibiglConan(ConanFile):
    name = "libigl"
    description = "Simple C++ geometry processing library"
    # As per https://libigl.github.io/license/, the library itself is MPL-2, components are not
    # No issue as we don't build them, but if done so in the future, please update this field!
    license = "MPL-2.0"
    homepage = "https://libigl.github.io/"
    topics = ("geometry", "matrices", "algorithms", "header-only")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "header_only": [True, False],
    }
    default_options = {
        "fPIC": True,
        "header_only": False,
    }
    implements = ["auto_header_only", "auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/3.4.0", transitive_headers=True)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16]")

    def validate(self):
        if self.settings.arch == "x86":
            raise ConanInvalidConfiguration(f"Architecture {self.settings.arch} is not supported")
        if is_msvc_static_runtime(self) and not self.options.header_only:
            raise ConanInvalidConfiguration("Visual Studio build with MT runtime is not supported")
        check_min_cppstd(self, 14)
        # v2.5.0 fails with WindingNumberTree.h:217:57: error: template-id not allowed for destructor
        check_max_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()

        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_libigl_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["LIBIGL_USE_STATIC_LIBRARY"] = not self.options.header_only
        tc.cache_variables["LIBIGL_POSITION_INDEPENDENT_CODE"] = self.options.get_safe("fPIC", True)
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0048"] = "NEW"
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"

        # All these dependencies are needed to build the examples or the tests
        tc.cache_variables["LIBIGL_BUILD_TUTORIALS"] = False
        tc.cache_variables["LIBIGL_BUILD_TESTS"] = False
        tc.cache_variables["LIBIGL_BUILD_PYTHON"] = False

        tc.cache_variables["LIBIGL_EMBREE"] = False
        tc.cache_variables["LIBIGL_GLFW"] = False
        tc.cache_variables["LIBIGL_IMGUI"] = False
        tc.cache_variables["LIBIGL_OPENGL"] = False
        tc.cache_variables["LIBIGL_STB"] = False
        tc.cache_variables["LIBIGL_PREDICATES"] = False
        tc.cache_variables["LIBIGL_SPECTRA"] = False
        tc.cache_variables["LIBIGL_XML"] = False
        tc.cache_variables["LIBIGL_COPYLEFT_CORE"] = False
        tc.cache_variables["LIBIGL_COPYLEFT_CGAL"] = False
        tc.cache_variables["LIBIGL_COPYLEFT_COMISO"] = False
        tc.cache_variables["LIBIGL_COPYLEFT_TETGEN"] = False
        tc.cache_variables["LIBIGL_RESTRICTED_MATLAB"] = False
        tc.cache_variables["LIBIGL_RESTRICTED_MOSEK"] = False
        tc.cache_variables["LIBIGL_RESTRICTED_TRIANGLE"] = False
        tc.cache_variables["LIBIGL_GLFW_TESTS"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        # If components are built and packaged in the future, uncomment this line, their license is different
        # copy(self, "LICENSE.GPL", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "LICENSE.MPL2", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        if not self.options.header_only:
            rm(self, "*.c", self.package_folder, recursive=True)
            rm(self, "*.cpp", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "libigl")
        self.cpp_info.set_property("cmake_target_name", "igl::igl")

        self.cpp_info.components["common"].set_property("cmake_target_name", "igl::common")
        self.cpp_info.components["common"].requires = ["eigen::eigen"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["common"].system_libs = ["pthread"]

        self.cpp_info.components["core"].set_property("cmake_target_name", "igl::core")
        self.cpp_info.components["core"].requires = ["common"]
        if not self.options.header_only:
            self.cpp_info.components["core"].libs = ["igl"]
            self.cpp_info.components["core"].defines.append("IGL_STATIC_LIBRARY")
