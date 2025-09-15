#include <complex.h>

void ma02bz_(const char *side, const int *m, const int *n,
             double _Complex *a, const int *lda);

int main() {
    const char side = 'B';
    const int m = 2, n = 3, lda = 2; // lda >= m
    // A in column-major: columns are contiguous blocks of lda
    double _Complex A[2 * 3] = {
        1.0 + 0.0*I, 2.0 + 0.0*I,   // column 1
        3.0 + 0.0*I, 4.0 + 0.0*I,   // column 2
        5.0 + 0.0*I, 6.0 + 0.0*I    // column 3
    };
    ma02bz_(&side, &m, &n, A, &lda);
}
