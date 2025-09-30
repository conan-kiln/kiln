#include <rerun.hpp>
#include <iostream>

int main()
{
	std::cout << "Rerun SDK version: " << rerun::version_string() << std::endl;
	rerun::check_binary_and_header_version_match().throw_on_failure();
}
