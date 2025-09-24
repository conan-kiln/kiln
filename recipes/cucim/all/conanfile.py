import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class PackageConan(ConanFile):
    name = "cucim"
    description = "cuCIM: RAPIDS GPU-accelerated image processing library"
    license = "Apache-2.0"
    homepage = "https://docs.rapids.ai/api/cucim/stable/"
    topics = ("computer-vision", "gpu", "cuda", "image-processing", "nvidia", "medical-imaging", "segmentation", "image-analysis",
              "microscopy", "digital-pathology", "image-data", "multidimensional-image-processing", "rapids")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-cuda/latest"
    python_requires_extend = "conan-cuda.Cuda"

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def package_id(self):
        # No device code is being built
        del self.info.settings.cuda

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("fmt/[*]", transitive_headers=True, transitive_libs=True)
        self.requires("abseil/[*]")
        self.requires("libcuckoo/[>=0.3 <1]")
        self.requires("boost/[^1.75]", libs=False)
        self.requires("nlohmann_json/[^3]")
        self.requires("nvtx/[^3]", transitive_headers=True, transitive_libs=True)
        self.requires("taskflow/[^3.2]")
        self.requires("dlpack/[^1]", transitive_headers=True)
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cufile")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <5]")
        self.tool_requires("rapids-cmake/[*]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        save(self, "cmake/RAPIDS.cmake", "find_package(rapids-cmake REQUIRED)")
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 17)", "")
        replace_in_file(self, "CMakeLists.txt", "add_definitions(-D_GLIBCXX_USE_CXX11_ABI=0)", "")
        replace_in_file(self, "cpp/CMakeLists.txt", "_GLIBCXX_USE_CXX11_ABI=0", "")
        replace_in_file(self, "CMakeLists.txt", "${INSTALL_TARGETS}", "cucim")
        replace_in_file(self, "CMakeLists.txt", "superbuild_depend(", "# superbuild_depend(")
        replace_in_file(self, "CMakeLists.txt", "# Copy 3rdparty headers", "return()")
        replace_in_file(self, "cpp/CMakeLists.txt", "gds_static", "gds")
        replace_in_file(self, "gds/CMakeLists.txt", "-Werror", "")
        replace_in_file(self, "cpp/CMakeLists.txt", "-Werror", "")
        save(self, "benchmarks/CMakeLists.txt", "")
        save(self, "examples/cpp/CMakeLists.txt", "")
        save(self, "cpp/tests/CMakeLists.txt", "")
        rmdir(self, "cpp/include/cucim/3rdparty")
        replace_in_file(self, "cpp/CMakeLists.txt", "include/cucim/3rdparty", "# include/cucim/3rdparty")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_libcucim_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["CMAKE_PREFIX_PATH"] = self.generators_folder.replace("\\", "/")
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_Doxygen"] = True
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["CUCIM_STATIC_GDS"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.build_context_activated.append("rapids-cmake")
        deps.build_context_build_modules.append("rapids-cmake")
        deps.set_property("fmt", "cmake_target_name", "deps::fmt")
        deps.set_property("abseil", "cmake_target_name", "deps::abseil")
        deps.set_property("libcuckoo", "cmake_target_name", "deps::libcuckoo")
        deps.set_property("boost", "cmake_target_name", "deps::boost-header-only")
        deps.set_property("nlohmann_json", "cmake_target_name", "deps::json")
        deps.set_property("nvtx", "cmake_target_name", "deps::nvtx3")
        deps.set_property("taskflow", "cmake_target_name", "deps::taskflow")
        deps.generate()

        tc = self.cuda.CudaToolchain()
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cucim")
        self.cpp_info.set_property("cmake_target_name", "cucim::cucim")
        self.cpp_info.libs = ["cucim"]
        v = Version(self.version)
        self.cpp_info.defines = [
            f"CUCIM_VERSION={self.version}",
            f"CUCIM_VERSION_MAJOR={v.major}",
            f"CUCIM_VERSION_MINOR={v.minor}",
            f"CUCIM_VERSION_PATCH={v.patch}",
            f"CUCIM_VERSION_BUILD=dev",
            "CUCIM_SUPPORT_GDS",
            "CUCIM_STATIC_GDS",
            "CUCIM_SUPPORT_CUDA",
            "CUCIM_SUPPORT_NVTX",
        ]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread", "dl"]
