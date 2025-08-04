# Makefile for AI Trend Navigator C++ Backtest

CXX = g++
CXXFLAGS = -std=c++17 -O3 -march=native -pthread -Wall -Wextra
TARGET = ai_trend_navigator
SOURCE = ai_trend_navigator.cpp

.PHONY: all clean run

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SOURCE)

clean:
	rm -f $(TARGET) btc_data.csv

run: $(TARGET)
	./$(TARGET)

install-deps:
	@echo "Installing dependencies..."
	@echo "Make sure you have g++ installed:"
	@echo "  Ubuntu/Debian: sudo apt install g++"
	@echo "  macOS: xcode-select --install"
	@echo "  Windows: Install MinGW-w64 or Visual Studio"

benchmark: $(TARGET)
	@echo "Running benchmark..."
	time ./$(TARGET)

help:
	@echo "Available targets:"
	@echo "  all       - Compile the C++ program"
	@echo "  clean     - Remove compiled files and data"
	@echo "  run       - Compile and run the program"
	@echo "  benchmark - Run with timing"
	@echo "  help      - Show this help message"
