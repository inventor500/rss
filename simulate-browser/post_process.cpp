#include "post_process.hpp"
#include <numeric>
#include <format>
#include <iostream>

std::string apply_regex(const std::vector<find_replace>& regex_list, const std::string& string, bool verbose) {
	return std::accumulate(regex_list.cbegin(), regex_list.cend(), string, [verbose](const std::string& accum, const find_replace& fr) {
		if (verbose) {
			std::cerr << std::format("Replacing '{}' with '{}'...\n", fr.find, fr.replace);
		}
		try {
			return std::regex_replace(accum, std::regex(fr.find), fr.replace);
		} catch (const std::exception& err) {
			throw std::runtime_error(std::format("Unable to apply regex: {}", err.what()));
		}
	});
}
