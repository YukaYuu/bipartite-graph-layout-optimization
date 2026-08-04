CXX ?= c++
CXXFLAGS ?= -O2 -std=c++17 -Wall

SRCS = main.cpp layout.cpp sampling.cpp projection.cpp
TARGET = layout3d

$(TARGET): $(SRCS) layout.h sampling.h projection.h
	$(CXX) $(CXXFLAGS) $(SRCS) -o $(TARGET)

clean:
	rm -f $(TARGET) nodes_3d.csv viewpoints.csv projections.csv

.PHONY: clean
