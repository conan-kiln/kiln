import glob
import os
from functools import lru_cache

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

from helpers import parse_proto_libraries

required_conan_version = ">=2.1"


class GoogleAPIS(ConanFile):
    name = "googleapis"
    package_type = "library"
    description = "Public interface definitions of Google APIs"
    license = "Apache-2.0"
    homepage = "https://github.com/googleapis/googleapis"
    topics = "google", "protos", "api"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    exports = "helpers.py"

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
            self.options["protobuf"].shared = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # https://github.com/conan-io/conan-center-index/pull/15601#issuecomment-1493086506
        self.requires("protobuf/[>=3.21.12]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 11)
        if is_msvc(self) and self.options.shared:
            raise ConanInvalidConfiguration("Source code generated from protos is missing some export macro")
        if self.options.shared and not self.dependencies.host["protobuf"].options.shared:
            raise ConanInvalidConfiguration("If built as shared, protobuf must be shared as well. Please, use `protobuf:shared=True`")

    def build_requirements(self):
        self.tool_requires("protobuf/<host_version>")
        # CMake >= 3.20 is required. There is a proto with dots in the name 'k8s.min.proto' and CMake fails to generate project files
        self.tool_requires("cmake/[>=3.20 <5]")

    def source(self):
        get(self, **self.conan_data["sources"][str(self.version)], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    @lru_cache
    def _parse_proto_libraries(self):
        # Generate the libraries to build dynamically
        proto_libraries = []
        for filename in glob.iglob(os.path.join(self.source_folder, "google", "**", "BUILD.bazel"), recursive=True):
            proto_libraries += parse_proto_libraries(filename, self.source_folder, self.output.error)

        for filename in glob.iglob(os.path.join(self.source_folder, "grafeas", "**", "BUILD.bazel"), recursive=True):
            proto_libraries += parse_proto_libraries(filename, self.source_folder, self.output.error)

        # Validate that all files exist and all dependencies are found
        all_deps = [f"{it.qname}:{it.name}" for it in proto_libraries]
        all_deps += ["protobuf::libprotobuf"]
        for it in proto_libraries:
            it.validate(self.source_folder, all_deps)

        # Mark the libraries we need recursively (C++ context)
        all_dict = {f"{it.qname}:{it.name}": it for it in proto_libraries}

        def activate_library(proto_library):
            proto_library.is_used = True
            for it_dep in proto_library.deps:
                if it_dep == "protobuf::libprotobuf":
                    continue
                activate_library(all_dict[it_dep])

        for it in filter(lambda u: u.is_used, proto_libraries):
            activate_library(it)

        # Tweaks
        def deactivate_library(key):
            if key in all_dict:
                all_dict[key].is_used = False
        if (self.settings.os == "Linux" and self.settings.compiler == "clang" and self.settings.compiler.libcxx == "libc++") or \
            is_msvc(self):
            deactivate_library("//google/cloud/channel/v1:channel_proto")
            deactivate_library("//google/cloud/channel/v1:channel_cc_proto")
        #  - Inconvenient names for android
        if self.settings.os == "Android":
            deactivate_library("//google/identity/accesscontextmanager/type:type_proto")
            deactivate_library("//google/identity/accesscontextmanager/type:type_cc_proto")
            deactivate_library("//google/identity/accesscontextmanager/v1:accesscontextmanager_proto")
            deactivate_library("//google/identity/accesscontextmanager/v1:accesscontextmanager_cc_proto")
            deactivate_library("//google/devtools/testing/v1:testing_proto")
            deactivate_library("//google/devtools/testing/v1:testing_cc_proto")
            deactivate_library("//google/devtools/resultstore/v2:resultstore_proto")
            deactivate_library("//google/devtools/resultstore/v2:resultstore_cc_proto")
            deactivate_library("//google/cloud/talent/v4beta1:talent_proto")
            deactivate_library("//google/cloud/talent/v4beta1:talent_cc_proto")
            deactivate_library("//google/cloud/talent/v4:talent_proto")
            deactivate_library("//google/cloud/talent/v4:talent_cc_proto")
            deactivate_library("//google/cloud/asset/v1:asset_proto")
            deactivate_library("//google/cloud/asset/v1:asset_cc_proto")
        # This fails to build on Windows. It is arguably a missing feature of
        # Protobuf.
        #     https://github.com/protocolbuffers/protobuf/issues/12774
        # Fortunately this library is not used by any downstream packages
        # (grpc-protos, or google-cloud-cpp), and it is only "beta" at the
        # moment. Simply disable it for now.
        deactivate_library("//google/cloud/lifesciences/v2beta:lifesciences_proto")
        deactivate_library("//google/cloud/lifesciences/v2beta:lifesciences_cc_proto")

        return proto_libraries

    def build(self):
        proto_libraries = self._parse_proto_libraries()
        # Use a separate file to host the generated code, which is generated in full each time.
        # This is safe to call multiple times, for example, if you need to invoke `conan build` more than
        # once.
        with open(os.path.join(self.source_folder, "generated_targets.cmake"), "w", encoding="utf-8") as f:
            f.write("# Generated C++ library targets for googleapis\n")
            f.write("# DO NOT EDIT - change the generation code in conanfile.py instead\n")
            for it in filter(lambda u: u.is_used, proto_libraries):
                f.write(it.cmake_content)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    _DEPS_FILE = "share/googleapis/generated_targets.deps"

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.proto", self.source_folder, os.path.join(self.package_folder, "share", "googleapis"))
        copy(self, "*.pb.h", self.build_folder, os.path.join(self.package_folder, "include"))

        for pattern in ["*.lib", "*.a", "*.so*", "*.dylib"]:
            copy(self, pattern, self.build_folder, os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.dll", self.build_folder, os.path.join(self.package_folder, "bin"), keep_path=False)

        with open(os.path.join(self.package_folder, self._DEPS_FILE), "w", encoding="utf-8") as f:
            for lib in filter(lambda u: u.is_used, self._parse_proto_libraries()):
                interface = "LIB" if lib.srcs else "INTERFACE"
                f.write(f"{lib.cmake_target} {interface} {','.join(lib.cmake_deps)}\n")

    def package_info(self):
        with open(os.path.join(self.package_folder, self._DEPS_FILE), "r", encoding="utf-8") as f:
            for line in f:
                (name, libtype, deps) = line.rstrip("\n").split(" ")
                self.cpp_info.components[name].requires = deps.split(",")
                self.cpp_info.components[name].resdirs = [os.path.join("share", "googleapis")]
                if libtype == "LIB":
                    self.cpp_info.components[name].libs = [name]
                self.cpp_info.components[name].set_property("pkg_config_name", name)
                if self.settings.os in ["Linux", "FreeBSD"]:
                    self.cpp_info.components[name].system_libs.extend(["m"])
