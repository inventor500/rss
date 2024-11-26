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

arguments parse_arguments(int argc, char** argv);

std::string get_user_agent();
