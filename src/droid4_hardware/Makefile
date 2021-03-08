CXX=g++
TARGET = droid4-hardware-demon
CFLAGS = -g -Wall
LIBS = -lsqlite3 -lpthread

SRCS=hardware_demon_main.cpp buttons_handler.cpp modem_handler.cpp modem_db.cpp vibrate.cpp date_functions.cpp
OBJECTS=$(subst .cpp,.o,$(SRCS))
HEADERS = $(wildcard *.h)

.PHONY: default all clean

default: $(TARGET)
all: default


%.o: %.c $(HEADERS)
	$(CXX) $(CFLAGS) -c $< -o $@

$(TARGET): $(OBJECTS)
	$(CXX) $(OBJECTS) -Wall $(LIBS) -o $@

clean:
	-rm -f *.o
	-rm -f $(TARGET)

install: all
	cp $(TARGET) /usr/local/bin/
