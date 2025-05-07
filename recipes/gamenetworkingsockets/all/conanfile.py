import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.gnu import PkgConfigDeps

required_conan_version = ">=2.1"


class GameNetworkingSocketsConan(ConanFile):
    name = "gamenetworkingsockets"
    description = "GameNetworkingSockets is a basic transport layer for games."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ValveSoftware/GameNetworkingSockets"
    topics = ("networking", "game-development")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "encryption": ["openssl", "libsodium", "bcrypt"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "encryption": "openssl",
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("protobuf/[>=3.21.12]")
        if self.options.encryption == "openssl":
            self.requires("openssl/[>=1.1 <4]")
        elif self.options.encryption == "libsodium":
            self.requires("libsodium/[^1.0.20]")

    def validate(self):
        check_min_cppstd(self, 11)
        if self.options.encryption == "bcrypt" and self.settings.os != "Windows":
            raise ConanInvalidConfiguration("bcrypt is only valid on Windows")

    def build_requirements(self):
        self.tool_requires("protobuf/<host_version>")
        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Let Conan set the C++ standard
        replace_in_file(self, "CMakeLists.txt", "CXX_STANDARD 11", "FOLDER xyz")
        replace_in_file(self, os.path.join("src", "external", "steamwebrtc", "CMakeLists.txt"), "CXX_STANDARD 14", "FOLDER xyz")
        # Disable MSVC runtime override
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"), "configure_msvc_runtime()", "")
        # Add support for Protobuf v30, which returns std::string_view instead of std::string
        replace_in_file(self, "src/steamnetworkingsockets/steamnetworkingsockets_internal.h",
                        "msg.GetTypeName().c_str()",
                        "std::string(msg.GetTypeName()).c_str()")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["GAMENETWORKINGSOCKETS_BUILD_EXAMPLES"] = False
        tc.variables["GAMENETWORKINGSOCKETS_BUILD_TESTS"] = False
        tc.variables["Protobuf_USE_STATIC_LIBS"] = not self.dependencies["protobuf"].options.shared
        tc.variables["Protobuf_IMPORT_DIRS"] = os.path.join(self.source_folder, "src", "common").replace("\\", "/")
        crypto = {
            "openssl": "OpenSSL",
            "libsodium": "libsodium",
            "bcrypt": "BCrypt",
        }
        tc.variables["USE_CRYPTO"] = crypto[str(self.options.encryption)]
        crypto25519 = {
            "openssl": "OpenSSL",
            "libsodium": "libsodium",
            "bcrypt": "Reference",
        }
        tc.variables["USE_CRYPTO25519"] = crypto25519[str(self.options.encryption)]
        if self.options.encryption == "openssl":
            tc.variables["OPENSSL_NEW_ENOUGH"] = True
            tc.variables["OPENSSL_HAS_25519_RAW"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        deps = PkgConfigDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "GameNetworkingSockets")
        self.cpp_info.set_property("cmake_target_name", "GameNetworkingSockets::GameNetworkingSockets")
        self.cpp_info.set_property("pkg_config_name", "GameNetworkingSockets")
        self.cpp_info.includedirs.append(os.path.join("include", "GameNetworkingSockets"))
        if self.options.shared:
            self.cpp_info.libs = ["GameNetworkingSockets"]
        else:
            self.cpp_info.libs = ["GameNetworkingSockets_s"]
            self.cpp_info.defines = ["STEAMNETWORKINGSOCKETS_STATIC_LINK"]

        self.cpp_info.requires = ["protobuf::libprotobuf"]
        if self.options.encryption == "openssl":
            self.cpp_info.requires += ["openssl::crypto"]
        elif self.options.encryption == "libsodium":
            self.cpp_info.requires += ["libsodium::libsodium"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32", "crypt32", "winmm", "iphlpapi"]
            if self.options.encryption == "bcrypt":
                self.cpp_info.system_libs += ["bcrypt"]
