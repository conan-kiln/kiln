#include <iostream>
#include <iomanip>
#include <experimental/mdspan>

#ifdef MDSPAN_STD
namespace stdex = std;
#else
namespace stdex = std::experimental;
#endif

int main()
{
  double buffer[2 * 3 * 4] = {};
  auto s1 = stdex::mdspan<double, stdex::dextents<size_t, 3>>(buffer, 2, 3, 4);
  s1(1, 1, 1) = 42;

  auto sub1 = stdex::submdspan(s1, 1, 1, stdex::full_extent);
  std::cout << std::boolalpha << (sub1[1] == 42) << std::endl;
}
