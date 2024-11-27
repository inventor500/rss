#include "post_process.hpp"
#include "download.hpp"
#include "main.hpp"
#include <gtest/gtest.h>
#include <gmock/gmock.h>

/* Post Processing Tests */

TEST(PostProcess, ApplyRegex) {
	std::vector<find_replace> replacements = {{"html", "lmth"}};
	std::string input = "<!DOCTYPE html><html>Hello world!</html>";
	std::string expected = "<!DOCTYPE lmth><lmth>Hello world!</lmth>";
	EXPECT_EQ(apply_regex(replacements, input, false), expected) << "Returned an unexpected result";
	replacements = {{"(", "lmth"}};
	EXPECT_THROW(apply_regex(replacements, input, false), std::runtime_error) << "Expected to throw an std::runtime_error for invalid regex";
}

/* Downloading Tests */

/* Main Tests */

TEST(ParseArguments, NoArguments) {
	EXPECT_THROW(parse_arguments(0, NULL), argument_error);
	std::vector<const char*> args{"test"};
	EXPECT_THROW(parse_arguments(args.size(), args.data()), argument_error);
}

TEST(ParseArguments, Help) {
	for (const std::vector<const char*>& args : std::vector<std::vector<const char*>>{
			{"test", "-h"},
			{"test", "--help"},
			{"test", "--help", "example.org"},
			{"test", "-h", "example.org"},
			{"test", "--verbose", "--help", "example.org"},
			{"test", "--verbose", "-h", "example.org"}}) {
		EXPECT_THROW(parse_arguments(args.size(), args.data()), argument_error);
	}
}

TEST(ParseArguments, Verbose) {
	std::vector<const char*> args{"test", "--verbose", "example.org"};
	EXPECT_TRUE(parse_arguments(args.size(), args.data()).verbose) << "Expected verbose mode to be true";
	args = {"test", "example.org"};
	EXPECT_FALSE(parse_arguments(args.size(), args.data()).verbose) << "Expected verbose mode to be false";
}

TEST(ParseArguments, SocksHostname) {
	std::vector<const char*> args{"test", "--socks5-hostname", "example.org"};
	EXPECT_THROW(parse_arguments(args.size(), args.data()), argument_error)
		<< "Expected --socks5-hostname with no value to throw an error";
	args = {"test", "--socks5-hostname", "localhost:8000", "example.org"};
	EXPECT_EQ(parse_arguments(args.size(), args.data()).socks, "localhost:8000")
		<< "Expected --socks5-hostname to be localhost:8000";
	// Unspecified value
	args = {"test", "example.org"};
	EXPECT_FALSE(parse_arguments(args.size(), args.data()).socks.has_value());
}

TEST(ParseArguments, Timeout) {
	std::vector<const char*> args{"test", "--timeout", "20", "example.org"};
	EXPECT_EQ(parse_arguments(args.size(), args.data()).timeout, 20) << "Expected timeout to be 20";
	args[1] = "-t";
	EXPECT_EQ(parse_arguments(args.size(), args.data()).timeout, 20) << "Expected timeout to be 20";
	args = {"test", "example.org"};
	EXPECT_EQ(parse_arguments(args.size(), args.data()).timeout, 10) << "Expected default timeout to be 10";
	for (const auto& a : std::vector<std::vector<const char*>>{
			{"test", "--timeout", "example.org"},
			{"test", "-t", "example.org"},
			{"test", "-t", "-1", "example.org"},
			{"test", "-t", "a", "example.org"},
			// {"test", "-t", "1a", "example.org"}, // This actually works
		}) {
		EXPECT_THROW(parse_arguments(a.size(), a.data()), argument_error);
	}
}

TEST(ParseArguments, Regex) {
	for (const auto& args : std::vector<std::vector<const char*>>{
			{"test", "--regex", "test1", "test2", "example.org"},
			{"test", "-r", "test1", "test2", "example.org"},
		}) {
		std::vector<find_replace> expected = {{"test1", "test2"}};
		auto result = parse_arguments(args.size(), args.data()).replacements;
		ASSERT_EQ(result.size(), expected.size()) << "Result should be size " << expected.size();
		EXPECT_EQ(result.at(0).find, expected.at(0).find);
		EXPECT_EQ(result.at(0).replace, expected.at(0).replace);
		EXPECT_EQ(result.size(), result.capacity());
	}
	for (const auto& args : std::vector<std::vector<const char*>>{
			{"test", "-r", "test1", "example.org"},
			{"test", "-r", "test1", "test2", "test3", "example.org"},
			{"test", "-r", "example.org"},
		}) {
		EXPECT_THROW(parse_arguments(args.size(), args.data()), argument_error);
	}
}

TEST(ParseArguments, UnrecognizedOption) {
	std::vector<const char*> args{"test", "--fizzbuzz", "example.org"};
	EXPECT_THROW(parse_arguments(args.size(), args.data()), argument_error);
}

TEST(ParseArguments, Full) {
	std::vector<const char*> args{"test", "-v", "--socks5-hostname", "localhost:8000", "-t", "20", "-r", "test1", "test2", "example.org"};
	auto res = parse_arguments(args.size(), args.data());
	ASSERT_TRUE(res.verbose);
	ASSERT_EQ(res.socks, "localhost:8000");
	ASSERT_EQ(res.timeout, 20);
	ASSERT_EQ(res.replacements.size(), 1);
	ASSERT_EQ(res.url, "example.org");
}

/* Main Function */

int main(void) {
	testing::InitGoogleTest();
    return RUN_ALL_TESTS();
}
