import os
from pathlib import Path

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc_static_runtime

required_conan_version = ">=2.1"


class SentencePieceConan(ConanFile):
    name = "sentencepiece"
    description = "Unsupervised text tokenizer for Neural Network-based text generation"
    license = "Apache-2.0"
    homepage = "https://github.com/google/sentencepiece"
    topics = ("nlp", "tokenizer", "neural-network", "machine-learning", "llm")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tools": [True, False],
        "build_nfkc": [True, False],
        "with_tcmalloc": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "tools": True,
        "build_nfkc": True,
        "with_tcmalloc": False,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def configure(self):
        if self.options.shared:
            self.settings.rm_safe("fPIC")

    def requirements(self):
        self.requires("protobuf/[*]", transitive_headers=True, transitive_libs=True)
        self.requires("abseil/[*]")
        if self.options.build_nfkc:
            self.requires("icu/[*]")
        if self.options.with_tcmalloc:
            self.requires("gperftools/[^2]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("protobuf/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 17)", "")
        replace_in_file(self, "src/CMakeLists.txt", " -fPIC", "")
        replace_in_file(self, "src/CMakeLists.txt",
                        "find_library(TCMALLOC_LIB NAMES tcmalloc_minimal)",
                        "find_package(gperftools REQUIRED)\n"
                        "set(TCMALLOC_LIB gperftools::tcmalloc_minimal)")
        rmdir(self, "third_party/absl")
        rmdir(self, "third_party/absl.org")
        rmdir(self, "third_party/protobuf-lite")
        for f in list(Path("src").rglob("*.cc")) + list(Path("src").rglob("*.h")):
            replace_in_file(self, f, "third_party/absl", "absl", strict=False)
        replace_in_file(self, "CMakeLists.txt",
                        "if (NOT EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/third_party/absl.org)",
                        "if(0)")
        replace_in_file(self, "src/CMakeLists.txt",
                        "include_directories(${Protobuf_INCLUDE_DIRS})",
                        "link_libraries(protobuf::libprotobuf)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["SPM_ENABLE_SHARED"] = self.options.shared
        tc.cache_variables["SPM_BUILD_TEST"] = False
        tc.cache_variables["SPM_COVERAGE"] = False
        tc.cache_variables["SPM_ENABLE_NFKC_COMPILE"] = self.options.build_nfkc
        tc.cache_variables["SPM_ENABLE_TCMALLOC"] = self.options.with_tcmalloc
        tc.cache_variables["SPM_ENABLE_MSVC_MT_BUILD"] = is_msvc_static_runtime(self)
        tc.cache_variables["SPM_PROTOBUF_PROVIDER"] = "package"
        tc.cache_variables["SPM_ABSL_PROVIDER"] = "package"
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
        if self.options.shared:
            rm(self, "*.a", os.path.join(self.package_folder, "lib"))
            rm(self, "sentencepiece.lib", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        if not self.options.tools:
            if self.settings.os == "Windows":
                rm(self, "*.exe", os.path.join(self.package_folder, "bin"))
            else:
                rmdir(self, os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "sentencepiece")
        self.cpp_info.set_property("pkg_config_name", "sentencepiece")

        suffix = ""
        if self.options.shared and self.settings.os == "Windows":
            if self.settings.compiler == "msvc":
                suffix = "_import.lib"
            else:
                suffix = ".dll.a"

        # Core sentencepiece library
        self.cpp_info.components["core"].set_property("cmake_target_name", "sentencepiece::sentencepiece")
        self.cpp_info.components["core"].set_property("cmake_target_aliases", ["sentencepiece::sentencepiece-static"])
        self.cpp_info.components["core"].set_property("pkg_config_name", "sentencepiece")
        self.cpp_info.components["core"].libs = ["sentencepiece" + suffix]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["core"].system_libs = ["pthread"]
        if self.settings.os == "Android":
            self.cpp_info.components["core"].system_libs = ["log"]
        self.cpp_info.components["core"].requires.append("protobuf::libprotobuf")
        self.cpp_info.components["core"].requires.extend(["abseil::strings", "abseil::flags", "abseil::flags_parse", "abseil::log", "abseil::check"])
        if self.options.build_nfkc:
            self.cpp_info.components["core"].requires.extend(["icu::icu-i18n", "icu::icu-data", "icu::icu-uc"])
        if self.options.with_tcmalloc:
            self.cpp_info.components["core"].requires.append("gperftools::tcmalloc_minimal")

        # Training library
        self.cpp_info.components["train"].set_property("cmake_target_name", "sentencepiece::sentencepiece_train")
        self.cpp_info.components["train"].set_property("cmake_target_aliases", ["sentencepiece::sentencepiece_train-static"])
        self.cpp_info.components["train"].libs = ["sentencepiece_train" + suffix]
        self.cpp_info.components["train"].requires = ["core"]
