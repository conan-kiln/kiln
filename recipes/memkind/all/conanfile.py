import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import check_min_cppstd, cross_building
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsDeps, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class MemkindConan(ConanFile):
    name = "memkind"
    description = "User Extensible Heap Manager"
    license = "BSD-2-Clause"
    homepage = "https://pmem.io/memkind/"
    topics = ("memory", "numa", "jemalloc", "heap-manager", "hbw")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "with_hwloc": [True, False],
        "with_tls": [True, False],
        "with_decorators": [True, False],
        "with_heap_manager": [True, False],
        "tools": [True, False],
    }
    default_options = {
        "fPIC": True,
        "with_hwloc": True,
        "with_tls": False,
        "with_decorators": False,
        "with_heap_manager": True,
        "tools": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("libnuma/[^2.0]", transitive_headers=True)
        if self.options.with_hwloc:
            self.requires("hwloc/[^2.3.0]", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 11)
        if self.settings.os not in ["Linux", "FreeBSD"]:
            raise ConanInvalidConfiguration(f"memkind requires a Unix-like system. {self.settings.os} is not supported.")

    def build_requirements(self):
        self.tool_requires("libtool/[^2.4.7]")
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/latest")
            if is_msvc(self):
                self.tool_requires("automake/[^1.18.1]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "examples/Makefile.mk", "")

    def generate(self):
        if not cross_building(self):
            VirtualRunEnv(self).generate(scope="build")

        yes_no = lambda x: "yes" if x else "no"
        tc = AutotoolsToolchain(self)
        tc.configure_args.extend([
            "--enable-daxctl=no",
            f"--enable-hwloc={yes_no(self.options.with_hwloc)}",
            f"--enable-tls={yes_no(self.options.with_tls)}",
            f"--enable-decorators={yes_no(self.options.with_decorators)}",
            f"--enable-heap-manager={yes_no(self.options.with_heap_manager)}",
        ])
        tc.generate()

        deps = AutotoolsDeps(self)
        deps.generate()

    def build(self):
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            save(self, "VERSION", self.version)
            autotools.autoreconf()
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install()
        if not self.options.tools:
            rmdir(self, os.path.join(self.package_folder, "bin"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "memkind")
        self.cpp_info.libs = ["memkind"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl", "rt", "pthread", "m"]
