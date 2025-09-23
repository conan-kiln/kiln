double dnrm2_(const int* n, const double* x, const int* incx);

int main() {
    int n = 10;
    double x[10] = {0};
    int incx = 1;
    dnrm2_(&n, x, &incx);
}
