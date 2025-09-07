import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsDeps, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, NMakeToolchain, msvc_runtime_flag

required_conan_version = ">=2.1"


class SevenZipConan(ConanFile):
    name = "7zip"
    description = "7-Zip is a file archiver with a high compression ratio"
    license = ("LGPL-2.1-or-later", "BSD-3-Clause", "Unrar")
    homepage = "https://www.7-zip.org"
    topics = ("archive", "compression", "decompression", "zip")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def validate(self):
        if self.settings.os != "Windows":
            raise ConanInvalidConfiguration("Only Windows supported")
        if self.settings.arch not in ("x86", "x86_64"):
            raise ConanInvalidConfiguration("Unsupported architecture")

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        if not is_msvc(self):
            self.tool_requires("make/[^4.4.1]")

    def package_id(self):
        del self.info.settings.build_type
        del self.info.settings.compiler

    def source(self):
        get(self, **self.conan_data["sources"][self.version])

    def generate(self):
        if is_msvc(self):
            tc = NMakeToolchain(self)
            tc.generate()
        else:
            tc = AutotoolsToolchain(self)
            if self.settings.compiler == "gcc":
                env = tc.environment()
                env.define("IS_MINGW", "1")
            tc.generate(env=env)
            deps = AutotoolsDeps(self)
            deps.generate()

    @property
    def _msvc_platform(self):
        return {"x86_64": "x64", "x86": "x86"}[str(self.settings.arch)]

    def _patch_sources(self):
        if is_msvc(self):
            fn = os.path.join(self.source_folder, "CPP", "Build.mak")
            os.chmod(fn, 0o644)
            replace_in_file(self, fn, "-MT", f"-{msvc_runtime_flag(self)}")
            replace_in_file(self, fn, "-MD", f"-{msvc_runtime_flag(self)}")

    def build(self):
        self._patch_sources()
        if is_msvc(self):
            with chdir(self, os.path.join(self.source_folder, "CPP", "7zip")):
                self.run(f"nmake /f makefile PLATFORM={self._msvc_platform}")
        else:
            autotools = Autotools(self)
            with chdir(self, os.path.join(self.source_folder, "CPP", "7zip", "Bundles", "LzmaCon")):
                autotools.make(args=["-f", "makefile.gcc"], target="all")

    def package(self):
        copy(self, "License.txt", dst=os.path.join(self.package_folder, "licenses"), src=os.path.join(self.source_folder, "DOC"))
        copy(self, "unRarLicense.txt", dst=os.path.join(self.package_folder, "licenses"), src=os.path.join(self.source_folder, "DOC"))
        if self.settings.os == "Windows":
            copy(self, "*.exe", os.path.join(self.source_folder, "CPP", "7zip"), os.path.join(self.package_folder, "bin"), keep_path=False)
            copy(self, "*.dll", os.path.join(self.source_folder, "CPP", "7zip"), os.path.join(self.package_folder, "bin"), keep_path=False)
        # TODO: Package the libraries: binaries and headers (add the rest of settings)

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
