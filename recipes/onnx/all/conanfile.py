import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class OnnxConan(ConanFile):
    name = "onnx"
    description = "Open standard for machine learning interoperability."
    license = "Apache-2.0"
    topics = ("machine-learning", "deep-learning", "neural-network")
    homepage = "https://github.com/onnx/onnx"
    url = "https://github.com/conan-io/conan-center-index"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "disable_static_registration": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "disable_static_registration": True,
    }

    @property
    def _min_cppstd(self):
        if Version(self.version) >= "1.15.0":
            return 17
        if Version(self.version) >= "1.13.0" and is_msvc(self):
            return 17
        return 11

    @property
    def _compilers_minimum_version(self):
        if Version(self.version) < "1.16.0":
            return {
                "msvc": "191",
                "gcc": "7",
                "clang": "5",
                "apple-clang": "10",
            }
        # 1.16.0+ requires <filesystem> header available with gcc8+
        return {
            "msvc": "191",
            "gcc": "8",
            "clang": "5",
            "apple-clang": "10",
        }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if is_msvc(self):
            del self.options.shared
            self.package_type = "static-library"
        if self.options.get_safe("shared"):
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if Version(self.version) >= "1.15.0":
            self.requires("protobuf/[>=3.21.12]", transitive_headers=True, transitive_libs=True)
        else:
            self.requires("protobuf/[>3 <3.22]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        if self._min_cppstd > 11:
            minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
            if minimum_version and Version(self.settings.compiler.version) < minimum_version:
                raise ConanInvalidConfiguration(
                    f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
                )

    def build_requirements(self):
        self.tool_requires("protobuf/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        if Version(self.version) >= "1.15.0":
            # The project incorrectly tries to add missing Protobuf deps
            replace_in_file(self, "CMakeLists.txt",
                            '("${Protobuf_VERSION}" VERSION_GREATER_EQUAL',
                            '(FALSE) #')

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ONNX_USE_PROTOBUF_SHARED_LIBS"] = self.dependencies.host["protobuf"].options.shared
        tc.variables["BUILD_ONNX_PYTHON"] = False
        tc.variables["ONNX_GEN_PB_TYPE_STUBS"] = False
        tc.variables["ONNX_WERROR"] = False
        tc.variables["ONNX_COVERAGE"] = False
        tc.variables["ONNX_BUILD_TESTS"] = False
        tc.variables["ONNX_USE_LITE_PROTO"] = self.dependencies.host["protobuf"].options.lite
        tc.variables["ONNX_ML"] = True
        tc.variables["ONNX_VERIFY_PROTO3"] = Version(self.dependencies.host["protobuf"].ref.version).major == "3"
        if is_msvc(self):
            tc.variables["ONNX_USE_MSVC_STATIC_RUNTIME"] = is_msvc_static_runtime(self)
        tc.variables["ONNX_DISABLE_STATIC_REGISTRATION"] = self.options.get_safe("disable_static_registration")
        if Version(self.version) < "1.17.0":
            tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.15" # CMake 4 support
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ONNX")

        self.cpp_info.components["libonnx"].set_property("cmake_target_name", "onnx")
        self.cpp_info.components["libonnx"].libs = ["onnx"]
        self.cpp_info.components["libonnx"].defines = ["ONNX_NAMESPACE=onnx", "ONNX_ML=1", "__STDC_FORMAT_MACROS"]
        self.cpp_info.components["libonnx"].requires = ["onnx_proto"]

        self.cpp_info.components["onnx_proto"].set_property("cmake_target_name", "onnx_proto")
        self.cpp_info.components["onnx_proto"].libs = ["onnx_proto"]
        self.cpp_info.components["onnx_proto"].defines = ["ONNX_NAMESPACE=onnx", "ONNX_ML=1"]
        self.cpp_info.components["onnx_proto"].requires = ["protobuf::libprotobuf"]
