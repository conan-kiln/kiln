#include <cugraph/algorithms.hpp>
#include <cugraph/graph_functions.hpp>
#include <raft/core/handle.hpp>

void dummy_main() {
  std::shared_ptr<rmm::mr::device_memory_resource> resource = std::make_shared<rmm::mr::cuda_memory_resource>();
  rmm::mr::set_current_device_resource(resource.get());
  raft::handle_t handle(rmm::cuda_stream_per_thread, resource);

  using vertex_t    = int32_t;
  using edge_t      = int32_t;
  constexpr bool multi_gpu        = false;
  constexpr bool store_transposed = false;
  cugraph::graph_t<vertex_t, edge_t, store_transposed, multi_gpu> graph(handle);
}

int main() { }
