#include <hpipm_d_dense_qp_dim.h>
#include <stdlib.h>

int main() {
	hpipm_size_t dim_size = d_dense_qp_dim_memsize();
	void *dim_mem = malloc(dim_size);
	struct d_dense_qp_dim dim;
	d_dense_qp_dim_create(&dim, dim_mem);
}
