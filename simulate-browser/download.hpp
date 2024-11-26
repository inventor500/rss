#pragma once
#include <string>
#include <optional>
#include <curl/curl.h>
#include <iostream>

const std::string default_user_agent = "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0";

class Downloader {
public:
	const int timeout = 10;
	const std::string user_agent = default_user_agent;
	const std::optional<std::string> socks_hostname{};
	const bool verbose = false;
	std::ostream& verbose_output = std::cerr; // For testing
	[[nodiscard]] std::string download(const std::string& url) const;
	Downloader() {}
	Downloader(const std::string &user_agent, const std::string& socks_hostname) :
		user_agent{user_agent}, socks_hostname{socks_hostname} {}
	Downloader(int timeout, const std::string& user_agent, bool verbose):
		timeout{timeout}, user_agent{user_agent}, verbose{verbose} {}
	Downloader(int timeout, const std::string& user_agent, const std::string& socks_hostname, bool verbose):
		timeout{timeout}, user_agent{user_agent}, socks_hostname{socks_hostname}, verbose{verbose} {}
};
