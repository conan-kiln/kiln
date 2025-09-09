import os
from functools import cached_property

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class SoPlexConan(ConanFile):
    name = "soplex"
    description = "SoPlex linear programming solver"
    license = "Apache-2.0"
    homepage = "https://soplex.zib.de"
    topics = ("simplex", "solver", "linear", "programming")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "library"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_boost": [True, False],
        "with_gmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_boost": True,
        "with_gmp": True,
    }
    implements = ["auto_shared_fpic"]

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if Version(self.version) < "6.0":
            del self.options.shared
            self.package_type = "static-library"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # transitive libs as anything using soplex requires gzread, gzwrite, gzclose, gzopen
        self.requires("zlib-ng/[^2.0]", transitive_headers=True, transitive_libs=True)
        if self.options.with_gmp:
            # transitive libs as anything using soplex requires __gmpz_init_set_si
            # see https://github.com/conan-io/conan-center-index/pull/16017#issuecomment-1495688452
            self.requires("gmp/[^6.3.0]", transitive_headers=True, transitive_libs=True)
        if self.options.with_boost:
            self.requires("boost/[^1.71.0]", transitive_headers=True, libs=False)

    def validate(self):
        check_min_cppstd(self, 14 if Version(self.version) >= "6.0" else 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        if Version(self.version) < "7.0":
            replace_in_file(self, "CMakeLists.txt",
                            "cmake_minimum_required(VERSION ",
                            "cmake_minimum_required(VERSION 3.5) # ")
        if Version(self.version) < "4.0":
            save(self, "src/git_hash.cpp", '#define SPX_GITHASH ""\n')

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["MPFR"] = False
        tc.cache_variables["GMP"] = self.options.with_gmp
        tc.cache_variables["BOOST"] = self.options.with_boost
        if self.options.with_boost:
            v = self.dependencies["boost"].ref.version
            tc.cache_variables["Boost_VERSION_MACRO"] = str(100000 * int(v.major.value) + 100 * int(v.minor.value) + int(v.patch.value))
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()
        deps = CMakeDeps(self)
        if self.options.with_gmp:
            deps.set_property("gmp", "cmake_file_name", "GMP")
        deps.generate()

    @cached_property
    def _target(self):
        if self.options.get_safe("shared", False):
            return "libsoplexshared"
        elif self.options.get_safe("fPIC"):
            return "libsoplex-pic"
        else:
            return "libsoplex"

    @cached_property
    def _all_targets(self):
        if Version(self.version) >= "6.0":
            return ["soplex", "libsoplex", "libsoplex-pic", "libsoplexshared"]
        else:
            return ["soplex", "libsoplex", "libsoplex-pic"]

    def _patch_sources(self):
        cmakelists = os.path.join(self.source_folder, "src", "CMakeLists.txt")
        # Build only the desired target
        excluded = [l for l in self._all_targets if l != self._target]
        save(self, cmakelists, "\n" + "\n".join(f"set_target_properties({tgt} PROPERTIES EXCLUDE_FROM_ALL 1)" for tgt in excluded), append=True)
        # Don't install any other targets
        replace_in_file(self, cmakelists,
                        "install(TARGETS " + " ".join(self._all_targets),
                        "install(TARGETS " + self._target)
        replace_in_file(self, cmakelists, "install(EXPORT ", "# install(EXPORT ")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        if Version(self.version) >= "6.0":
            copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        else:
            copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "soplex")
        libname = self._target if self.settings.compiler == "msvc" else self._target[3:]
        self.cpp_info.libs = [libname]
        self.cpp_info.set_property("cmake_target_name", libname)
        self.cpp_info.set_property("cmake_target_aliases", ["soplex"])
        if self.settings.compiler == "msvc":
            # https://github.com/scipopt/soplex/blob/release-715/src/CMakeLists.txt#L185
            self.cpp_info.cxxflags.append("/Zc:__cplusplus")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
