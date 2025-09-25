import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class CumlConan(ConanFile):
    name = "cuml"
    description = "cuML: GPU Machine Learning Algorithms"
    license = "Apache-2.0"
    homepage = "https://github.com/rapidsai/cuml"
    topics = ("machine-learning", "gpu", "cuda", "rapids")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "logging_level": ["trace", "debug", "info", "warn", "error", "critical", "off"],
        "with_openmp": [True, False],
        "with_nvtx": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "logging_level": "info",
        "with_openmp": True,
        "with_nvtx": True,
    }
    _algorithms = [
        "arima",
        "autoarima",
        "cd",
        "cluster",
        "datasets",
        "dbscan",
        "decisiontree",
        "decomposition",
        "ensemble",
        "explainer",
        "fil",
        "genetic",
        "hdbscan",
        "hierarchicalclustering",
        "holtwinters",
        "kmeans",
        "knn",
        "lars",
        "lasso",
        "linear_model",
        "linearregression",
        "logisticregression",
        "manifold",
        "metrics",
        "pca",
        "qn",
        "randomforest",
        "ridge",
        "sgd",
        "solvers",
        "spectralclustering",
        "svm",
        "treeshap",
        "tsa",
        "tsne",
        "tsvd",
        "umap",
    ]
    options.update({algo: [True, False] for algo in _algorithms})
    default_options.update({algo: True for algo in _algorithms})

    python_requires = "conan-cuda/latest"
    python_requires_extend = "conan-cuda.Cuda"

    # https://github.com/rapidsai/cuml/blob/v25.08.00/cpp/cmake/modules/ConfigureAlgorithms.cmake
    @property
    def _treelite_required(self):
        return self.options.fil or self.options.treeshap or self.options.randomforest

    @property
    def _cufft_required(self):
        return self.options.tsne

    @property
    def _cuvs_required(self):
        return any([
            self.options.dbscan,
            self.options.hdbscan,
            self.options.kmeans,
            self.options.knn,
            self.options.metrics,
            self.options.tsne,
            self.options.umap,
        ])

    @property
    def _gputreeshap_required(self):
        return self.options.treeshap

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        # Fails with
        #   error: static assertion failed: Attempt to use an extended __device__ lambda in a context ...
        self.options.treeshap = False

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        # https://github.com/rapidsai/cuml/blob/v25.08.00/cpp/cmake/modules/ConfigureAlgorithms.cmake
        if self.options.cluster:
            self.options.dbscan.value = True
            self.options.hdbscan.value = True
            self.options.kmeans.value = True
            self.options.hierarchicalclustering.value = True
            self.options.spectralclustering.value = True
        if self.options.decomposition:
            self.options.pca.value = True
            self.options.tsvd.value = True
        if self.options.ensemble:
            self.options.randomforest.value = True
        if self.options.linear_model:
            self.options.linearregression.value = True
            self.options.ridge.value = True
            self.options.lasso.value = True
            self.options.logisticregression.value = True
            self.options.solvers.value = True
        if self.options.manifold:
            self.options.tsne.value = True
            self.options.umap.value = True
        if self.options.solvers:
            self.options.lars.value = True
            self.options.cd.value = True
            self.options.sgd.value = True
            self.options.qn.value = True
        if self.options.tsa:
            self.options.arima.value = True
            self.options.autoarima.value = True
            self.options.holtwinters.value = True
        if self.options.hdbscan:
              self.options.hierarchicalclustering.value = True
        if self.options.hdbscan or self.options.tsne or self.options.umap_algo:
              self.options.knn.value = True
        if self.options.randomforest:
              self.options.decisiontree.value = True
        if self.options.hierarchicalclustering or self.options.kmeans:
            self.options.metrics.value = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("raft/[*]", transitive_headers=True, transitive_libs=True)
        self.requires("rmm/[*]", transitive_headers=True, transitive_libs=True)
        if self._cuvs_required:
            self.requires("cuvs/[>=25.0 <26]")
        if self._treelite_required:
            self.requires("treelite/[^4.4]", transitive_headers=True, transitive_libs=True)
        if self._gputreeshap_required:
            self.requires("gputreeshap/[*]")
        if self.options.with_openmp:
            self.requires("openmp/system", transitive_headers=True, transitive_libs=True)
        self.requires("cumlprims_mg/[*]", transitive_headers=True, transitive_libs=True)
        self.cuda.requires("cudart", transitive_headers=True, transitive_libs=True)
        if self._cufft_required:
            self.cuda.requires("cufft")
        if self.options.with_nvtx:
            self.requires("nvtx/[^3]")

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.30]")
        self.tool_requires("rapids-cmake/[*]")
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "cmake/RAPIDS.cmake", "find_package(rapids-cmake REQUIRED)")
        save(self, "cpp/cmake/thirdparty/get_gputreeshap.cmake", "find_package(GPUTreeShap REQUIRED)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CUML_ALGORITHMS"] = ";".join(algo for algo in self._algorithms if self.options.get_safe(algo))
        tc.cache_variables["BUILD_CUML_C_LIBRARY"] = True
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["BUILD_CUML_TESTS"] = False
        tc.cache_variables["BUILD_CUML_MG_TESTS"] = False
        tc.cache_variables["BUILD_PRIMS_TESTS"] = False
        tc.cache_variables["BUILD_CUML_EXAMPLES"] = False
        tc.cache_variables["BUILD_CUML_BENCH"] = False
        tc.cache_variables["BUILD_CUML_MPI_COMMS"] = False
        tc.cache_variables["LIBCUML_LOGGING_LEVEL"] = str(self.options.logging_level).upper()
        tc.cache_variables["DISABLE_OPENMP"] = not self.options.with_openmp
        tc.cache_variables["CUML_ENABLE_GPU"] = True
        tc.cache_variables["NVTX"] = self.options.with_nvtx
        tc.cache_variables["ENABLE_CUMLPRIMS_MG"] = True
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True
        tc.cache_variables["CMAKE_PREFIX_PATH"] = self.generators_folder.replace("\\", "/")
        tc.generate()

        deps = CMakeDeps(self)
        deps.build_context_activated.append("rapids-cmake")
        deps.build_context_build_modules.append("rapids-cmake")
        deps.set_property("libcumlprims", "cmake_target_name", "cumlprims::cumlprims")
        deps.set_property("cuvs", "cmake_target_name", "cuvs::cuvs")
        deps.generate()

        cuda_tc = self.cuda.CudaToolchain()
        cuda_tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="cpp")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cuml")
        self.cpp_info.set_property("cmake_target_name", "cuml::cuml++")
        self.cpp_info.libs = ["cuml++"]
        self.cpp_info.defines = [
            f"CUML_LOG_ACTIVE_LEVEL={str(self.options.logging_level).upper()}",
            "CUML_ENABLE_GPU",
            "DISABLE_CUSPARSE_DEPRECATED",
        ]
        self.cpp_info.requires = [
            "raft::raft",
            "rmm::rmm",
            "cudart::cudart_",
            "cumlprims_mg::cumlprims_mg",
        ]
        if self._cuvs_required:
            self.cpp_info.requires.append("cuvs::cuvs")
        if self._treelite_required:
            self.cpp_info.requires.append("treelite::treelite")
        if self._gputreeshap_required:
            self.cpp_info.requires.append("gputreeshap::gputreeshap")
        if self.options.with_openmp:
            self.cpp_info.requires.append("openmp::openmp")
        if self._cufft_required:
            self.cpp_info.requires.append("cufft::cufft")
        if self.options.with_nvtx:
            self.cpp_info.requires.append("nvtx::nvtx")
        if not self.options.shared:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs = ["m", "pthread", "dl"]
            if stdcpp_library(self):
                self.cpp_info.system_libs.append(stdcpp_library(self))
