#include "download.hpp"
#include <iostream>

size_t write_callback(void *contents, size_t size, size_t nmemb, void *userp) {
	static_cast<std::string*>(userp)->append(static_cast<char*>(contents), size * nmemb);
	return size * nmemb;
}

class download_internal {
public:
	download_internal(int timeout, const std::optional<std::string> &user_agent) {
		init(timeout, user_agent);
	}
	explicit download_internal(int timeout, const std::optional<std::string>& user_agent, const std::string& socks)
		: socks{socks} {
		init(timeout, user_agent);
	}
	~download_internal() {
		if (hnd != NULL) {
			curl_easy_cleanup(hnd);
		}
		if (headers != NULL) {
			curl_slist_free_all(headers);
		}
	}
	[[nodiscard]] std::string download(const std::string& url);
	int timeout = 10;
	std::string user_agent = default_user_agent;
	std::optional<std::string> socks{};
private:
	CURL *hnd;
	char errors[CURL_ERROR_SIZE];
	struct curl_slist *headers = NULL;
	void init(int timeout, const std::optional<std::string>& user_agent) {
		hnd = curl_easy_init();
		if (!hnd) {
			throw std::runtime_error("Unable to initialize CURL");
		}
		curl_easy_setopt(hnd, CURLOPT_TIMEOUT, timeout);
		curl_easy_setopt(hnd, CURLOPT_WRITEFUNCTION, write_callback);
		curl_easy_setopt(hnd, CURLOPT_HEADER, false);
		errors[0] = 0;
		curl_easy_setopt(hnd, CURLOPT_ERRORBUFFER, errors);
		if (socks.has_value() && *socks != "") {
			curl_easy_setopt(hnd, CURLOPT_PROXYTYPE, CURLPROXY_SOCKS5_HOSTNAME);
			curl_easy_setopt(hnd, CURLOPT_PROXY, socks->c_str());
		}
		for (const auto& header : {"Sec-GPC: 1",
					"Accept: text/html,application/xhtml+xmlapplication/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
					"Accept-Language: en-US,en;q=0.5",
					"DNT: 1",
					"Sec-GPC: 1",
					"Sec-Fetch-User: ?1",
					"Sec-Fetch-Site: same-origin",
					"Sec-Fetch-Mode: navigate",
					"Sec-Fetch-Dest: document",
					"Upgrade-Insecure-Requests: 1"}) {
			curl_slist_append(headers, header);
		}
		curl_easy_setopt(hnd, CURLOPT_HTTPHEADER, headers);
		// Accept all available on the system
		curl_easy_setopt(hnd, CURLOPT_ACCEPT_ENCODING, "");
		if (user_agent.has_value()) {
			curl_easy_setopt(hnd, CURLOPT_USERAGENT, user_agent->c_str());
		}
		// TODO: Verbose mode could enable cURL's verbose mode here...
		// Also change where curl ouptuts to match Downloader's output stream
		// curl_easy_setopt(hnd, CURLOPT_VERBOSE, 1)
	}
};

[[nodiscard]] std::string download_internal::download(const std::string& url) {
	curl_easy_setopt(hnd, CURLOPT_URL, url.c_str());
	curl_easy_setopt(hnd, CURLOPT_REFERER, url.c_str());
	CURLcode res;
	std::string result;
	curl_easy_setopt(hnd, CURLOPT_WRITEDATA, &result);
	res = curl_easy_perform(hnd);
	long http_code;
	curl_easy_getinfo(hnd, CURLINFO_RESPONSE_CODE, &http_code);
	if (res != CURLE_OK || http_code != 200) {
		// Since this is an error, it should still go to cerr,
		// Not the verbose output stream
		std::cerr << "Unable to download: ";
		if (http_code != 200) {
			std::cerr << " Recevied code " << http_code;
		}
		if (errors[0] != 0) {
			std::cerr << " " << errors << '\n';
		}
		throw std::runtime_error("Unable to download");
	}
	return result;
}

[[nodiscard]] std::string Downloader::download(const std::string& url) const {
	if (verbose) {
		if (socks_hostname.has_value()) {
			verbose_output << "Using SOCKS5 proxy " << *socks_hostname << "\n...";
		}
		verbose_output << "Sending GET request to " << url << "...\n";
	}
	return ((socks_hostname.has_value()) ?
			download_internal{timeout,user_agent, *socks_hostname}
			: download_internal{timeout, user_agent}).download(url);
}
