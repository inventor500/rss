#include <iostream>
#include <format>
#include "main.hpp"

int main(int argc, const char* const* argv) {
	try {
		const arguments args = parse_arguments(argc, argv);
		Downloader down = (args.socks.has_value()) ?
			Downloader{args.timeout, get_user_agent(), *args.socks, args.verbose} :
			Downloader{args.timeout, get_user_agent(), args.verbose};
		std::string buf = down.download(args.url);
		std::cout << apply_regex(args.replacements, buf, args.verbose) << '\n';
	} catch (const argument_error& err) {
		std::cerr << std::format(
			"{}\nUsage:\n{} [--verbose] [--socks5-hostname <hostname>] [--timeout <seconds>] [--regex {{<pattern_1> <replacement_1> ... <pattern_n> <replacement_n>}}] <url>\n",
			err.what(),
			argv[0]);
		return 1;
	} catch (const std::runtime_error& err) {
		std::cerr << "Error: " << err.what() << '\n';
		return 1;
	}
	return 0;
}
