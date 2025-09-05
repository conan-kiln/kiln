import os

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import stdcpp_library
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import check_min_vs, is_msvc, MSBuild, MSBuildToolchain
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class ZimgConan(ConanFile):
    name = "zimg"
    description = "Scaling, colorspace conversion, and dithering library"
    license = "WTFPL"
    homepage = "https://github.com/sekrit-twc/zimg"
    topics = ("image", "manipulation")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    @property
    def _msbuild_configuration(self):
        return "Debug" if self.settings.build_type == "Debug" else "Release"

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        check_min_vs(self, 191)

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

    def generate(self):
        if is_msvc(self):
            tc = MSBuildToolchain(self)
            tc.configuration = self._msbuild_configuration
            tc.properties["WholeProgramOptimization"] = "false"
            tc.generate()
        else:
            VirtualBuildEnv(self).generate()
            tc = AutotoolsToolchain(self)
            tc.generate()

    def build(self):
        if is_msvc(self):
            #==========================
            # TODO: to remove once https://github.com/conan-io/conan/pull/12817 available in conan client
            vcxproj_files = [
                os.path.join(self.source_folder, "_msvc", "zimg", "zimg.vcxproj"),
                os.path.join(self.source_folder, "_msvc", "dll", "dll.vcxproj"),
            ]
            for vcxproj_file in vcxproj_files:
                replace_in_file(
                    self, vcxproj_file,
                    "<WholeProgramOptimization>true</WholeProgramOptimization>",
                    ""
                )
            platform_toolset = MSBuildToolchain(self).toolset
            conantoolchain_props = os.path.join(self.generators_folder, MSBuildToolchain.filename)
            for vcxproj_file in vcxproj_files:
                if Version(self.version) >= "3.0.5":
                    replace_in_file(
                        self, vcxproj_file,
                        "<PlatformToolset>v143</PlatformToolset>",
                        f"<PlatformToolset>{platform_toolset}</PlatformToolset>",
                    )
                else:
                    replace_in_file(
                        self, vcxproj_file,
                        "<PlatformToolset>v142</PlatformToolset>",
                        f"<PlatformToolset>{platform_toolset}</PlatformToolset>",
                    )
                replace_in_file(
                    self, vcxproj_file,
                    "<Import Project=\"$(VCTargetsPath)\\Microsoft.Cpp.targets\" />",
                    f"<Import Project=\"{conantoolchain_props}\" /><Import Project=\"$(VCTargetsPath)\\Microsoft.Cpp.targets\" />",
                )
            #==========================

            msbuild = MSBuild(self)
            msbuild.build_type = self._msbuild_configuration
            msbuild.platform = "Win32" if self.settings.arch == "x86" else msbuild.platform
            msbuild.build(os.path.join(self.source_folder, "_msvc", "zimg.sln"),
                          targets=["dll" if self.options.shared else "zimg"])
        else:
            autotools = Autotools(self)
            autotools.autoreconf()
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        if is_msvc(self):
            src_include_dir = os.path.join(self.source_folder, "src", "zimg", "api")
            copy(self, "zimg.h", src=src_include_dir, dst=os.path.join(self.package_folder, "include"))
            copy(self, "zimg++.hpp", src=src_include_dir, dst=os.path.join(self.package_folder, "include"))
            output_dir = os.path.join(self.source_folder, "_msvc")
            copy(self, "*.lib", src=output_dir, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
            copy(self, "*.dll", src=output_dir, dst=os.path.join(self.package_folder, "bin"), keep_path=False)
            old_lib = "z_imp.lib" if self.options.shared else "z.lib"
            rename(self, os.path.join(self.package_folder, "lib", old_lib),
                         os.path.join(self.package_folder, "lib", "zimg.lib"))
        else:
            autotools = Autotools(self)
            autotools.install()
            rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
            rmdir(self, os.path.join(self.package_folder, "share"))
            rm(self, "*.la", os.path.join(self.package_folder, "lib"))
            fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "zimg")
        self.cpp_info.libs = ["zimg"]
        if not self.options.shared:
            if self.settings.os in ("FreeBSD", "Linux"):
                self.cpp_info.system_libs.append("m")
            libcxx = stdcpp_library(self)
            if libcxx:
                self.cpp_info.system_libs.append(libcxx)
