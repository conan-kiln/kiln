Conan Kiln
==========

Kiln is a recipes-only Conan repository, forked from ConanCenter to
deliver faster iteration, broader coverage (CV/ML/robotics, especially on
edge devices), and greater control over your dependency graph.

No pre-built binaries will be provided by design:

- Minimal defaults – we avoid enabling most options "just in case."
  Packages and dependency trees are much leaner by default with optional components enabled only as-needed by consuming recipes.
- Liberal use of version ranges – version bumps to central packages don't trigger a rebuild of the whole universe.
- Less administrative overhead – the focus is on improving the choice and quality of the packages themselves, not on maintaining the infrastructure.

We encourage users and organizations to host their own binary repositories, with the exact feature sets and build profiles they need, instead of relying on a centrally-managed one.
We plan to offer additional tooling and examples to streamline that process in the future.

While this repository is not compatible with ConanCenter, we continuously sync changes from upstream.
As a result, the packages here are always at least as new, and generally much more up to date, than those on ConanCenter.

## Highlights

The most notable additions in this repository are:
- Full CUDA support at both the language and Toolkit level. All of Nvidia's binary packages are available as well as most of their open-source projects. CUDA support has been added to all recipes that support it.
- TensorRT, plus CUDA-capable ONNX Runtime and PyTorch recipes.
- Full Intel oneAPI support (oneMKL, oneDNN, oneMath, etc). Intel oneAPI DPC++/C++ Compiler toolchain is provided for SYCL support.
- The full suite of GStreamer and its 250+ plugins is supported.
- SuiteSparse, Ceres, GTSAM, g2o, COLMAP, GLOMAP.
- Comprehensive collection of solvers:
    - most COIN-OR libraries with all optional features,
    - SCIP Optimization Suite,
    - Google's OR-Tools,
    - cuOPT,
    - all major commercial solvers (GUROBI, CPLEX, XPRESS, MOSEK, etc).
- Versions of LLVM and Clang that actually work and are used by a few compiler toolchains (e.g. for shaders and other domain-specific IR compilation).
- Complete recipes for Python, Rust and Go to allow building of bindings in either direction.
    - A PythonVenv generator is also provided to streamline the installation of Python buld-time dependencies.
- A better-maintained Vulkan SDK suite.
- Fortran is supported for LAPACK and other numerical libraries.
- All libraries have been tested and fixed as necessary to support for cross-compilation to linux-aarch64.
- libjpeg and zlib have been swapped out for libjpeg-turbo and zlib-ng everywhere for improved performance, matching the behavior of most mainstream distros.
- and much, much more...

In total, 400 additional recipes and 7,500 commits on top of ConanCenter as of 2025-09.

## Setup

You can add this repo as a Conan remote with the following commands:

```
git clone https://github.com/conan-kiln/kiln.git
conan remote add kiln "$PWD/kiln" --type local-recipes-index
```

Requires Conan v2.2 or newer.

## Added recipes and versions

Package versions that are available here but not on ConanCenter as of <date>:

<versions>

