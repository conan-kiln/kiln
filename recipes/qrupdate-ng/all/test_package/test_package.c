#include <stdio.h>

extern void dch1up_(
    double *R,   /* leading dimension ldr x p (column-major upper triangular) */
    int *ldr,    /* leading dimension of R (>= p) */
    int *p,      /* order of R */
    double *u,   /* vector length p */
    double *alpha,
    double *w    /* workspace length p */
);

int main() {
    const int p = 3;
    const int ldr = 3;
    double R[9] = {
        2.0, 0.0, 0.0,  /* col 0 */
        1.0, 3.0, 0.0,  /* col 1 */
        0.0, 1.0, 4.0   /* col 2 */
    };
    double u[3] = {1.0, -2.0, 0.5};
    double alpha = 0.8;
    double w[3] = {0.0, 0.0, 0.0};
    int ip = p;
    int ildr = ldr;
    dch1up_(R, &ildr, &ip, u, &alpha, w);
}
