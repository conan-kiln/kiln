import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, cross_building
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class AmplMpConan(ConanFile):
    name = "ampl-mp"
    description = ("AMPL/MP library is a set of solver drivers and tools to create and use with new AMPL solver drivers."
                   " It provides type-safe and flexible interfaces suitable for linear and mixed-integer, non-linear, and Constraint Programming solvers.")
    license = "SMLNJ"
    homepage = "https://github.com/ampl/mp"
    topics = ("optimization", "ampl", "solver-drivers")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_nlw2": [True, False],
        # Solver backends
        "cbcmp": [True, False],
        "cplex": [True, False],
        "cplexodh": [True, False],
        "cuoptmp": [True, False],
        "gcgmp": [True, False],
        "gurobi": [True, False],
        "gurobi_ampls": [True, False],
        "gurobiodh": [True, False],
        "highsmp": [True, False],
        "ilogcp": [True, False],
        "mosek": [True, False],
        "mp2nl": [True, False],
        "ortoolsmp": [True, False],
        "scipmp": [True, False],
        "smpswriter": [True, False],
        "visitor": [True, False],
        "xpress": [True, False],
        # "baronmp": [True, False],
        # "copt": [True, False],
        # "gecode": [True, False],
        # "jacop": [True, False],
        # "localsolver": [True, False],
        # "sulum": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_nlw2": True,
        # Solver backends
        "cbcmp": False,
        "cplex": False,
        "cplexodh": False,
        "cuoptmp": False,
        "gcgmp": False,
        "gurobi": False,
        "gurobi_ampls": False,
        "gurobiodh": False,
        "highsmp": False,
        "ilogcp": False,
        "mosek": False,
        "mp2nl": False,
        "ortoolsmp": False,
        "scipmp": False,
        "smpswriter": False,
        "visitor": False,
        "xpress": False,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.options.mp2nl:
            self.options.build_nlw2.value = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("gch-small-vector/[*]", transitive_headers=True)

        if self.options.cbcmp:
            self.requires("coin-cbc/[^2.10]")
        if self.options.cuoptmp:
            self.requires("cuopt/[*]")
        if self.options.highsmp:
            self.requires("highs/[^1.0]")
        if self.options.ortoolsmp:
            self.requires("or-tools/[>=9.0]")
        if self.options.scipmp or self.options.gcgmp:
            self.requires("scip/[>=7.0]")
        if self.options.cplex or self.options.cplexodh or self.options.ilogcp:
            self.requires("cplex/[*]")
        if self.options.gurobi or self.options.gurobi_ampls or self.options.gurobiodh:
            self.requires("gurobi/[*]")
        if self.options.mosek:
            self.requires("mosek/[*]")
        if self.options.xpress:
            self.requires("xpress/[*]")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Unvendor
        rmdir(self, "thirdparty")
        replace_in_file(self, "include/mp/utils-vec.h", "../../thirdparty/gharveymn/small_vector/small_vector.hpp", "gch/small_vector.hpp")
        # Don't try to build cplex
        replace_in_file(self, "solvers/CMakeLists.txt", "check_module(cplex build_cplex)", "")
        # Fix a minor incompatibility
        replace_in_file(self, "solvers/mosek/mosekcommon.cc", "int64_t value = 0;", "MSKint64t value = 0;")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_MP_INCLUDE"] = "conan_deps.cmake"
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["BUILD_EXAMPLES"] = False
        tc.cache_variables["BUILD_DOC"] = False
        tc.cache_variables["BUILD_TESTS"] = False
        tc.cache_variables["MP_CROSSCOMPILING"] = cross_building(self)
        tc.cache_variables["NLW2_LIB"] = self.options.build_nlw2
        tc.cache_variables["BUILD"] = ",".join(solver for solver in ALL_BACKENDS if self.options.get_safe(solver))
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("cplex", "cmake_file_name", "CPLEX")
        deps.set_property("mosek", "cmake_file_name", "MOSEK")
        deps.set_property("coin-cbc", "cmake_file_name", "CBC")
        deps.set_property("scip", "cmake_file_name", "SCIP")
        deps.set_property("highs", "cmake_file_name", "HIGHS")
        deps.set_property("or-tools", "cmake_file_name", "ortoolsmp")
        deps.set_property("xpress", "cmake_file_name", "XPRESS")
        deps.set_property("gurobi", "cmake_file_name", "GUROBI")
        deps.set_property("cuopt", "cmake_file_name", "CUOPT")
        deps.set_property("cplex::cplex_", "cmake_target_aliases", ["cplex-library"])
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "share"))

    def package_info(self):
        self.cpp_info.components["mp"].libs = ["mp"]
        self.cpp_info.components["mp"].requires = ["gch-small-vector::gch-small-vector"]

        tool_requires = []
        if self.options.cbcmp:
            tool_requires.append("coin-cbc::coin-cbc")
        if self.options.cuoptmp:
            tool_requires.append("cuopt::cuopt")
        if self.options.highsmp:
            tool_requires.append("highs::highs")
        if self.options.ortoolsmp:
            tool_requires.append("or-tools::or-tools")
        if self.options.scipmp or self.options.gcgmp:
            tool_requires.append("scip::scip")
        if self.options.cplex or self.options.cplexodh or self.options.ilogcp:
            tool_requires.append("cplex::cplex")
        if self.options.gurobi or self.options.gurobi_ampls or self.options.gurobiodh:
            tool_requires.append("gurobi::gurobi")
        if self.options.mosek:
            tool_requires.append("mosek::mosek")
        if self.options.xpress:
            tool_requires.append("xpress::xpress")
        self.cpp_info.components["_backend_executables"].requires = tool_requires

ALL_BACKENDS = [
    "baronmp",
    "cbcmp",
    "copt",
    "cplex",
    "cplexodh",
    "cuoptmp",
    "gcgmp",
    "gecode",
    "gurobi",
    "gurobi_ampls",
    "gurobiodh",
    "highsmp",
    "ilogcp",
    "jacop",
    "localsolver",
    "mosek",
    "mp2nl",
    "ortoolsmp",
    "scipmp",
    "smpswriter",
    "sulum",
    "visitor",
    "xpress",
]
