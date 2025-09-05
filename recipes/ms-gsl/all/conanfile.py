import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class MicrosoftGslConan(ConanFile):
    name = "ms-gsl"
    description = "Microsoft's implementation of the Guidelines Support Library"
    license = "MIT"
    homepage = "https://github.com/microsoft/GSL"
    topics = ("gsl", "guidelines", "core", "span", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "on_contract_violation": ["terminate", "throw", "unenforced"]
    }
    default_options = {
        "on_contract_violation": "terminate"
    }
    no_copy_source = True

    @property
    def _minimum_cpp_standard(self):
        return 14

    @property
    def _contract_map(self):
        return {
            "terminate": "GSL_TERMINATE_ON_CONTRACT_VIOLATION",
            "throw": "GSL_THROW_ON_CONTRACT_VIOLATION",
            "unenforced": "GSL_UNENFORCED_ON_CONTRACT_VIOLATION",
        }

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "5",
            "clang": "3.4",
            "apple-clang": "3.4",
            "msvc": "190",
        }

    def config_options(self):
        if Version(self.version) >= "3.0.0":
            del self.options.on_contract_violation

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, self._minimum_cpp_standard)

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._minimum_cpp_standard}, which your compiler does not fully support."
            )

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        pass

    def build(self):
        pass

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Microsoft.GSL")
        self.cpp_info.set_property("cmake_target_name", "Microsoft.GSL::GSL")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        if Version(self.version) < "3.0.0":
            self.cpp_info.defines = [
                self._contract_map[str(self.options.on_contract_violation)]
            ]
