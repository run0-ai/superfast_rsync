#!/bin/bash

# Superfast rsync build script
# Builds the main project, runs tests, benchmarks, and test directory

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists cargo; then
        print_error "Cargo not found. Please install Rust and Cargo first."
        exit 1
    fi
    
    if ! command_exists rustc; then
        print_error "Rust compiler not found. Please install Rust first."
        exit 1
    fi
    
    # Check if Rust is available
    if ! command_exists rustc; then
        print_error "Rust compiler not found. Please install Rust first."
        exit 1
    fi
    
    print_status "Using Rust toolchain: $(rustup show active-toolchain 2>/dev/null | cut -d' ' -f1 || echo 'unknown')"
    
    print_success "Prerequisites check passed"
}

# Clean previous builds
clean_builds() {
    print_status "Cleaning previous builds..."
    cargo clean
    if [[ -d "test" ]]; then
        (cd test && cargo clean 2>/dev/null || true)
    fi
    if [[ -d "fuzz" ]]; then
        (cd fuzz && cargo clean 2>/dev/null || true)
    fi
    print_success "Clean completed"
}

# Build the main project
build_main() {
    print_status "Building main project..."
    cargo build --release
    print_success "Main project built successfully"
}

# Run unit tests
run_tests() {
    print_status "Running unit tests..."
    cargo test --release
    print_success "Unit tests passed"
}

# Run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    cargo test --release --tests
    print_success "Integration tests passed"
}

# Run benchmarks
run_benchmarks() {
    print_status "Running benchmarks..."
    if [[ -d "benches" ]]; then
        cargo bench --no-run
        print_success "Benchmarks compiled successfully"
    else
        print_warning "No benchmarks directory found"
    fi
}

# Build and run examples
build_examples() {
    if [[ -f "examples/performance_test.rs" ]]; then
        print_status "Building examples..."
        cargo build --release --examples
        print_success "Examples built successfully"
        
        # Check if test data files exist for performance test
        if [[ ! -f "original_large_snapshot.bin" ]] || [[ ! -f "modified_large_snapshot.bin" ]]; then
            print_warning "Test data files not found. Generating test data..."
            if command_exists python3; then
                python3 tools/generate_test_data.py || {
                    print_warning "Failed to generate test data with Python, trying with python..."
                    python tools/generate_test_data.py || {
                        print_error "Failed to generate test data"
                        return 1
                    }
                }
            else
                print_error "Python not found. Cannot generate test data."
                return 1
            fi
        fi
        
        print_status "Running performance test example..."
        cargo run --release --example performance_test -- --hash blake3 --block-size 4096 --hash-size 16
        print_success "Performance test example completed successfully"
    else
        print_warning "No examples directory found"
    fi
}

# Run fuzz tests
run_fuzz_tests() {
    if [[ -d "fuzz" ]]; then
        print_status "Building fuzz tests..."
        (cd fuzz && cargo build --release)
        print_success "Fuzz tests built successfully"
        
        # Note: Actual fuzzing would require additional setup and time
        print_warning "Fuzz tests built but not executed (requires additional setup)"
    else
        print_warning "No fuzz directory found"
    fi
}

# Run clippy for code quality
run_clippy() {
    print_status "Running clippy for code quality checks..."
    cargo clippy --release -- -D warnings || {
        print_warning "Clippy found some issues"
        return 1
    }
    print_success "Clippy checks passed"
}



# Generate documentation
generate_docs() {
    print_status "Generating documentation..."
    cargo doc --release --no-deps
    print_success "Documentation generated successfully"
}

# Main build process
main() {
    echo "🚀 Starting Superfast rsync build process..."
    echo "================================================"
    
    # Check prerequisites
    check_prerequisites
    
    # Clean previous builds
    clean_builds
    
    # Run linting checks
    run_clippy
    
    # Build main project
    build_main
    
    # Run tests
    run_tests
    run_integration_tests
    
    # Run benchmarks
    run_benchmarks
    
    # Build and run examples
    build_examples
    
    # Run fuzz tests
    run_fuzz_tests
    
    # Generate documentation
    generate_docs
    
    echo "================================================"
    print_success "🎉 Build process completed successfully!"
    echo ""
    echo "📦 Build artifacts:"
    echo "   - Release binary: target/release/superfast_rsync"
    echo "   - Examples: examples/target/release/examples/"
    echo "   - Documentation: target/doc/superfast_rsync/index.html"
    echo ""
    echo "🧪 To run tests manually:"
    echo "   cargo test --release"
    echo ""
    echo "📊 To run benchmarks:"
    echo "   cargo bench"
    echo ""
    echo "🚀 To run examples:"
    echo "   cargo run --release --example performance_test"
    echo ""
    echo "📖 To view documentation:"
    echo "   cargo doc --open"
}

# Handle script arguments
case "${1:-}" in
    "clean")
        clean_builds
        ;;
    "test")
        check_prerequisites
        run_tests
        run_integration_tests
        ;;
    "bench")
        check_prerequisites
        run_benchmarks
        ;;
    "examples")
        check_prerequisites
        build_examples
        ;;
    "docs")
        check_prerequisites
        generate_docs
        ;;
    "check")
        check_prerequisites
        run_clippy
        ;;
    "help"|"-h"|"--help")
        echo "Superfast rsync build script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no args)  Full build process (default)"
        echo "  clean      Clean all build artifacts"
        echo "  test       Run tests only"
        echo "  bench      Run benchmarks only"
        echo "  examples   Build and run performance test example only"
        echo "  docs       Generate documentation only"
        echo "  check      Run linting checks only"
        echo "  help       Show this help message"
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac 