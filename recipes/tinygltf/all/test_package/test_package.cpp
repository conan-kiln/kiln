#ifndef TINYGLTF_HEADER_ONLY
#define TINYGLTF_IMPLEMENTATION
#define STB_IMAGE_IMPLEMENTATION
#define STB_IMAGE_WRITE_IMPLEMENTATION
#endif
#include <tiny_gltf.h>

#include <cstdio>
#include <string>

int main() {
  tinygltf::Model model;
  tinygltf::TinyGLTF loader;
  std::string err;
  std::string warn;
  bool ret = loader.LoadBinaryFromFile(&model, &err, &warn, "non_existent_file.glb");
  printf("Test %d\n", ret);
}
