#include <octave/oct.h>

DEFUN_DLD(hello, args, nargout, "hello(name) -> greeting")
{
  if (args.length() < 1 || !args(0).is_string())
    print_usage();

  std::string name = args(0).string_value();
  std::string out = "Hello, " + name + "!";

  return octave_value(out);
}
