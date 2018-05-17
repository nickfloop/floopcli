#!/bin/bash

# compile with g++
# produces binary hello, which runs immediately
g++ /floop/hello.cpp /floop/main.cpp \
    -o /floop/hello && \
    /floop/hello
