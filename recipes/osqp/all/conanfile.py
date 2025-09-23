import os
from functools import cached_property

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *

required_conan_version = ">=2.4"


class OsqpConan(ConanFile):
    name = "osqp"
    package_type = "library"
    description = "The OSQP (Operator Splitting Quadratic Program) solver is a numerical optimization package."
    license = "Apache-2.0"
    homepage = "https://osqp.org/"
    topics = ("machine-learning", "control", "optimization", "svm", "solver", "lasso", "portfolio-optimization",
              "numerical-optimization", "quadratic-programming", "convex-optimization", "model-predictive-control")
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "backend": ["builtin", "cuda", "mkl"],
        "float32": [True, False],
        "int32": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "backend": "builtin",
        "float32": False,
        "int32": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.options.backend != "cuda":
            del self.settings.cuda
        else:
            self.options.int32.value = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("qdldl/[>=0.1 <1]", options={"float32": self.options.float32, "int32": self.options.int32})
        self.requires("suitesparse-amd/[*]")
        if self.options.backend == "cuda":
            self.cuda.requires("cudart")
            self.cuda.requires("cublas")
            self.cuda.requires("cusparse")
        elif self.options.backend == "mkl":
            self.requires("onemkl/[*]")

    def validate(self):
        if self.options.backend == "cuda":
            self.cuda.validate_settings()

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18]")
        if self.options.backend == "cuda":
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # Let CudaToolchain manage CUDA architectures
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CUDA_ARCHITECTURES ", "# set(CMAKE_CUDA_ARCHITECTURES ")
        replace_in_file(self, "algebra/mkl/CMakeLists.txt", "$<TARGET_PROPERTY:MKL::MKL", ") #")
        rmdir(self, "algebra/_common/lin_sys/qdldl/amd")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_PROJECT_osqp_INCLUDE"] = "conan_deps.cmake"
        tc.variables["OSQP_BUILD_SHARED_LIB"] = self.options.shared
        tc.variables["OSQP_BUILD_STATIC_LIB"] = not self.options.shared
        tc.variables["OSQP_ALGEBRA_BACKEND"] = self.options.backend
        tc.variables["OSQP_BUILD_DEMO_EXE"] = False
        tc.variables["OSQP_BUILD_UNITTESTS"] = False
        tc.variables["OSQP_USE_FLOAT"] = self.options.float32
        tc.variables["OSQP_USE_LONG"] = not self.options.int32
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        if self.options.backend == "cuda":
            cuda_tc = self.cuda.CudaToolchain()
            cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "include", "qdldl"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "osqp")
        self.cpp_info.set_property("cmake_target_name", "osqp::osqp")
        self.cpp_info.libs = ["osqp" if self.options.shared else "osqpstatic"]
        self.cpp_info.includedirs.append("include/osqp")
        self.cpp_info.resdirs = ["share"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
