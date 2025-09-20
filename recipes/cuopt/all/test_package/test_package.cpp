#include <cuopt/linear_programming/solver_settings.hpp>
#include <cuopt/linear_programming/cuopt_c.h>
#include <stdio.h>

int main() {
    cuopt::linear_programming::solver_settings_t<cuopt_int_t, cuopt_float_t> settings;

    cuopt_int_t major, minor, patch;
    cuOptGetVersion(&major, &minor, &patch);
    printf("cuOPT version: %02d.%02d.%02d", major, minor, patch);
}
