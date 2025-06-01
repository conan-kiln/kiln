import os
import textwrap

from conan import ConanFile
from conan.tools.build import check_min_cppstd, valid_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class mFASTConan(ConanFile):
    name = "mfast"
    description = (
        "mFAST is a high performance C++ encoding/decoding library for FAST "
        "(FIX Adapted for STreaming) protocol"
    )
    license = "LGPL-3.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://objectcomputing.github.io/mFAST/"
    topics = ("fast", "fix", "fix-adapted-for-streaming",
              "financial-information-exchange", "libraries", "cpp")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_sqlite3": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_sqlite3": False,
    }
    implements = ["auto_shared_fpic"]

    @property
    def _min_cppstd(self):
        return "14" if Version(self.version) >= "1.2.2" else "98"

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # transitive_headers=True because mfast/mfast_export.h includes boost/config.hpp
        self.requires("boost/[^1.71.0 <1.78]", transitive_headers=True)
        self.requires("tinyxml2/[^9.0.0]")
        if self.options.with_sqlite3:
            self.requires("sqlite3/[>=3.43 <4]")

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTS"] = False
        tc.variables["BUILD_EXAMPLES"] = False
        tc.variables["BUILD_PACKAGES"] = False
        tc.variables["BUILD_SQLITE3"] = self.options.with_sqlite3
        if not valid_min_cppstd(self, self._min_cppstd):
            tc.variables["CMAKE_CXX_STANDARD"] = self._min_cppstd
        if Version(self.version) <= "1.2.2":
            # Relocatable shared libs on macOS
            tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
            tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.5" # CMake 4 support
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "licence.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        mkdir(self, os.path.join(self.package_folder, self._new_mfast_config_dir))
        self._extract_fasttypegentarget_macro()
        rmdir(self, os.path.join(self.package_folder, self._old_mfast_config_dir))
        rmdir(self, os.path.join(self.package_folder, "share"))
        if self.options.shared:
            rm(self, "*_static*" if self.settings.os == "Windows" else "*.a", os.path.join(self.package_folder, "lib"))

        # TODO: several CMake variables should also be emulated (casing issues):
        #       [ ] MFAST_INCLUDE_DIR         - include directories for mFAST
        #       [ ] MFAST_LIBRARY_DIRS        - library directories for mFAST
        #       [ ] MFAST_LIBRARIES           - libraries to link against
        #       [ ] MFAST_COMPONENTS          - installed components
        #       [ ] MFAST_<component>_LIBRARY - particular component library
        #       [x] MFAST_EXECUTABLE          - the fast_type_gen executable => done in _prepend_exec_target_in_fasttypegentarget()
        self._prepend_exec_target_in_fasttypegentarget()

    @property
    def _new_mfast_config_dir(self):
        return os.path.join("lib", "cmake")

    @property
    def _old_mfast_config_dir(self):
        return "CMake" if self.settings.os == "Windows" else os.path.join("lib", "cmake", "mFAST")

    @property
    def _fast_type_gen_target_file(self):
        return os.path.join(self._new_mfast_config_dir, "FastTypeGenTarget.cmake")

    def _extract_fasttypegentarget_macro(self):
        if Version(self.version) < "1.2.2":
            config_file_content = load(self, os.path.join(self.package_folder, self._old_mfast_config_dir, "mFASTConfig.cmake"))
            begin = config_file_content.find("macro(FASTTYPEGEN_TARGET Name)")
            end = config_file_content.find("endmacro()", begin) + len("endmacro()")
            macro_str = config_file_content[begin:end]
            save(self, os.path.join(self.package_folder, self._fast_type_gen_target_file), macro_str)
        else:
            rename(self, os.path.join(self.package_folder, self._old_mfast_config_dir, "FastTypeGenTarget.cmake"),
                         os.path.join(self.package_folder, self._fast_type_gen_target_file))

    def _prepend_exec_target_in_fasttypegentarget(self):
        exec_target_content = textwrap.dedent(f"""\
            if(NOT TARGET fast_type_gen)
                find_program(MFAST_EXECUTABLE NAMES fast_type_gen PATHS ENV PATH NO_DEFAULT_PATH)
                add_executable(fast_type_gen IMPORTED)
                set_property(TARGET fast_type_gen PROPERTY IMPORTED_LOCATION ${{MFAST_EXECUTABLE}})
            endif()
        """)
        module_abs_path = os.path.join(self.package_folder, self._fast_type_gen_target_file)
        old_content = load(self, module_abs_path)
        new_content = exec_target_content + old_content
        save(self, module_abs_path, new_content)

    @property
    def _mfast_lib_components(self):
        target_suffix = "_static" if not self.options.shared else ""
        lib_suffix = "_static" if self.settings.os == "Windows" and not self.options.shared else ""
        components = {
            "libmfast": {
                "comp": "mfast",
                "target": "mfast" + target_suffix,
                "lib": "mfast" + lib_suffix,
                "requires": ["boost::headers"],
            },
            "mfast_coder": {
                "comp": "mfast_coder",
                "target": "mfast_coder" + target_suffix,
                "lib": "mfast_coder" + lib_suffix,
                "requires": ["libmfast", "boost::headers"],
            },
            "mfast_xml_parser": {
                "comp": "mfast_xml_parser",
                "target": "mfast_xml_parser" + target_suffix,
                "lib": "mfast_xml_parser" + lib_suffix,
                "requires": ["libmfast", "boost::headers", "tinyxml2::tinyxml2"],
            },
            "mfast_json": {
                "comp": "mfast_json",
                "target": "mfast_json" + target_suffix,
                "lib": "mfast_json" + lib_suffix,
                "requires": ["libmfast", "boost::headers"],
            },
        }
        if self.options.with_sqlite3:
            components.update({
                "mfast_sqlite3": {
                    "comp": "mfast_sqlite3",
                    "target": "mfast_sqlite3" + target_suffix,
                    "lib": "mfast_sqlite3" + lib_suffix,
                    "requires": ["libmfast", "boost::headers", "sqlite3::sqlite3"],
                },
            })
        return components

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "mFAST")
        self.cpp_info.set_property("cmake_build_modules", [self._fast_type_gen_target_file])

        for conan_comp, values in self._mfast_lib_components.items():
            target = values["target"]
            comp = values["comp"]
            lib = values["lib"]
            requires = values["requires"]
            self.cpp_info.components[conan_comp].set_property("cmake_target_name", target)
            if comp != target:
                # Also provide alias component for find_package(mFAST COMPONENTS ...) if static
                self.cpp_info.components[conan_comp].set_property("cmake_target_aliases", [comp])
            if self.settings.os in ("FreeBSD", "Linux"):
                self.cpp_info.components[conan_comp].system_libs.append("m")
            self.cpp_info.components[conan_comp].libs = [lib]
            self.cpp_info.components[conan_comp].requires = requires
            if self.options.shared:
                self.cpp_info.components[conan_comp].defines = ["MFAST_DYN_LINK"]
