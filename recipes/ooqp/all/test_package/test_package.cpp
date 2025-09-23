#include <ooqp/QpGenSparseMa27.h>
#include <ooqp/OoqpVersion.h>


int main() {
    const int nx   = 2;
    int my         = 0;
    const int mz   = 2;
    const int nnzQ = 3;
    int nnzA       = 0;
    const int nnzC = 4;
    QpGenSparseMa27 * qp = new QpGenSparseMa27( nx, my, mz, nnzQ, nnzA, nnzC );
    printOoqpVersionString();
}
