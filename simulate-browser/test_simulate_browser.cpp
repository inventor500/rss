#include "post_process.hpp"
#include "download.hpp"
#include <gtest/gtest.h>

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



/* Main Function */

int main(void) {
	testing::InitGoogleTest();
    return RUN_ALL_TESTS();
}
