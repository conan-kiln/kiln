#include <stdio.h>

void gdotx_(int *n, const double x[], const double ws[], const int lws[], double v[]) { }

void bqpd_(const int *n, const int *m, int *k, int *kmax, double *a, int *la,
           double *x, double *bl, double *bu, double *f, double *fmin,
           double *g, double *r, double *w, double *e, int *ls, double *alp,
           int *lp, int *mlp, int *peq, double *ws, int *lws,
           const int *mode, int *ifail, int *info, int *iprint, int *nout);

int main() {
  int n = 1;
  int m = 0;
  int peq = 0;
  int k = 0;
  int kmax = 10;
  int la = 1;
  double a_storage = 0.0;
  double *a = &a_storage;
  double x[1] = {0.0};
  double bl[1] = {0.0};
  double bu[1] = {10.0};
  double f = 0.0;
  double fmin = -1.0e50;
  double g[1] = {0.0};
  double r[64];
  double w[128];
  double e[64];
  double ws[64];
  int lws = 64;
  int ls[64];
  double alp = 0.0;
  int lp = 0;
  int mlp = 0;
  int mode = 0;
  int ifail = 0;
  int info = 0;
  int iprint = 0;
  int nout = 6;

  bqpd_(&n, &m, &k, &kmax, a, &la, x, bl, bu, &f, &fmin, g,
        r, w, e, ls, &alp, &lp, &mlp, &peq, ws, &lws,
        &mode, &ifail, &info, &iprint, &nout);

  printf("ifail=%d, x=%.10g, f=%.10g\n", ifail, x[0], f);
}
