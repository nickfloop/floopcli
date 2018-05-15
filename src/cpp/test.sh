#!/bin/bash
g++ /floop/hello_test.cpp /floop/hello.cpp -lpthread -lgtest -lgtest_main -o /floop/hello_test && /floop/hello_test
