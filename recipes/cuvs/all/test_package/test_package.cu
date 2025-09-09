#include <cuvs/neighbors/brute_force.hpp>

int dummy_main() {
    using namespace cuvs::neighbors;
    using dataset_dtype  = float;
    using indexing_dtype = int64_t;
    auto dim             = 128;
    auto n_vectors       = 90;
    raft::device_resources res;
    brute_force::index_params index_params;
    brute_force::search_params search_params;
    auto dataset = raft::make_device_matrix<dataset_dtype, indexing_dtype>(res, n_vectors, dim);
    auto index = brute_force::build(res, index_params, raft::make_const_mdspan(dataset.view()));
}

int main() { }
