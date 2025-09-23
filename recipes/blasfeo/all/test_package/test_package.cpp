#include <blasfeo.h>
#include <stdio.h>

void test_f77blas() {
  double A[6] = {1.0,2.0,1.0,-3.0,4.0,-1.0};
  double B[6] = {1.0,2.0,1.0,-3.0,4.0,-1.0};
  double C[9] = {.5,.5,.5,.5,.5,.5,.5,.5,.5};
  char transa = 'N';
  char transb = 'T';
  int m = 3;
  int n = 3;
  int k = 2;
  int lda = 3;
  int ldb = 3;
  int ldc = 3;
  double alpha = 1.0;
  double beta  = 2.0;
#ifdef FORTRAN_BLAS_API
  dgemm_(&transa, &transb, &m, &n, &k, &alpha, A, &lda, B, &ldb, &beta, C, &ldc);
#else
  blasfeo_blas_dgemm(&transa, &transb, &m, &n, &k, &alpha, A, &lda, B, &ldb, &beta, C, &ldc);
#endif

  for(int i=0; i<9; i++)
    printf("%lf ", C[i]);
  printf("\n");
}

int main()
{
  test_f77blas();
}
