#include "hello.h"
#include <gtest/gtest.h>

TEST(helloTest, test){
    EXPECT_EQ(0, hello());
}
