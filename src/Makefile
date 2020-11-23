CC = g++
SRCS := $(wildcard *.cpp)
BINS := $(SRCS:%.cpp=%)

.PHONY: all

all: ${BINS}

%: %.o
        ${CC} $< -o $@

%.o: %.c
        ${CC} -c $<

.PHONY: install
install: all
        cp ${BINS} /usr/local/bin/
