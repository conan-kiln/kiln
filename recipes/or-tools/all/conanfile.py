import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class OrToolsConan(ConanFile):
    name = "or-tools"
    description = "OR-Tools is fast and portable software for combinatorial optimization"
    license = "Apache-2.0"
    homepage = "https://developers.google.com/optimization/"
    topics = ("optimization", "linear-programming", "operations-research", "combinatorial-optimization")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_flatzinc": [True, False],
        "build_bop": [True, False],
        "build_glop": [True, False],
        "build_pdlp": [True, False],
        "with_coinor": [True, False],
        "with_glpk": [True, False],
        "with_gurobi": [True, False],
        "with_highs": [True, False],
        "with_scip": [True, False],
        "with_cplex": [True, False],
        "with_xpress": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_flatzinc": True,
        "build_bop": True,
        "build_glop": True,
        "build_pdlp": True,
        "with_coinor": False,
        "with_glpk": False,
        "with_gurobi": False,
        "with_highs": True,
        "with_scip": False,
        "with_cplex": False,
        "with_xpress": False,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zlib-ng/[^2.0]")
        self.requires("bzip2/[^1.0.8]")
        self.requires("eigen/[>=3.3 <6]")
        self.requires("protobuf/[>=3.29.4]", transitive_headers=True, transitive_libs=True)
        self.requires("abseil/[>=20240116.2 <20250814.0]", transitive_headers=True, transitive_libs=True)
        self.requires("re2/[>=20220601]")
        if self.options.with_coinor:
            self.requires("coin-clp/[^1]", transitive_headers=True, transitive_libs=True)
            self.requires("coin-cbc/[^2]", transitive_headers=True, transitive_libs=True)
        if self.options.with_glpk:
            self.requires("glpk/[>=4 <6]", transitive_headers=True, transitive_libs=True)
        if self.options.with_gurobi:
            self.requires("gurobi/[*]", transitive_headers=True, transitive_libs=True)
        if self.options.with_highs:
            self.requires("highs/[^1]", transitive_headers=True, transitive_libs=True)
        if self.options.with_scip:
            self.requires("scip/[<10]", transitive_headers=True, transitive_libs=True)
        if self.options.with_cplex:
            self.requires("cplex/[*]", transitive_headers=True, transitive_libs=True)
        if self.options.with_xpress:
            self.requires("xpress/[*]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if is_msvc(self):
            check_min_cppstd(self, 20)
        else:
            check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.20]")
        self.tool_requires("protobuf/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # protoc is available from Conan when cross-compiling, no need to fetch and build it
        save(self, os.path.join(self.source_folder, "cmake", "host.cmake"), "")
        # Let Conan set the C++ standard
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD", "# set(CMAKE_CXX_STANDARD")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_FLATZINC"] = self.options.build_flatzinc
        tc.cache_variables["USE_BOP"] = self.options.build_bop
        tc.cache_variables["USE_GLOP"] = self.options.build_glop
        tc.cache_variables["USE_PDLP"] = self.options.build_pdlp
        tc.cache_variables["USE_COINOR"] = self.options.with_coinor
        tc.cache_variables["USE_GUROBI"] = True  # can't actually be disabled
        tc.cache_variables["USE_GLPK"] = self.options.with_glpk
        tc.cache_variables["USE_HIGHS"] = self.options.with_highs
        tc.cache_variables["USE_SCIP"] = self.options.with_scip
        tc.cache_variables["USE_CPLEX"] = self.options.with_cplex
        tc.cache_variables["USE_XPRESS"] = self.options.with_xpress
        protoc_path = os.path.join(self.dependencies.build["protobuf"].cpp_info.bindir, "protoc")
        tc.cache_variables["PROTOC_PRG"] = protoc_path.replace("\\", "/")
        tc.cache_variables["BUILD_DEPS"] = False
        tc.cache_variables["BUILD_SAMPLES"] = False
        tc.cache_variables["BUILD_EXAMPLES"] = False
        tc.cache_variables["BUILD_TESTING"] = False
        tc.generate()
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("coin-cbc", "cmake_file_name", "Cbc")
        deps.set_property("coin-cbc::solver", "cmake_target_name", "Coin::CbcSolver")
        deps.set_property("coin-cbc::solver", "cmake_target_aliases", ["Coin::Cbc"])
        deps.set_property("coin-cbc::osi-cbc", "cmake_target_name", "Coin::OsiCbc")
        deps.set_property("coin-clp", "cmake_file_name", "Clp")
        deps.set_property("coin-clp::solver", "cmake_target_name", "Coin::ClpSolver")
        deps.set_property("coin-clp::solver", "cmake_target_aliases", ["Coin::Clp"])
        deps.set_property("coin-clp::osi-clp", "cmake_target_name", "Coin::OsiClp")
        deps.set_property("coin-cgl", "cmake_file_name", "Cgl")
        deps.set_property("coin-cgl", "cmake_target_name", "Coin::Cgl")
        deps.set_property("coin-osi", "cmake_file_name", "Osi")
        deps.set_property("coin-osi", "cmake_target_name", "Coin::Osi")
        deps.set_property("coin-utils", "cmake_file_name", "CoinUtils")
        deps.set_property("coin-utils", "cmake_target_name", "Coin::CoinUtils")
        deps.set_property("cplex", "cmake_file_name", "CPLEX")
        deps.set_property("cplex", "cmake_target_name", "CPLEX::CPLEX")
        deps.set_property("glpk", "cmake_file_name", "GLPK")
        deps.set_property("glpk", "cmake_target_name", "GLPK::GLPK")
        deps.set_property("highs", "cmake_file_name", "HIGHS")
        deps.set_property("highs", "cmake_target_name", "highs::highs")
        deps.set_property("scip", "cmake_file_name", "SCIP")
        deps.set_property("scip", "cmake_target_name", "SCIP::libscip")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share", "doc"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ortools")

        self.cpp_info.components["core"].set_property("cmake_target_name", "ortools::ortools")
        self.cpp_info.components["core"].libs = ["ortools"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["core"].system_libs = ["m", "pthread", "dl"]
        self.cpp_info.components["core"].requires = [
            "zlib-ng::zlib-ng",
            "bzip2::bzip2",
            "eigen::eigen",
            "protobuf::protobuf",
            "abseil::abseil",
            "re2::re2",
        ]
        self.cpp_info.components["core"].defines.append("USE_MATH_OPT")
        if self.options.shared and self.settings.compiler == "msvc":
            self.cpp_info.components["core"].defines.append("OR_BUILD_DLL")
            self.cpp_info.components["core"].defines.append("OR_PROTO_DLL=__declspec(dllimport)")
        else:
            self.cpp_info.components["core"].defines.append("OR_PROTO_DLL=")
        if self.options.build_bop:
            self.cpp_info.components["core"].defines.append("USE_BOP")
        if self.options.build_glop:
            self.cpp_info.components["core"].defines.append("USE_GLOP")
        if self.options.build_pdlp:
            self.cpp_info.components["core"].defines.append("USE_PDLP")
        if self.options.with_coinor:
            self.cpp_info.components["core"].defines.append("USE_CLP")
            self.cpp_info.components["core"].defines.append("USE_CBC")
            self.cpp_info.components["core"].requires.append("coin-clp::coin-clp")
            self.cpp_info.components["core"].requires.append("coin-cbc::coin-cbc")
        if self.options.with_glpk:
            self.cpp_info.components["core"].defines.append("USE_GLPK")
            self.cpp_info.components["core"].requires.append("glpk::glpk")
        if self.options.with_gurobi:
            self.cpp_info.components["core"].defines.append("USE_GUROBI")
            self.cpp_info.components["core"].requires.append("gurobi::gurobi_c")
        if self.options.with_highs:
            self.cpp_info.components["core"].defines.append("USE_HIGHS")
            self.cpp_info.components["core"].requires.append("highs::highs")
        if self.options.with_scip:
            self.cpp_info.components["core"].defines.append("USE_SCIP")
            self.cpp_info.components["core"].requires.append("scip::scip")
        if self.options.with_cplex:
            self.cpp_info.components["core"].defines.append("USE_CPLEX")
            self.cpp_info.components["core"].requires.append("cplex::cplex_")
        if self.options.with_xpress:
            self.cpp_info.components["core"].defines.append("USE_XPRESS")
            self.cpp_info.components["core"].requires.append("xpress::xprs")

        if self.options.build_flatzinc:
            self.cpp_info.components["flatzinc"].set_property("cmake_target_name", "ortools::flatzinc")
            self.cpp_info.components["flatzinc"].libs = ["ortools_flatzinc"]
            self.cpp_info.components["flatzinc"].requires = ["core"]
