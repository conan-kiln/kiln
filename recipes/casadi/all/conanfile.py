import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class PackageConan(ConanFile):
    name = "casadi"
    description = "CasADi is a symbolic framework for automatic differentation and numeric optimization"
    license = "LGPL-3.0-or-only"
    homepage = "https://casadi.org"
    topics = ("optimization", "nonlinear", "numerical-calculations", "scientific-computing", "derivatives",
              "code-generation", "parameter-estimation", "optimal-control", "symbolic-manipulation",
              "algorithmic-differentation", "nonlinear-programming")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "enable_deprecated": [True, False],
        "threadsafe_symbolics": [True, False],
        "install_internal_headers": [True, False],
        "with_alpaqa": [True, False],
        "with_ampl": [True, False],
        "with_blocksqp": [True, False],
        "with_bonmin": [True, False],
        "with_cbc": [True, False],
        "with_clang": [True, False],
        "with_clarabel": [True, False],
        "with_clp": [True, False],
        "with_cplex": [True, False],
        "with_csparse": [True, False],
        "with_daqp": [True, False],
        "with_dsdp": [True, False],
        "with_fatrop": [True, False],
        "with_fmi2": [True, False],
        "with_fmi3": [True, False],
        "with_ghc_filesystem": [True, False],
        "with_gurobi": [True, False],
        "with_highs": [True, False],
        "with_hpipm": [True, False],
        "with_hpmpc": [True, False],
        "with_hsl": [True, False],
        "with_ipopt": [True, False],
        "with_knitro": [True, False],
        "with_lapack": [True, False],
        "with_libzip": [True, False],
        "with_mumps": [True, False],
        "with_ooqp": [True, False],
        "with_opencl": [True, False],
        "with_openmp": [True, False],
        "with_osqp": [True, False],
        "with_proxqp": [True, False],
        "with_pthread": [True, False],
        "with_qpoases": [True, False],
        "with_rumoca": [True, False],
        "with_sleqp": [True, False],
        "with_slicot": [True, False],
        "with_spral": [True, False],
        "with_sundials": [True, False],
        "with_superscs": [True, False],
        "with_tinyxml": [True, False],
        "with_worhp": [True, False],
        "with_zlib": [True, False],
    }
    default_options = {
        "enable_deprecated": True,
        "threadsafe_symbolics": False,
        "install_internal_headers": False,
        "with_alpaqa": False,
        "with_ampl": False,
        "with_blocksqp": True,
        "with_bonmin": False,
        "with_cbc": False,
        "with_clang": False,
        "with_clarabel": False,
        "with_clp": False,
        "with_cplex": False,
        "with_csparse": True,
        "with_daqp": False,
        "with_dsdp": False,
        "with_fatrop": False,
        "with_fmi2": True,
        "with_fmi3": True,
        "with_ghc_filesystem": True,
        "with_gurobi": False,
        "with_highs": False,
        "with_hpipm": False,
        "with_hpmpc": False,
        "with_hsl": False,
        "with_ipopt": False,
        "with_knitro": False,
        "with_lapack": True,
        "with_libzip": True,
        "with_mumps": False,
        "with_ooqp": False,
        "with_opencl": False,
        "with_openmp": True,
        "with_osqp": False,
        "with_proxqp": True,
        "with_pthread": False,
        "with_qpoases": True,
        "with_rumoca": False,
        "with_sleqp": False,
        "with_slicot": False,
        "with_spral": False,
        "with_sundials": True,
        "with_superscs": False,
        "with_tinyxml": True,
        "with_worhp": False,
        "with_zlib": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        if self.options.with_pthread:
            self.options.threadsafe_symbolics.value = True
        if self.options.with_blocksqp:
            self.options.with_qpoases.value = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_alpaqa:
            self.requires("alpaqa/1.0.0-casadi.20230731")
        if self.options.with_bonmin:
            self.requires("coin-bonmin/[*]")
        if self.options.with_cbc:
            self.requires("coin-cbc/[^2.10.11]")
        if self.options.with_clang:
            # clang::CompilerInstance::createDiagnostics() is not compatible in v20
            self.requires("clang/[<20]")
        if self.options.with_clarabel:
            self.requires("clarabel/[*]")
        if self.options.with_clp:
            self.requires("coin-clp/[^1.17.9]")
        if self.options.with_cplex:
            self.requires("cplex/[*]")
        if self.options.with_csparse:
            self.requires("suitesparse-cxsparse/[^4.4.1]")
        if self.options.with_daqp:
            self.requires("daqp/[*]")
        if self.options.with_dsdp:
            self.requires("dsdp/[^5.8]")
        if self.options.with_fatrop:
            self.requires("fatrop/[*]")
        if self.options.with_fmi2:
            self.requires("fmi2/[*]")
        if self.options.with_fmi3:
            self.requires("fmi3/[*]")
        if self.options.with_ghc_filesystem:
            self.requires("ghc-filesystem/[*]")
        if self.options.with_gurobi:
            self.requires("gurobi/[*]")
        if self.options.with_highs:
            self.requires("highs/[*]")
        if self.options.with_hpipm:
            self.requires("hpipm/0.1.3+git.20250801")
        if self.options.with_hpmpc:
            self.requires("hpmpc/[*]")
        if self.options.with_hsl:
            self.requires("coin-hsl/[*]")
        if self.options.with_ipopt:
            self.requires("coin-ipopt/[^3.14.13]")
        if self.options.with_knitro:
            self.requires("knitro/[*]")
        if self.options.with_lapack:
            self.requires("openblas/[>=0.3 <1]")
        if self.options.with_libzip:
            self.requires("libzip/[*]")
        if self.options.with_mumps:
            self.requires("coin-mumps/[^3.0.5]")
        if self.options.with_ooqp:
            self.requires("ooqp/[*]")
        if self.options.with_opencl:
            self.requires("opencl-headers/[>=2023.12.14]")
        if self.options.with_openmp:
            self.requires("openmp/system")
        if self.options.with_osqp:
            self.requires("osqp/[>=0.5.0 <1]")
        if self.options.with_proxqp:
            self.requires("proxsuite/[*]")
        if self.options.with_pthread and self.settings.os == "Windows":
            self.requires("pthreads4w/[^3.0.0]")
        if self.options.with_qpoases:
            self.requires("qpoases/3.2.2-casadi")
        if self.options.with_rumoca:
            self.requires("rumoca/[*]")
        if self.options.with_sleqp:
            self.requires("sleqp/[*]")
        if self.options.with_slicot:
            self.requires("slicot/[*]")
        if self.options.with_spral:
            self.requires("spral/[*]")
        if self.options.with_sundials:
            self.requires("sundials/[^2.5]", options={"build_arkode": False, "build_cvode": False, "build_ida": False})
        if self.options.with_superscs:
            self.requires("superscs/[*]", options={"casadi_compatibility": True})
        if self.options.with_tinyxml:
            self.requires("tinyxml2/[*]")
        if self.options.with_worhp:
            self.requires("worhp/[*]")
        if self.options.with_zlib:
            self.requires("zlib-ng/[^2.0]")

    def validate(self):
        check_min_cppstd(self, 11)
        if self.options.with_alpaqa:
            check_min_cppstd(self, 20)
        if self.options.with_pthread and self.settings.compiler == "msvc":
            raise ConanInvalidConfiguration("with_pthread=True is not supported for MSVC")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # Everything is unvendored
        rmdir(self, "external_packages")
        save(self, "external_packages/CMakeLists.txt", "")
        rm(self, "Find*.cmake", "cmake")
        # Use the regular CMake installation layout on all platforms
        replace_in_file(self, "CMakeLists.txt", "WITH_SELFCONTAINED OR (WIN32 AND NOT CYGWIN)", "FALSE")
        replace_in_file(self, "CMakeLists.txt", "file(RELATIVE_PATH REL_LIB_PREFIX", "set(REL_LIB_PREFIX lib) #")
        replace_in_file(self, "CMakeLists.txt", "file(RELATIVE_PATH REL_CMAKE_PREFIX", "set(REL_CMAKE_PREFIX lib/cmake/casadi) #")
        replace_in_file(self, "casadi/CMakeLists.txt", "file(RELATIVE_PATH TREL_LIB_PREFIX", "set(TREL_LIB_PREFIX lib) #")
        replace_in_file(self, "casadi/CMakeLists.txt", "file(RELATIVE_PATH TREL_BIN_PREFIX", "set(TREL_BIN_PREFIX bin) #")
        replace_in_file(self, "casadi/core/CMakeLists.txt", "file(RELATIVE_PATH TREL_BIN_PREFIX", "set(TREL_BIN_PREFIX bin) #")
        replace_in_file(self, "casadi/core/CMakeLists.txt", "file(RELATIVE_PATH TREL_INCLUDE_PREFIX", "set(TREL_INCLUDE_PREFIX include) #")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["WITH_EXAMPLES"] = False
        tc.cache_variables["USE_CXX11"] = True
        tc.cache_variables["WITH_PYTHON"] = False  # TODO
        tc.cache_variables["WITH_MATLAB"] = False
        tc.cache_variables["WITH_OCTAVE"] = False  # TODO
        tc.cache_variables["WITH_JSON"] = False  # TODO
        tc.cache_variables["INSTALL_INTERNAL_HEADERS"] = self.options.install_internal_headers
        tc.cache_variables["ENABLE_STATIC"] = not self.options.get_safe("shared", True)
        tc.cache_variables["ENABLE_SHARED"] = self.options.get_safe("shared", True)
        tc.cache_variables["WITH_OPENMP"] = self.options.with_openmp
        tc.cache_variables["WITH_THREAD"] = self.options.with_pthread
        tc.cache_variables["WITH_THREAD_MINGW"] = False
        tc.cache_variables["WITH_THREADSAFE_SYMBOLICS"] = self.options.threadsafe_symbolics
        tc.cache_variables["WITH_DEPRECATED_FEATURES"] = self.options.enable_deprecated
        tc.cache_variables["WITH_BUILD_REQUIRED"] = False
        tc.cache_variables["WITH_BUILD_SUNDIALS"] = False
        tc.cache_variables["WITH_BUILD_CSPARSE"] = False
        tc.cache_variables["WITH_BUILD_TINYXML"] = False
        tc.cache_variables["CMAKE_Fortran_COMPILER"] = ""
        tc.cache_variables["Fortran_language_works"] = True

        tc.cache_variables["WITH_OPENCL"] = self.options.with_opencl
        tc.cache_variables["WITH_FMI2"] = self.options.with_fmi2
        tc.cache_variables["WITH_FMI3"] = self.options.with_fmi3
        tc.cache_variables["WITH_SUNDIALS"] = self.options.with_sundials
        tc.cache_variables["WITH_CSPARSE"] = self.options.with_csparse
        tc.cache_variables["WITH_HPIPM"] = self.options.with_hpipm
        tc.cache_variables["WITH_HPMPC"] = self.options.with_hpmpc
        tc.cache_variables["WITH_FATROP"] = self.options.with_fatrop
        tc.cache_variables["WITH_SUPERSCS"] = self.options.with_superscs
        tc.cache_variables["WITH_OSQP"] = self.options.with_osqp
        tc.cache_variables["WITH_CLARABEL"] = self.options.with_clarabel
        tc.cache_variables["WITH_RUMOCA"] = self.options.with_rumoca
        tc.cache_variables["WITH_PROXQP"] = self.options.with_proxqp
        tc.cache_variables["WITH_TINYXML"] = self.options.with_tinyxml
        tc.cache_variables["WITH_DSDP"] = self.options.with_dsdp
        tc.cache_variables["WITH_CLANG"] = self.options.with_clang
        tc.cache_variables["WITH_LAPACK"] = self.options.with_lapack
        tc.cache_variables["WITH_QPOASES"] = self.options.with_qpoases
        tc.cache_variables["WITH_BLOCKSQP"] = self.options.with_blocksqp
        tc.cache_variables["WITH_SLEQP"] = self.options.with_sleqp
        tc.cache_variables["WITH_IPOPT"] = self.options.with_ipopt
        tc.cache_variables["WITH_MOCKUP_REQUIRED"] = False
        tc.cache_variables["WITH_MADNLP"] = False  # TODO
        tc.cache_variables["WITH_KNITRO"] = self.options.with_knitro
        tc.cache_variables["WITH_SNOPT"] = False
        tc.cache_variables["WITH_WORHP"] = self.options.with_worhp
        tc.cache_variables["WITH_CPLEX"] = self.options.with_cplex
        tc.cache_variables["WITH_GUROBI"] = self.options.with_gurobi
        tc.cache_variables["WITH_BONMIN"] = self.options.with_bonmin
        tc.cache_variables["WITH_CBC"] = self.options.with_cbc
        tc.cache_variables["WITH_CLP"] = self.options.with_clp
        tc.cache_variables["WITH_MUMPS"] = self.options.with_mumps
        tc.cache_variables["WITH_SPRAL"] = self.options.with_spral
        tc.cache_variables["WITH_HSL"] = self.options.with_hsl
        tc.cache_variables["WITH_HIGHS"] = self.options.with_highs
        tc.cache_variables["WITH_DAQP"] = self.options.with_daqp
        tc.cache_variables["WITH_ALPAQA"] = self.options.with_alpaqa
        tc.cache_variables["WITH_ZLIB"] = self.options.with_zlib
        tc.cache_variables["WITH_LIBZIP"] = self.options.with_libzip
        tc.cache_variables["WITH_GHC_FILESYSTEM"] = self.options.with_ghc_filesystem
        tc.cache_variables["WITH_OOQP"] = self.options.with_ooqp
        tc.cache_variables["WITH_SQIC"] = False
        tc.cache_variables["WITH_AMPL"] = self.options.with_ampl
        tc.cache_variables["WITH_SLICOT"] = self.options.with_slicot
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("alpaqa", "cmake_target_name", "alpaqa")
        deps.set_property("clang", "cmake_file_name", "CLANG")
        deps.set_property("coin-bonmin", "cmake_file_name", "BONMIN")
        deps.set_property("coin-bonmin", "cmake_target_name", "bonmin")
        deps.set_property("coin-cbc", "cmake_file_name", "CBC")
        deps.set_property("coin-cbc", "cmake_target_name", "cbc")
        deps.set_property("coin-clp", "cmake_file_name", "CLP")
        deps.set_property("coin-clp", "cmake_target_name", "clp")
        deps.set_property("coin-hsl", "cmake_file_name", "HSL")
        deps.set_property("coin-hsl", "cmake_target_name", "hsl::hsl")
        deps.set_property("coin-ipopt", "cmake_file_name", "IPOPT")
        deps.set_property("coin-ipopt", "cmake_target_name", "ipopt")
        deps.set_property("coin-mumps", "cmake_file_name", "MUMPS")
        deps.set_property("coin-mumps", "cmake_target_name", "mumps")
        deps.set_property("clarabel", "cmake_target_name", "clarabel")
        deps.set_property("cplex", "cmake_file_name", "CPLEX")
        deps.set_property("daqp", "cmake_target_name", "daqp")
        deps.set_property("dsdp", "cmake_file_name", "DSDP")
        deps.set_property("ecos", "cmake_file_name", "ECOS")
        deps.set_property("eigen", "cmake_file_name", "Eigen3")
        deps.set_property("eigen", "cmake_target_name", "eigen3")
        deps.set_property("fatrop", "cmake_file_name", "FATROP")
        deps.set_property("fmi2", "cmake_file_name", "FMI2")
        deps.set_property("fmi3", "cmake_file_name", "FMI3")
        deps.set_property("ghc-filesystem", "cmake_file_name", "ghcFilesystem")
        deps.set_property("gsl", "cmake_file_name", "GSL")
        deps.set_property("gurobi", "cmake_file_name", "GUROBI")
        deps.set_property("highs", "cmake_file_name", "HIGHS")
        deps.set_property("highs", "cmake_target_name", "highs")
        deps.set_property("hpmpc", "cmake_file_name", "HPMPC")
        deps.set_property("ipopt", "cmake_file_name", "IPOPT")
        deps.set_property("knitro", "cmake_file_name", "KNITRO")
        deps.set_property("metis", "cmake_file_name", "METIS")
        deps.set_property("metis", "cmake_target_name", "metis::metis")
        deps.set_property("mumps", "cmake_file_name", "MUMPS")
        deps.set_property("ooqp", "cmake_file_name", "OOQP")
        deps.set_property("ooqp", "cmake_target_name", "OOQP")
        deps.set_property("opencl-headers", "cmake_file_name", "OpenCL")
        deps.set_property("osqp", "cmake_file_name", "OSQP")
        deps.set_property("osqp", "cmake_target_name", "osqp::osqp")
        deps.set_property("proxsuite", "cmake_file_name", "PROXQP")
        deps.set_property("qpoases", "cmake_file_name", "QPOASES")
        deps.set_property("slicot", "cmake_file_name", "SLICOT")
        deps.set_property("spral", "cmake_file_name", "SPRAL")
        deps.set_property("suitesparse-cxsparse", "cmake_file_name", "CSPARSE")
        deps.set_property("sundials", "cmake_file_name", "SUNDIALS")
        deps.set_property("superscs", "cmake_target_name", "superscs")
        deps.set_property("tinyxml2", "cmake_file_name", "TINYXML")
        deps.set_property("tinyxml2", "cmake_target_name", "tinyxml2::tinyxml2")
        deps.set_property("worhp", "cmake_file_name", "WORHP")
        deps.set_property("worhp", "cmake_target_name", "worhp::worhp")
        # deps.set_property("matlab", "cmake_file_name", "MATLAB")
        # deps.set_property("numpy", "cmake_file_name", "NUMPY")
        # deps.set_property("octave", "cmake_file_name", "OCTAVE")
        # deps.set_property("snopt", "cmake_file_name", "SNOPT")
        # deps.set_property("snopt_interface", "cmake_file_name", "SNOPT_INTERFACE")
        # deps.set_property("sqic", "cmake_file_name", "SQIC")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "casadi")
        self.cpp_info.set_property("cmake_target_name", "casadi::casadi")
        self.cpp_info.set_property("pkg_config_name", "casadi")
        self.cpp_info.libs = ["casadi"]
        self.cpp_info.defines.append("CASADI_SNPRINTF=snprintf")
        if self.options.threadsafe_symbolics:
            self.cpp_info.defines.append("CASADI_WITH_THREADSAFE_SYMBOLICS")
        if self.options.with_pthread:
            self.cpp_info.defines.append("CASADI_WITH_THREAD")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "dl"]
            if self.options.with_pthread:
                self.cpp_info.system_libs.append("pthread")

        if self.settings.os == "Windows":
            casadipath = os.path.join(self.package_folder, "bin")
        else:
            casadipath = os.path.join(self.package_folder, "lib")
        self.runenv_info.define_path("CASADIPATH", casadipath)
