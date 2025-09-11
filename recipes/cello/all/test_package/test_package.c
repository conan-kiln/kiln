#include <Cello.h>

int main(int argc, char** argv) {
  var i0 = $(Int, 5);
  var i1 = $(Int, 3);
  var i2 = $(Int, 4);
  var items = new(Array, Int, i0, i1, i2);
  foreach (item in items) {
    print("Object %$ is of type %$\n",
      item, type_of(item));
  }
}
