import json
import os
import re
import textwrap
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.build import check_min_cppstd, can_run
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class ClangConan(ConanFile):
    name = "clang"
    description = "The Clang project provides a language front-end and tooling infrastructure for languages in the C language family"
    license = "Apache-2 with LLVM-exception"
    homepage = "https://clang.llvm.org/"
    topics = ("clang", "llvm", "compiler")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    no_copy_source = True

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"llvm-core/{self.version}", transitive_headers=True, transitive_libs=True)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.20 <5]")
        # needed to build c-index-test but not actually required by any components
        self.test_requires("libxml2/[^2.12.5]")
        # llvm-tblgen
        if not can_run(self):
            self.tool_requires("llvm-core/<host_version>")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        sources = self.conan_data["sources"][self.version]
        get(self, **sources["clang"], destination="clang", strip_root=True)
        get(self, **sources["cmake"], destination="cmake", strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        if can_run(self):
            # for llvm-tblgen
            VirtualRunEnv(self).generate(scope="build")
        tc = CMakeToolchain(self)
        tc.cache_variables["LLVM_INCLUDE_TESTS"] = False
        tc.cache_variables["LLVM_BUILD_TOOLS"] = True
        tc.cache_variables["LLVM_BUILD_UTILS"] = True
        tc.cache_variables["LINKER_SUPPORTS_COLOR_DIAGNOSTICS"] = False  # breaks with mold
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    @property
    def _source_path(self):
        return Path(self.source_folder) / "clang"

    @property
    def _graphviz_file(self):
        return Path(self.build_folder) / "clang.dot"

    def _validate_components(self, components):
        for component, info in components.items():
            if not component.startswith("clang") and component != "libclang":
                raise ConanException(f"Unexpected component: {component}")
            for req in info["requires"]:
                if not req.startswith("clang"):
                    dep = req.split("::", 1)[0]
                    if dep not in self.dependencies.direct_host:
                        raise ConanException(f"Unexpected dependency for {component}: {req}")

    @cached_property
    def _clang_build_info(self):
        return {
            "components": components_from_dotfile(self._graphviz_file.read_text()),
        }

    def _write_build_info(self, path):
        Path(path).write_text(json.dumps(self._clang_build_info, indent=2))

    def _read_build_info(self) -> dict:
        return json.loads(self._build_info_file.read_text())

    def build(self):
        cmake = CMake(self)
        graphviz_args = [f"--graphviz={self._graphviz_file}"]

        # components not exported or not of interest
        exclude_patterns = [
            "CONAN_LIB*",
            "llvm-core*",
            # The *-resource-headers targets are not exported by the official ClangConfig.cmake.
            ".+-resource-headers",
        ]
        save(self, Path(self.build_folder) / "CMakeGraphVizOptions.cmake", textwrap.dedent(f"""
            set(GRAPHVIZ_EXECUTABLES OFF)
            set(GRAPHVIZ_MODULE_LIBS OFF)
            set(GRAPHVIZ_OBJECT_LIBS OFF)
            set(GRAPHVIZ_IGNORE_TARGETS "{';'.join(exclude_patterns)}")
        """))
        cmake.configure(build_script_folder="clang", cli_args=graphviz_args)
        self._write_build_info(self._build_info_file.name)
        self._validate_components(self._clang_build_info["components"])
        cmake.build()

    @property
    def _package_path(self):
        return Path(self.package_folder)

    @property
    def _cmake_module_path(self):
        return Path("lib") / "cmake" / "clang"

    @property
    def _build_info_file(self):
        return self._package_path / self._cmake_module_path / "conan_clang_build_info.json"

    def package(self):
        copy(self, "LICENSE.TXT", self._source_path, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        # Back up original cmake files for debugging purposes
        package_folder = Path(self.package_folder)
        cmake_dir = package_folder / self._cmake_module_path
        copy(self, "*", cmake_dir, os.path.join(self.package_folder, "share", "conan", self.name, "cmake_original"))

        self._write_build_info(self._build_info_file)

        rm(self, "ClangConfigVersion.cmake", cmake_dir)
        rm(self, "ClangTargets*", cmake_dir)
        rename(self,
               cmake_dir / "ClangConfig.cmake",
               cmake_dir / "ClangConfigVars.cmake")
        replace_in_file(self, cmake_dir / "ClangConfigVars.cmake",
                        'include("${CLANG_CMAKE_DIR}/ClangTargets.cmake")',
                        '# include("${CLANG_CMAKE_DIR}/ClangTargets.cmake")')

        self._write_export_executables_cmake(cmake_dir / "conan_add_executable_targets.cmake")

        rmdir(self, package_folder / "share" / "man")

    def _write_export_executables_cmake(self, cmake_file_path):
        bin_dir = Path(self.package_folder, "bin")
        content = 'get_filename_component(_IMPORT_PREFIX "${CMAKE_CURRENT_LIST_DIR}/../../.." ABSOLUTE)\n\n'
        content += "\n".join(
            f"if(NOT TARGET {x.stem})\n"
            f"  add_executable({x.stem} IMPORTED)\n"
            f'  set_target_properties({x.stem} PROPERTIES IMPORTED_LOCATION "${{_IMPORT_PREFIX}}/bin/{x.name}")\n'
            "endif()\n"
            for x in sorted(bin_dir.iterdir()) if x.suffix not in {".dll", ".pdb"}
        )
        save(self, cmake_file_path, content)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Clang")

        build_info = self._read_build_info()
        components = build_info["components"]
        for name, data in components.items():
            component = self.cpp_info.components[name]
            component.set_property("cmake_target_name", name)
            lib_name = "clang" if name == "libclang" else name
            component.libs = [lib_name]
            component.builddirs.append(self._cmake_module_path)
            component.requires = data["requires"]
            component.system_libs = data["system_libs"]
            if not self.dependencies["llvm-core"].options.rtti:
                no_rtti_flag = "/GR-" if is_msvc(self) else "-fno-rtti"
                component.cxxflags.append(no_rtti_flag)

        self.cpp_info.builddirs.append(self._cmake_module_path)
        self.cpp_info.set_property("cmake_build_modules", [
            self._cmake_module_path / "ClangConfigVars.cmake",
            self._cmake_module_path / "conan_add_executable_targets.cmake",
        ])


def parse_dotfile(dotfile, label_replacements=None):
    """
    Load the dependency graph defined by the nodes and edges in a dotfile.
    """
    label_replacements = label_replacements or {}
    labels = {}
    for node, label in re.findall(r'^\s*"(node\d+)"\s*\[\s*label\s*=\s*"(.+?)"', dotfile, re.MULTILINE):
        labels[node] = label_replacements.get(label, label)
    components = {l: [] for l in labels.values()}
    for src, dst in re.findall(r'^\s*"(node\d+)"\s*->\s*"(node\d+)"', dotfile, re.MULTILINE):
        components[labels[src]].append(labels[dst])
    return components


def components_from_dotfile(dotfile):
    """
    Parse the dotfile generated by the
    [cmake --graphviz](https://cmake.org/cmake/help/latest/module/CMakeGraphVizOptions.html)
    option to generate the list of available LLVM CMake targets and their inter-component dependencies.

    In future a [CPS](https://cps-org.github.io/cps/index.html) format could be used, or generated directly
    by the LLVM build system
    """
    known_system_libs = {
        "dl",
    }
    components = {}
    for component, deps in parse_dotfile(dotfile).items():
        if not component.startswith("clang") and component != "libclang":
            continue
        requires = []
        system_libs = []
        for dep in deps:
            if dep.startswith("LLVM"):
                dep = f"llvm-core::{dep}"
            if dep in known_system_libs:
                system_libs.append(dep)
            else:
                requires.append(dep)
        components[component] = {
            "requires": requires,
            "system_libs": system_libs,
        }
    return components
