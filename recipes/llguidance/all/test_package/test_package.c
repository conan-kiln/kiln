#include <llguidance.h>

int main() {
    struct LlgConstraintInit constraint_init;
    struct LlgTokenizerInit tokenizer;
    llg_constraint_init_set_defaults(&constraint_init, &tokenizer);
}
