import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class TaskflowConan(ConanFile):
    name = "taskflow"
    description = (
        "A fast C++ header-only library to help you quickly write parallel "
        "programs with complex task dependencies."
    )
    license = "MIT"
    homepage = "https://github.com/taskflow/taskflow"
    topics = ("tasking", "parallelism", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*",
                  src=os.path.join(self.source_folder, "taskflow"),
                  dst=os.path.join(self.package_folder, "include", "taskflow"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Taskflow")
        self.cpp_info.set_property("cmake_target_name", "Taskflow::Taskflow")

        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
        if is_msvc(self):
            self.cpp_info.defines = ["_ENABLE_EXTENDED_ALIGNED_STORAGE"]
