#include <qpDUNES.h>

int main() {
	unsigned int nI = 2;
	unsigned int nX = 3;
	unsigned int nU = 2;
	unsigned int* nD = 0;
    qpData_t qpData;
    qpDUNES_setup(&qpData, nI, nX, nU, nD, 0);
}
