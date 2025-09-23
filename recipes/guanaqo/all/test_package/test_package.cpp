#include <guanaqo/demangled-typename.hpp>
#include <iostream>

int main() {
    struct {
    } s;
    std::cout << guanaqo::demangled_typename(typeid(s)) << std::endl;
}
