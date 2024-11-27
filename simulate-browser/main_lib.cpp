#include "main.hpp"
#include <cstdlib>
#include <cstring>
#include <format>

bool streq(const char* str1, const char* str2) {
	return strcmp(str1, str2) == 0;
}

arguments parse_arguments(int argc, const char* const* argv) {
	if (argc <= 1) {
		throw argument_error();
	}
	arguments args{};
	for (int pos = 1; pos < argc-1; pos++) { // The last argument is the URL
		if (streq(argv[pos], "--help") || streq(argv[pos], "-h")) {
			// Print help text
			throw argument_error();
		} else if (streq(argv[pos], "--verbose") || streq(argv[pos], "-v")) {
			// Turn on verbose mode
			args.verbose = true;
		} else if (streq(argv[pos], "--socks5-hostname")) {
			// Set a socks5 hostname
			if ((pos+1) < (argc-1) && !streq(argv[pos+1], "")) {
				pos++; // Skip this value in the loop
				args.socks = argv[pos];
			} else {
				// No value was specified
				throw argument_error("Expected value after \"--socks5-hostname\"\n");
			}
		} else if (streq(argv[pos], "--timeout") || streq(argv[pos], "-t")) {
			if (pos+1 >= argc-1) {
				throw argument_error(std::format("Timeout requires a value to be specified"));
			}
			try {
				args.timeout = std::stoi(argv[++pos]);
			} catch (const std::exception& err) {
				throw argument_error(std::format("Unable to parse timeout value {}", argv[pos]));
			}
			if (args.timeout < 0) {
				throw argument_error("Timeout value cannot be less than 0");
			}
		} else if (streq(argv[pos], "--regex") || streq(argv[pos], "-r")) {
			// Turn on find/replace
			if ((argc-pos) % 2 == 1) {
				// Imbalanced argument count
				throw argument_error("Expected even number of find/replace arguments");
			}
			const int size = (argc - pos - 1) / 2;
			if (size == 0) {
				throw argument_error("Expected at least one find/replace pair");
			}
			std::vector<find_replace> temp;
			temp.reserve(size);
			for (int p = pos+1; p < argc-1; p += 2) {
				temp.push_back({argv[p], argv[p+1]});
			}
			args.replacements = std::move(temp);
			break;
		} else {
			throw argument_error(std::format("Unrecognized option {}", argv[pos]));
		}
	}
	if (streq(argv[argc-1], "--help") || streq(argv[argc-1], "-h")) {
		throw argument_error();
	} else if (argv[argc-1][0] == 0 || argv[argc-1][0] == '-') {
		throw argument_error("The last parameter must be the URL");
	} else {
		args.url = argv[argc-1];
	}
	return args;
}

std::string get_user_agent() {
	char* env = std::getenv("RSS_USER_AGENT");
	if (env == NULL) {
		env = std::getenv("USER_AGENT");
	}
	return (env != NULL) ? std::string(env) : default_user_agent;
}
