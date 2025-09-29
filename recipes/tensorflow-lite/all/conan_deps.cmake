find_package(FlatBuffers REQUIRED)
find_package(Protobuf REQUIRED)
find_package(fp16 REQUIRED)

link_libraries(fp16::fp16)

if(TFLITE_ENABLE_XNNPACK)
  find_package(XNNPACK REQUIRED)
  link_libraries(xnnpack::xnnpack)
endif()
