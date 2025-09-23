#define SDL_MAIN_HANDLED
#include <SDL3_ttf/SDL_ttf.h>
#include <stdio.h>

int main() {
    int version = TTF_Version();
    int major = version / 1000000;
    int minor = version / 1000 % 1000;
    int patch = version % 1000;
    printf("SDL3_ttf version: %d.%d.%d", major, minor, patch);
}
