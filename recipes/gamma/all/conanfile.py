import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class Gammaconan(ConanFile):
    name = "gamma"
    description = (
        "Gamma is a cross-platform, C++ library for doing generic synthesis "
        "and filtering of signals."
    )
    license = "MIT"
    topics = ("signal-processing", "sound", "audio")
    homepage = "https://github.com/LancePutnam/Gamma"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "audio_io": [True, False],
        "soundfile": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "audio_io": False,
        "soundfile": True,
    }
    implements = ["auto_shared_fpic"]

    exports_sources = "CMakeLists.txt"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.soundfile:
            self.requires("libsndfile/[^1.2.2]")

    def validate(self):
        check_min_cppstd(self, 14)

        if self.options.audio_io:
            # TODO: add audio_io support once portaudio added to CCI
            raise ConanInvalidConfiguration(
                "gamma:audio_io=True requires portaudio, not available in conan-center yet"
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["GAMMA_SRC_DIR"] = self.source_folder.replace("\\", "/")
        tc.variables["GAMMA_AUDIO_IO"] = self.options.audio_io
        tc.variables["GAMMA_SOUNDFILE"] = self.options.soundfile
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="..")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["Gamma"]
        if not self.options.shared and self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread"])
