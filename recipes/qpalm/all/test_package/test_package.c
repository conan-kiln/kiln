#include <qpalm.h>

int main() {
    QPALMSettings *settings = (QPALMSettings *)qpalm_malloc(sizeof(QPALMSettings));
    qpalm_set_default_settings(settings);
}
