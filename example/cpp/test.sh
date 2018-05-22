#!/bin/bash

# compile with g++, link to gtest and pthread (gtest dependency)
# produces binary hello_test, which runs immediately
g++ /floop/hello_test.cpp /floop/hello.cpp \
    -lpthread -lgtest -lgtest_main \
    -o /floop/hello_test && /floop/hello_test
