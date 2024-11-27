#pragma once
#include "post_process.hpp"
#include "download.hpp"

struct arguments {
	int timeout = 10;
	std::vector<find_replace> replacements = {};
	std::string url = "";
	bool verbose = false;
	std::optional<std::string> socks;
};

// Thrown when parsing arguments fails
class argument_error : public std::runtime_error {
public:
	argument_error() : std::runtime_error{""} {}
	explicit argument_error(const std::string& what) : std::runtime_error{what} {}
};

arguments parse_arguments(int argc, const char* const* argv);

std::string get_user_agent();
