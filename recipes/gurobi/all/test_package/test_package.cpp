#include <gurobi_c.h>
#include <stdio.h>

int main() {
    int major, minor, technical;
    GRBversion(&major, &minor, &technical);
    printf("Gurobi version %d.%d.%d\n", major, minor, technical);
#if GRB_VERSION_MAJOR >= 11
    char str[1000];
    GRBgetdistro(str);
    printf("Gurobi distribution: %s\n", str);
    printf("Gurobi platform: %s\n", GRBplatform());
    printf("Gurobi platform extension: %s\n", GRBplatformext());
#endif
}
