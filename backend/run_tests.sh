#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print section header
print_header() {
    echo -e "\n${YELLOW}=== $1 ===${NC}\n"
}

# Function to run tests with specific marker
run_marked_tests() {
    print_header "Running $1 tests"
    pytest -v -m "$2" --cov=src --cov-report=term-missing
    return $?
}

# Clean up previous test results
print_header "Cleaning up previous test results"
rm -rf .coverage htmlcov coverage.xml

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    print_header "Activating virtual environment"
    source .venv/bin/activate
fi

# Install test dependencies
print_header "Installing test dependencies"
pip install -r requirements.txt

# Run linting
print_header "Running linting checks"
flake8 src tests
FLAKE8_STATUS=$?

# Run type checking
print_header "Running type checks"
mypy src tests
MYPY_STATUS=$?

# Run unit tests
run_marked_tests "Unit" "unit"
UNIT_STATUS=$?

# Run integration tests
run_marked_tests "Integration" "integration"
INTEGRATION_STATUS=$?

# Run end-to-end tests
run_marked_tests "End-to-End" "e2e"
E2E_STATUS=$?

# Generate coverage reports
print_header "Generating coverage reports"
coverage html
coverage xml

# Print summary
print_header "Test Summary"
echo -e "Linting: $([ $FLAKE8_STATUS -eq 0 ] && echo "${GREEN}PASSED${NC}" || echo "${RED}FAILED${NC}")"
echo -e "Type Checking: $([ $MYPY_STATUS -eq 0 ] && echo "${GREEN}PASSED${NC}" || echo "${RED}FAILED${NC}")"
echo -e "Unit Tests: $([ $UNIT_STATUS -eq 0 ] && echo "${GREEN}PASSED${NC}" || echo "${RED}FAILED${NC}")"
echo -e "Integration Tests: $([ $INTEGRATION_STATUS -eq 0 ] && echo "${GREEN}PASSED${NC}" || echo "${RED}FAILED${NC}")"
echo -e "End-to-End Tests: $([ $E2E_STATUS -eq 0 ] && echo "${GREEN}PASSED${NC}" || echo "${RED}FAILED${NC}")"

# Check if any tests failed
if [ $UNIT_STATUS -ne 0 ] || [ $INTEGRATION_STATUS -ne 0 ] || [ $E2E_STATUS -ne 0 ] || [ $FLAKE8_STATUS -ne 0 ] || [ $MYPY_STATUS -ne 0 ]; then
    print_header "Some tests failed!"
    exit 1
else
    print_header "All tests passed!"
    exit 0
fi 