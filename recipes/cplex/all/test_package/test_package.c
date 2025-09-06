#include <ilcplex/cplex.h>
#include <stdio.h>

int main() {
    int status = 0;
    CPXENVptr env = CPXopenCPLEX (&status);
    if (env == NULL) {
        char errmsg[1024];
        fprintf(stderr, "Could not open CPLEX environment.\n");
        CPXgeterrorstring (env, status, errmsg);
        fprintf(stderr, "%s", errmsg);
        return 1;
    }
    printf("CPLEX version: %s\n", CPXversion(env));
}
