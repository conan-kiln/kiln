import os
import textwrap

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class AcadosConan(ConanFile):
    name = "acados"
    description = "Fast and embedded solvers for nonlinear optimal control"
    license = "BSD-2-Clause"
    homepage = "https://github.com/acados/acados"
    topics = ("optimal-control", "mpc", "nonlinear-programming", "embedded", "real-time")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_openmp": [True, False],
        "with_daqp": [True, False],
        "with_hpmpc": [True, False],
        "with_ooqp": [True, False],
        "with_osqp": [True, False],
        "with_qpdunes": [True, False],
        "with_qpoases": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openmp": True,
        "with_daqp": False,
        "with_hpmpc": False,
        "with_ooqp": False,  # probably not compatible with current blasfeo
        "with_osqp": False,
        "with_qpdunes": False,
        "with_qpoases": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("blasfeo/[>=0.1 <1]", transitive_headers=True)
        self.requires("hpipm/[>=0.1 <1]", transitive_headers=True)
        if self.options.with_openmp:
            self.requires("openmp/system")
        if self.options.with_daqp:
            self.requires("daqp/0.4.2-acados", transitive_headers=True)
        if self.options.with_hpmpc:
            self.requires("hpmpc/[*]")
        if self.options.with_ooqp:
            self.requires("ooqp/[*]")
        if self.options.with_osqp:
            self.requires("osqp/[<1]", transitive_headers=True)
        if self.options.with_qpdunes:
            self.requires("qpdunes/[*]", transitive_headers=True)
        if self.options.with_qpoases:
            self.requires("acados-qpoases/[*]")

    def validate(self):
        if self.settings.get_safe("compiler.cstd"):
            check_min_cppstd(self, 99)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.7.1]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_POSITION_INDEPENDENT_CODE TRUE)", "")
        replace_in_file(self, "CMakeLists.txt", "add_definitions(-D _GLIBCXX_USE_CXX11_ABI=0)", "")
        replace_in_file(self, "CMakeLists.txt", "NOT EXISTS ${PROJECT_SOURCE_DIR}/external", "FALSE AND ")
        rmdir(self, "external")
        save(self, "external/CMakeLists.txt", "")
        replace_in_file(self, "CMakeLists.txt", "add_subdirectory(acados)",
             textwrap.dedent("""\
                find_package(blasfeo REQUIRED)
                find_package(hpipm REQUIRED)
                if(ACADOS_WITH_HPMPC)
                    find_package(hpmpc REQUIRED)
                endif()
                if(ACADOS_WITH_QORE)
                    find_package(qore REQUIRED)
                endif()
                if(ACADOS_WITH_QPDUNES)
                    find_package(qpdunes REQUIRED)
                    link_libraries(qpdunes::qpdunes)
                endif()
                if(ACADOS_WITH_QPOASES)
                    find_package(qpOASES_e REQUIRED)
                    link_libraries(qpOASES_e)
                endif()
                if(ACADOS_WITH_DAQP)
                    find_package(daqp REQUIRED)
                endif()
                if(ACADOS_WITH_OSQP)
                    find_package(osqp REQUIRED)
                    link_libraries(osqp::osqp)
                endif()
                if (ACADOS_WITH_OOQP)
                    find_package(ooqp REQUIRED)
                    link_libraries(ooqp::ooqp)
                endif()

                add_subdirectory(acados)
             """))
        # hpipm
        for f in [
            "acados/dense_qp/dense_qp_common.c",
            "acados/dense_qp/dense_qp_common.h",
            "acados/dense_qp/dense_qp_hpipm.c",
            "acados/dense_qp/dense_qp_hpipm.h",
            "acados/ocp_nlp/ocp_nlp_common.c",
            "acados/ocp_qp/ocp_qp_common_frontend.c",
            "acados/ocp_qp/ocp_qp_common.c",
            "acados/ocp_qp/ocp_qp_common.h",
            "acados/ocp_qp/ocp_qp_full_condensing.c",
            "acados/ocp_qp/ocp_qp_full_condensing.h",
            "acados/ocp_qp/ocp_qp_hpipm.c",
            "acados/ocp_qp/ocp_qp_hpipm.h",
            "acados/ocp_qp/ocp_qp_partial_condensing.c",
            "acados/ocp_qp/ocp_qp_partial_condensing.h",
            "acados/utils/print.c",
            "interfaces/acados_c/dense_qp_interface.c",
        ]:
            replace_in_file(self, f, '#include "hpipm/include/', '#include "')
        # daqp
        for f in [
            "acados/dense_qp/dense_qp_daqp.h",
            "acados/dense_qp/dense_qp_daqp.c",
        ]:
            replace_in_file(self, f, '#include "daqp/include/', '#include "daqp/')
        # blasfeo
        for f in [
            "acados/ocp_nlp/ocp_nlp_sqp_with_feasible_qp.c",
            "interfaces/acados_c/ocp_nlp_interface.c",
        ]:
            replace_in_file(self, f, '#include "blasfeo/include/', '#include "')
        # hpmpc
        replace_in_file(self, "acados/ocp_qp/ocp_qp_hpmpc.c", '#include "hpmpc/include/', '#include "')
        # osqp
        for f in [
            "acados/ocp_qp/ocp_qp_osqp.h",
            "acados/ocp_qp/ocp_qp_osqp.c",
        ]:
            replace_in_file(self, f, '#include "osqp/include/', '#include "osqp/')

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["ACADOS_OCTAVE"] = False
        tc.cache_variables["ACADOS_PYTHON"] = False
        tc.cache_variables["ACADOS_WITH_QPOASES"] = self.options.with_qpoases
        tc.cache_variables["ACADOS_WITH_DAQP"] = self.options.with_daqp
        tc.cache_variables["ACADOS_WITH_HPMPC"] = self.options.with_hpmpc
        tc.cache_variables["ACADOS_WITH_QORE"] = False  # the QORE project has vanished without a trace
        tc.cache_variables["ACADOS_WITH_OOQP"] = self.options.with_ooqp
        tc.cache_variables["ACADOS_WITH_QPDUNES"] = self.options.with_qpdunes
        tc.cache_variables["ACADOS_WITH_OSQP"] = self.options.with_osqp
        tc.cache_variables["ACADOS_WITH_OPENMP"] = self.options.with_openmp
        tc.cache_variables["ACADOS_WITH_SYSTEM_BLASFEO"] = True
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "cmake"))

    def package_info(self):
        # Main acados library
        self.cpp_info.set_property("cmake_file_name", "acados")
        self.cpp_info.set_property("cmake_target_name", "acados")
        self.cpp_info.libs = ["acados"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]
        if self.options.with_qpoases:
            self.cpp_info.defines.append("ACADOS_WITH_QPOASES")
            self.cpp_info.defines.append("USE_ACADOS_TYPES")
        if self.options.with_qpdunes:
            self.cpp_info.defines.append("ACADOS_WITH_QPDUNES")
            self.cpp_info.defines.append("USE_ACADOS_TYPES")
        if self.options.with_daqp:
            self.cpp_info.defines.append("ACADOS_WITH_DAQP")
        if self.options.with_osqp:
            self.cpp_info.defines.append("ACADOS_WITH_OSQP")
        if self.options.with_ooqp:
            self.cpp_info.defines.append("ACADOS_WITH_OOQP")
        if self.options.with_hpmpc:
            self.cpp_info.defines.append("ACADOS_WITH_HPMPC")
        if self.options.with_openmp:
            self.cpp_info.defines.append("ACADOS_WITH_OPENMP")
