#include <worhp/worhp.h>
#include <stdio.h>

int main() {
    OptVar o;
    Workspace w;
    Params p;
    Control c;
    WorhpPreInit(&o, &w, &p, &c);
    printf("WORHP version: %s\n", WORHP_VERSION);
}
