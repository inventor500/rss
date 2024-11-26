#include <iostream>
#include <format>
#include <cstdlib>
#include <cstring>
#include "main.hpp"

int main(int argc, char** argv) {
	const arguments args = parse_arguments(argc, argv);
	Downloader down = (args.socks.has_value()) ?
		Downloader{args.timeout, get_user_agent(), *args.socks, args.verbose} :
		Downloader{args.timeout, get_user_agent(), args.verbose};
	try {
		std::string buf = down.download(args.url);
		std::cout << apply_regex(args.replacements, buf, args.verbose) << '\n';
	} catch (const std::runtime_error& err) {
		std::cerr << "Error: " << err.what() << '\n';
	}
}

void print_usage_and_exit(const std::string& name) {
	std::cerr << std::format(
			"Usage {} [--verbose] [--socks5-hostname <hostname>] [--regex {{<pattern_1> <replacement_1> ... <pattern_n> <replacement_n>}}] <url>\n", name);
		std::exit(1);
}

bool streq(const char* str1, const char* str2) {
	return strcmp(str1, str2) == 0;
}

arguments parse_arguments(int argc, char** argv) {
	if (argc == 1) {
		print_usage_and_exit(argv[0]);
	}
	arguments args{};
	for (int pos = 1; pos < argc-1; pos++) { // The last argument is the URL
		if (streq(argv[pos], "--help") || streq(argv[pos], "-h")) {
			print_usage_and_exit(argv[0]);
		} else if (streq(argv[pos], "--verbose") || streq(argv[pos], "-v")) {
			args.verbose = true;
		} else if (streq(argv[pos], "--socks5-hostname")) {
			if ((pos+1) < (argc-1) && !streq(argv[pos+1], "")) {
				pos++;
				args.socks = argv[pos];
			} else {
				std::cerr << "Expected value after \"--socks5-hostname\"\n";
				print_usage_and_exit(argv[0]);
			}
		} else if (streq(argv[pos], "--regex") || streq(argv[pos], "-r")) {
			if ((argc-pos) % 2 == 1) {
				std::cerr << "Expected even number of find/replace arguments\n";
				std::exit(1);
			}
			std::vector<find_replace> temp;
			temp.reserve((argc-pos-1) / 2);
			for (int p = pos+1; p < argc-1; p += 2) {
				temp.push_back({argv[p], argv[p+1]});
			}
			args.replacements = std::move(temp);
		}
	}
	if (strncmp(argv[argc-1], "http", 4) != 0) {
		// Catches invalid URLs and "./cmd --help"
		print_usage_and_exit(argv[0]);
	}
	args.url = argv[argc-1];
	return args;
}

std::string get_user_agent() {
	char* env = std::getenv("RSS_USER_AGENT");
	if (env == NULL) {
		env = std::getenv("USER_AGENT");
	}
	return (env != NULL) ? std::string(env) : default_user_agent;
}
