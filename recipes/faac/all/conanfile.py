import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, MSBuild, MSBuildToolchain

required_conan_version = ">=2.4"


class FaacConan(ConanFile):
    name = "faac"
    description = "Freeware Advanced Audio Coder"
    license = "LGPL-2.0-only"
    homepage = "https://sourceforge.net/projects/faac"
    topics = ("audio", "mp4", "encoder", "aac", "m4a", "faac")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "drm": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "drm": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    @property
    def _is_mingw(self):
        return self.settings.os == "Windows" and self.settings.compiler == "gcc"

    @property
    def _msbuild_configuration(self):
        return "Debug" if self.settings.build_type == "Debug" else "Release"

    @property
    def _sln_folder(self):
        return os.path.join(self.source_folder, "project", "msvc")

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        # FIXME: libfaac depends on kissfft. Try to unvendor this dependency
        pass

    def validate(self):
        if is_msvc(self):
            if self.settings.arch not in ["x86", "x86_64"]:
                raise ConanInvalidConfiguration(f"{self.ref} only supports x86 and x86_64 with Visual Studio")
            if self.options.drm and not self.options.shared:
                raise ConanInvalidConfiguration(f"{self.ref} with drm support can't be built as static with Visual Studio")

    def build_requirements(self):
        if not is_msvc(self):
            self.tool_requires("libtool/[^2.4.7]")
            if self.settings_build.os == "Windows":
                self.win_bash = True
                if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                    self.tool_requires("msys2/latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # Don't constrain Windows SDK version
        for f in [
            "project/msvc/faac.vcxproj",
            "project/msvc/libfaac.vcxproj",
            "project/msvc/libfaac_dll.vcxproj",
            "project/msvc/libfaac_dll_drm.vcxproj",
        ]:
            replace_in_file(self, f, "<WindowsTargetPlatformVersion>10.0</WindowsTargetPlatformVersion>", "")

    def generate(self):
        if is_msvc(self):
            tc = MSBuildToolchain(self)
            tc.configuration = self._msbuild_configuration
            tc.generate()
        else:
            tc = AutotoolsToolchain(self)
            yes_no = lambda v: "yes" if v else "no"
            tc.configure_args.append(f"--enable-drm={yes_no(self.options.drm)}")
            tc.generate()

    def _patch_msvc(self):
        platform_toolset = MSBuildToolchain(self).toolset
        conantoolchain_props = os.path.join(self.generators_folder, MSBuildToolchain.filename)
        for vcxproj_file in ["faac.vcxproj", "libfaac.vcxproj", "libfaac_dll.vcxproj", "libfaac_dll_drm.vcxproj"]:
            replace_in_file(
                self, os.path.join(self._sln_folder, vcxproj_file),
                "<PlatformToolset>v142</PlatformToolset>",
                f"<PlatformToolset>{platform_toolset}</PlatformToolset>",
            )
            replace_in_file(
                self, os.path.join(self._sln_folder, vcxproj_file),
                '<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.targets" />',
                rf'<Import Project="{conantoolchain_props}" /><Import Project="$(VCTargetsPath)\Microsoft.Cpp.targets" />',
            )


    def build(self):
        if is_msvc(self):
            self._patch_msvc()
            msbuild = MSBuild(self)
            msbuild.build_type = self._msbuild_configuration
            msbuild.platform = "Win32" if self.settings.arch == "x86" else msbuild.platform
            targets = ["faac"]
            if self.options.drm:
                targets.append("libfaac_dll_drm")
            else:
                targets.append("libfaac_dll" if self.options.shared else "libfaac")
            msbuild.build(os.path.join(self._sln_folder, "faac.sln"), targets=targets)
        else:
            autotools = Autotools(self)
            autotools.autoreconf()
            autotools.configure()
            if self._is_mingw and self.options.shared:
                replace_in_file(self, os.path.join(self.build_folder, "libfaac", "Makefile"),
                                "\nlibfaac_la_LIBADD = ",
                                "\nlibfaac_la_LIBADD = -no-undefined ")
            autotools.make()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        if is_msvc(self):
            copy(self, "*.h", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
            output_folder = os.path.join(self._sln_folder, "bin", self._msbuild_configuration)
            copy(self, "*.exe", output_folder, os.path.join(self.package_folder, "bin"))
            copy(self, "*.dll", output_folder, os.path.join(self.package_folder, "bin"))
            lib_folder = os.path.join(self.package_folder, "lib")
            if self.options.shared:
                if self.options.drm:
                    old_libname = "libfaacdrm.lib"
                    new_libname = "faac_drm.lib"
                else:
                    old_libname = "libfaac_dll.lib"
                    new_libname = "faac.lib"
                copy(self, old_libname, output_folder, lib_folder)
                rename(self, os.path.join(lib_folder, old_libname), os.path.join(lib_folder, new_libname))
            else:
                copy(self, "*.lib", output_folder, lib_folder)
        else:
            autotools = Autotools(self)
            autotools.install()
            rmdir(self, os.path.join(self.package_folder, "share"))
            rm(self, "*.la", os.path.join(self.package_folder, "lib"))
            fix_apple_shared_install_name(self)

    def package_info(self):
        suffix = "_drm" if self.options.drm else ""
        self.cpp_info.libs = [f"faac{suffix}"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
