#pragma once
#include <string>
#include <regex>

struct find_replace {
	std::string find;
	std::string replace;
};

std::string apply_regex(const std::vector<find_replace>& regex_list, const std::string& string, bool verbose);
