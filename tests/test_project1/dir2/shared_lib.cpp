#include <iostream>
#include "dir2/f1.hpp"
#include "dir2/f2.hpp"

int dir2_shared_lib() {
  std::cout << "START dir2_shared_lib" << std::endl;
  dir2_f1();
  dir2_f2();
  std::cout << "END dir2_shared_lib" << std::endl;
  return 10;
}
