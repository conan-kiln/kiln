import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import cross_building
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson, MesonToolchain

required_conan_version = ">=2.1"


class PulseAudioConan(ConanFile):
    name = "pulseaudio"
    description = "PulseAudio is a sound system for POSIX OSes, meaning that it is a proxy for sound applications."
    topics = ("sound", "audio", "sound-server")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://pulseaudio.org/"
    license = "LGPL-2.1"

    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "i18n": [True, False],
        "with_glib": [True, False],
        "with_fftw": [True, False],
        "with_x11": [True, False],
        "with_openssl": [True, False],
        "with_dbus": [True, False],
    }
    default_options = {
        "i18n": False,
        "with_glib": True,
        "with_fftw": False,
        "with_x11": True,
        "with_openssl": True,
        "with_dbus": False,
    }

    def config_options(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            del self.options.with_x11

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if not self.options.with_dbus:
            del self.options.with_fftw

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("libiconv/[^1.17]")
        self.requires("libsndfile/[^1.2.2]")
        if self.settings.os != "Linux":
            self.requires("gettext/[>=0.21 <1]")
        if self.options.with_glib:
            self.requires("glib/[^2.70.0]")
        if self.options.get_safe("with_fftw"):
            self.requires("fftw/[^3.3.10]")
        if self.options.get_safe("with_x11"):
            self.requires("xorg/system")
        if self.options.with_openssl:
            self.requires("openssl/[>=1.1 <4]")
        if self.options.with_dbus:
            self.requires("dbus/[^1.15]")

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration(f"{self.ref} recipe is only compatible with Linux right now. Contributions are welcome.")

        if self.options.get_safe("with_fftw"):
            if not self.dependencies["fftw"].options.precision_single:
                raise ConanInvalidConfiguration(
                     "Pulse audio uses fftw single precision. "
                     "Either set option -o fftw/*:precision_single=True or -o pulseaudio/*:with_fftw=False"
                )

    def build_requirements(self):
        self.tool_requires("m4/1.4.19")
        self.tool_requires("meson/[>=1.2.3 <2]")
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        if self.options.i18n:
            self.tool_requires("gettext/[>=0.21 <1]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if not cross_building(self):
            env = VirtualRunEnv(self)
            env.generate(scope="build")

        def feature(val):
            return "enabled" if val else "disabled"

        tc = MesonToolchain(self)
        tc.project_options["auto_features"] = "enabled"
        tc.project_options["udevrulesdir"] = "${prefix}/bin/udev/rules.d"
        tc.project_options["systemduserunitdir"] = os.path.join(self.build_folder, "ignore")
        tc.project_options["database"] = "simple"
        tc.project_options["tests"] = False
        tc.project_options["man"] = False
        tc.project_options["doxygen"] = False
        tc.project_options["daemon"] = False
        tc.project_options["alsa"] = "disabled"
        tc.project_options["asyncns"] = "disabled"
        tc.project_options["avahi"] = "disabled"
        tc.project_options["bluez5"] = "disabled"
        tc.project_options["bluez5-gstreamer"] = "disabled"
        tc.project_options["consolekit"] = "disabled"
        tc.project_options["dbus"] = feature(self.options.with_dbus)
        tc.project_options["elogind"] = "disabled"
        tc.project_options["fftw"] = feature(self.options.get_safe("with_fftw"))
        tc.project_options["glib"] = feature(self.options.with_glib)
        tc.project_options["gsettings"] = "disabled"
        tc.project_options["gstreamer"] = "disabled"
        tc.project_options["gtk"] = "disabled"
        tc.project_options["jack"] = "disabled"
        tc.project_options["lirc"] = "disabled"
        tc.project_options["openssl"] = feature(self.options.with_openssl)
        tc.project_options["orc"] = "disabled"
        tc.project_options["oss-output"] = "disabled"
        tc.project_options["soxr"] = "disabled"
        tc.project_options["speex"] = "disabled"
        tc.project_options["systemd"] = "disabled"
        tc.project_options["tcpwrap"] = "disabled"
        tc.project_options["udev"] = "disabled"
        tc.project_options["valgrind"] = "disabled"
        tc.project_options["webrtc-aec"] = "disabled"
        tc.project_options["x11"] = feature(self.options.get_safe("with_x11"))
        tc.generate()

        pkg = PkgConfigDeps(self)
        pkg.generate()

    def build(self):
        if not self.options.i18n:
            save(self, os.path.join(self.source_folder, "po", "meson.build"), "")
        meson = Meson(self)
        meson.configure()
        meson.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        meson = Meson(self)
        meson.install()
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share", "bash-completion"))
        rmdir(self, os.path.join(self.package_folder, "share", "zsh"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"), recursive=True)

    def package_info(self):
        self.cpp_info.components["pulse"].set_property("pkg_config_name", "libpulse")
        self.cpp_info.components["pulse"].set_property("cmake_file_name", "PulseAudio")
        self.cpp_info.components["pulse"].set_property("cmake_additional_variables_prefixes", "PULSEAUDIO")
        self.cpp_info.components["pulse"].libs = ["pulse", f"pulsecommon-{self.version}"]
        self.cpp_info.components["pulse"].libdirs.append(os.path.join("lib", "pulseaudio"))
        self.cpp_info.components["pulse"].resdirs = ["share"]
        self.cpp_info.components["pulse"].requires = ["libiconv::libiconv", "libsndfile::libsndfile"]
        if self.settings.os != "Linux":
            self.cpp_info.components["pulse"].requires.append("gettext::gettext")
        if self.options.get_safe("with_fftw"):
            self.cpp_info.components["pulse"].requires.append("fftw::fftw")
        if self.options.get_safe("with_x11"):
            self.cpp_info.components["pulse"].requires.append("xorg::x11")
        if self.options.with_openssl:
            self.cpp_info.components["pulse"].requires.append("openssl::openssl")
        if self.options.with_dbus:
            self.cpp_info.components["pulse"].requires.append("dbus::dbus")

        self.cpp_info.components["pulse-simple"].set_property("pkg_config_name", "libpulse-simple")
        self.cpp_info.components["pulse-simple"].libs = ["pulse-simple"]
        self.cpp_info.components["pulse-simple"].defines.append("_REENTRANT")
        self.cpp_info.components["pulse-simple"].requires = ["pulse"]

        if self.options.with_glib:
            self.cpp_info.components["pulse-mainloop-glib"].set_property("pkg_config_name", "libpulse-mainloop-glib")
            self.cpp_info.components["pulse-mainloop-glib"].libs = ["pulse-mainloop-glib"]
            self.cpp_info.components["pulse-mainloop-glib"].defines.append("_REENTRANT")
            self.cpp_info.components["pulse-mainloop-glib"].requires = ["pulse", "glib::glib-2.0"]
