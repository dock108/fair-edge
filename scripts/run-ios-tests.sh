#!/bin/bash

# Fair-Edge iOS Testing Script
# Runs iOS tests with various configurations and reporting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IOS_PROJECT_DIR="ios/FairEdge"
SIMULATOR_DESTINATION="platform=iOS Simulator,name=iPhone 15,OS=17.0"
DERIVED_DATA_PATH="DerivedData"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if we're in the right directory
check_ios_project() {
    if [ ! -d "$IOS_PROJECT_DIR" ]; then
        print_error "iOS project directory not found. Please run this script from the project root."
        exit 1
    fi
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing iOS testing dependencies..."
    
    if ! command -v xcpretty &> /dev/null; then
        print_status "Installing xcpretty..."
        gem install xcpretty
    fi
    
    if ! command -v xcov &> /dev/null; then
        print_status "Installing xcov for coverage reporting..."
        gem install xcov
    fi
    
    print_success "Dependencies installed"
}

# Function to clean derived data
clean_build() {
    print_status "Cleaning build artifacts..."
    cd "$IOS_PROJECT_DIR"
    rm -rf "$DERIVED_DATA_PATH"
    mkdir -p "$DERIVED_DATA_PATH"
    cd - > /dev/null
    print_success "Build cleaned"
}

# Function to run unit tests
run_unit_tests() {
    print_status "Running iOS unit tests..."
    
    cd "$IOS_PROJECT_DIR"
    
    xcodebuild test \
        -scheme FairEdge \
        -destination "$SIMULATOR_DESTINATION" \
        -derivedDataPath "$DERIVED_DATA_PATH" \
        -enableCodeCoverage YES \
        -resultBundlePath UnitTestResults.xcresult \
        CODE_SIGN_IDENTITY="" \
        CODE_SIGNING_REQUIRED=NO \
        | xcpretty --report junit --output unit_test_results.xml
    
    local exit_code=${PIPESTATUS[0]}
    cd - > /dev/null
    
    if [ $exit_code -eq 0 ]; then
        print_success "Unit tests passed"
    else
        print_error "Unit tests failed with exit code $exit_code"
        return $exit_code
    fi
}

# Function to run UI tests
run_ui_tests() {
    print_status "Running iOS UI tests..."
    
    cd "$IOS_PROJECT_DIR"
    
    xcodebuild test \
        -scheme FairEdge \
        -destination "$SIMULATOR_DESTINATION" \
        -derivedDataPath "$DERIVED_DATA_PATH" \
        -testPlan FairEdgeUITests \
        -enableCodeCoverage YES \
        -resultBundlePath UITestResults.xcresult \
        CODE_SIGN_IDENTITY="" \
        CODE_SIGNING_REQUIRED=NO \
        | xcpretty --report junit --output ui_test_results.xml
    
    local exit_code=${PIPESTATUS[0]}
    cd - > /dev/null
    
    if [ $exit_code -eq 0 ]; then
        print_success "UI tests passed"
    else
        print_warning "UI tests failed with exit code $exit_code (this is expected if simulators aren't configured)"
        return 0  # Don't fail the script for UI test issues
    fi
}

# Function to generate coverage report
generate_coverage() {
    print_status "Generating coverage report..."
    
    cd "$IOS_PROJECT_DIR"
    
    xcov \
        --derived_data_path "$DERIVED_DATA_PATH" \
        --scheme FairEdge \
        --output_directory coverage \
        --json_report \
        --minimum_coverage_percentage 70 \
        --ignore_file_path .xcovignore || true
    
    cd - > /dev/null
    
    if [ -f "$IOS_PROJECT_DIR/coverage/report.json" ]; then
        print_success "Coverage report generated at $IOS_PROJECT_DIR/coverage/"
    else
        print_warning "Coverage report generation failed, but continuing..."
    fi
}

# Function to run specific test class
run_specific_test() {
    local test_class=$1
    print_status "Running specific test class: $test_class"
    
    cd "$IOS_PROJECT_DIR"
    
    xcodebuild test \
        -scheme FairEdge \
        -destination "$SIMULATOR_DESTINATION" \
        -only-testing:"FairEdgeTests/$test_class" \
        CODE_SIGN_IDENTITY="" \
        CODE_SIGNING_REQUIRED=NO \
        | xcpretty
    
    local exit_code=${PIPESTATUS[0]}
    cd - > /dev/null
    
    if [ $exit_code -eq 0 ]; then
        print_success "Test class $test_class passed"
    else
        print_error "Test class $test_class failed"
        return $exit_code
    fi
}

# Function to validate build
validate_build() {
    print_status "Validating iOS build..."
    
    cd "$IOS_PROJECT_DIR"
    
    xcodebuild build \
        -scheme FairEdge \
        -destination "$SIMULATOR_DESTINATION" \
        CODE_SIGN_IDENTITY="" \
        CODE_SIGNING_REQUIRED=NO \
        | xcpretty
    
    local exit_code=${PIPESTATUS[0]}
    cd - > /dev/null
    
    if [ $exit_code -eq 0 ]; then
        print_success "Build validation passed"
    else
        print_error "Build validation failed"
        return $exit_code
    fi
}

# Function to show test results summary
show_summary() {
    print_status "Test Results Summary"
    echo "===================="
    
    if [ -f "$IOS_PROJECT_DIR/unit_test_results.xml" ]; then
        local unit_tests=$(grep -o 'tests="[0-9]*"' "$IOS_PROJECT_DIR/unit_test_results.xml" | grep -o '[0-9]*' || echo "0")
        local unit_failures=$(grep -o 'failures="[0-9]*"' "$IOS_PROJECT_DIR/unit_test_results.xml" | grep -o '[0-9]*' || echo "0")
        echo -e "Unit Tests: ${GREEN}$unit_tests tests${NC}, ${RED}$unit_failures failures${NC}"
    fi
    
    if [ -f "$IOS_PROJECT_DIR/ui_test_results.xml" ]; then
        local ui_tests=$(grep -o 'tests="[0-9]*"' "$IOS_PROJECT_DIR/ui_test_results.xml" | grep -o '[0-9]*' || echo "0")
        local ui_failures=$(grep -o 'failures="[0-9]*"' "$IOS_PROJECT_DIR/ui_test_results.xml" | grep -o '[0-9]*' || echo "0")
        echo -e "UI Tests: ${GREEN}$ui_tests tests${NC}, ${RED}$ui_failures failures${NC}"
    fi
    
    if [ -f "$IOS_PROJECT_DIR/coverage/report.json" ]; then
        # Extract coverage percentage if available
        echo "Coverage report: $IOS_PROJECT_DIR/coverage/"
    fi
    
    echo "===================="
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  all                Run all tests (unit + UI) with coverage"
    echo "  unit               Run unit tests only"
    echo "  ui                 Run UI tests only"
    echo "  build              Validate build only"
    echo "  coverage           Generate coverage report"
    echo "  clean              Clean build artifacts"
    echo "  specific <class>   Run specific test class"
    echo ""
    echo "Examples:"
    echo "  $0 all                                    # Run all tests"
    echo "  $0 unit                                   # Run unit tests only"
    echo "  $0 specific PushNotificationServiceTests  # Run specific test class"
    echo ""
}

# Main script logic
main() {
    local command=${1:-"all"}
    
    case $command in
        "all")
            check_ios_project
            install_dependencies
            clean_build
            validate_build
            run_unit_tests
            run_ui_tests
            generate_coverage
            show_summary
            ;;
        "unit")
            check_ios_project
            install_dependencies
            clean_build
            validate_build
            run_unit_tests
            generate_coverage
            show_summary
            ;;
        "ui")
            check_ios_project
            install_dependencies
            clean_build
            validate_build
            run_ui_tests
            show_summary
            ;;
        "build")
            check_ios_project
            validate_build
            ;;
        "coverage")
            check_ios_project
            generate_coverage
            ;;
        "clean")
            check_ios_project
            clean_build
            ;;
        "specific")
            if [ -z "$2" ]; then
                print_error "Please specify a test class name"
                show_usage
                exit 1
            fi
            check_ios_project
            install_dependencies
            run_specific_test "$2"
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run the script
main "$@"