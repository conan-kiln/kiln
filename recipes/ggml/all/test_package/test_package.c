#include <ggml.h>
#include <ggml-backend.h>
#include <stdio.h>

struct ggml_backend_reg_i {
    const char * (*get_name)(ggml_backend_reg_t reg);
};

struct ggml_backend_reg {
    int api_version;
    struct ggml_backend_reg_i iface;
};

int main() {
    printf("GGML version: %s\n", ggml_version());
    printf("\nEnabled backends:\n");
    for (int i = 0; i < ggml_backend_reg_count(); i++) {
        ggml_backend_reg_t reg = ggml_backend_reg_get(i);
        printf(" - %s\n", reg->iface.get_name(reg));
    }
}
