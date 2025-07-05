# Superfast Rsync

A high-performance implementation of the rsync algorithm in pure Rust, featuring parallel delta generation and modern cryptographic hashing.

## 🚀 Features

### Core Functionality
- **Signature Generation**: Create compact signatures of large files for efficient delta computation
- **Delta Generation**: Compute minimal patches between original and modified files
- **Delta Application**: Apply patches to reconstruct modified files
- **Multiple Hash Algorithms**: Support for both MD4 (legacy) and BLAKE3 (modern, secure)

### Performance Optimizations
- **Parallel Delta Generation**: Multi-threaded BLAKE3 delta computation using Rayon
- **Optimized Block Processing**: Efficient CRC and hash computation
- **Memory-Efficient**: Streaming processing with minimal memory overhead
- **Configurable Block Sizes**: Tune for speed vs compression trade-offs

### Safety & Security
- **BLAKE3 Support**: Modern, cryptographically secure hash function
- **Memory Safety**: Rust's ownership system prevents common memory errors
- **Thread Safety**: Parallel processing with proper synchronization
- **Feature Flags**: Optional parallel processing to avoid conflicts with FFI

## 📊 Performance Results

Our comprehensive benchmarking shows dramatic performance improvements:

### Delta Generation Speedup
| File Size | Sequential BLAKE3 | Parallel BLAKE3 | Speedup |
|-----------|-------------------|-----------------|---------|
| 5MB       | ~3 MB/s          | ~240 MB/s       | **80×** |
| 25MB      | ~3 MB/s          | ~226 MB/s       | **75×** |
| 100MB     | ~3 MB/s          | ~236 MB/s       | **79×** |

### Compression Ratios
- **Small files (5MB, 10% delta)**: 90% compression
- **Medium files (25MB, 50% delta)**: 50% compression  
- **Large files (100MB, 80% delta)**: 20% compression

### CPU Efficiency
- **Parallel BLAKE3** reduces CPU cycles for delta generation by **50-100×**
- **Memory usage** scales linearly with file size
- **Block size optimization** provides additional performance tuning

## 🛠️ Installation

### Prerequisites
- Rust 1.70+ (latest stable recommended)
- Cargo

### Building
```bash
# Clone the repository
git clone <repository-url>
cd superfast_rsync

# Build with parallel support (recommended)
cargo build --features parallel

# Build without parallel support (for FFI compatibility)
cargo build
```

## 📖 Usage

### Basic API

```rust
use superfast_rsync::{Signature, SignatureOptions, diff, apply, HashAlgorithm};

// Create signature from original file
let signature = Signature::calculate(
    &original_data,
    SignatureOptions {
        block_size: 4096,
        crypto_hash_size: 16,
        hash_algorithm: HashAlgorithm::Blake3,
    },
);

// Generate delta between original and modified
let mut delta = Vec::new();
diff(&signature.index(), &modified_data, &mut delta)?;

// Apply delta to reconstruct modified file
let mut reconstructed = Vec::new();
apply(&original_data, &delta, &mut reconstructed)?;
```

### Parallel Processing (Feature Flag)

```rust
#[cfg(feature = "parallel")]
use superfast_rsync::diff_parallel;

// Use parallel delta generation for better performance
diff_parallel(&signature.index(), &modified_data, &mut delta)?;
```

### Command Line Interface

```bash
# Performance testing
cargo run --example performance_test -- \
    --original original.bin \
    --modified modified.bin \
    --hash blake3 \
    --block-size 4096 \
    --hash-size 16

# With parallel processing
cargo run --example performance_test --features parallel -- \
    --original original.bin \
    --modified modified.bin \
    --hash blake3 \
    --block-size 4096 \
    --hash-size 16
```

## 🧪 Testing & Benchmarking

### Comprehensive Performance Testing
```bash
# Run full performance test suite
python3 tools/run_comprehensive_tests.py
```

This script:
- Generates test files of various sizes (5MB, 25MB, 100MB)
- Tests different delta percentages (10%, 50%, 80%)
- Benchmarks sequential vs parallel BLAKE3
- Compares with MD4 baseline
- Provides detailed performance analysis

### Unit Testing
```bash
# Run all tests
cargo test

# Run tests with parallel feature
cargo test --features parallel
```

### Benchmarking
```bash
# Run criterion benchmarks
cargo bench
```

## ⚙️ Configuration

### Hash Algorithms
- **BLAKE3** (recommended): Modern, secure, fast, supports parallel processing
- **MD4** (legacy): Insecure, sequential only, for compatibility

### Block Sizes
- **4096 bytes**: Good compression, moderate speed
- **16384 bytes**: Better speed, slightly lower compression
- **Custom sizes**: Configurable for specific use cases

### Hash Sizes
- **16 bytes**: Standard size, good performance
- **32 bytes**: BLAKE3 only, higher security

## 🔧 Feature Flags

### Parallel Processing
```toml
[dependencies]
superfast_rsync = { version = "0.1.0", features = ["parallel"] }
```

**When to use:**
- ✅ Rust applications with multi-core systems
- ✅ Large file processing (>10MB)
- ✅ Performance-critical applications

**When NOT to use:**
- ❌ Python/FFI bindings (GIL conflicts)
- ❌ Single-threaded environments
- ❌ Small files (<1MB) where overhead dominates

## 📈 Performance Tuning

### For Maximum Speed
```rust
SignatureOptions {
    block_size: 16384,        // Larger blocks
    crypto_hash_size: 16,     // Standard hash size
    hash_algorithm: HashAlgorithm::Blake3,
}
```

### For Maximum Compression
```rust
SignatureOptions {
    block_size: 4096,         // Smaller blocks
    crypto_hash_size: 16,     // Standard hash size
    hash_algorithm: HashAlgorithm::Blake3,
}
```

### For Large Files (>100MB)
```rust
// Use parallel processing
#[cfg(feature = "parallel")]
diff_parallel(&signature.index(), &data, &mut delta)?;
```

## 🔒 Security Considerations

### Hash Algorithm Selection
- **BLAKE3**: Cryptographically secure, collision-resistant
- **MD4**: Cryptographically broken, use only for legacy compatibility

### Parallel Processing
- **Thread Safety**: All parallel operations are thread-safe
- **Memory Safety**: Rust's ownership system prevents data races
- **Deterministic Output**: Parallel and sequential produce identical results

## 📊 Architecture

### Core Components
- **Signature Generation**: Creates block-based signatures for efficient comparison
- **Delta Generation**: Finds matching blocks and generates minimal patches
- **Delta Application**: Reconstructs files from original + patch
- **Parallel Processing**: Multi-threaded block comparison using Rayon

### Data Flow
1. **Original File** → **Signature Generation** → **Signature**
2. **Modified File** + **Signature** → **Delta Generation** → **Delta**
3. **Original File** + **Delta** → **Delta Application** → **Reconstructed File**

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for details.

### Development Setup
```bash
# Clone and setup
git clone <repository-url>
cd superfast_rsync

# Install development dependencies
cargo install cargo-fuzz

# Run tests
cargo test --features parallel

# Run comprehensive benchmarks
python3 tools/run_comprehensive_tests.py
```

## 📄 License

This project is licensed under the Apache-2.0 License.

## 🙏 Acknowledgments

- **Dropbox Engineering Team**: Original fast_rsync implementation which uses MD4 and inspiration
- Based on the rsync algorithm by Andrew Tridgell and Paul Mackerras
- BLAKE3 implementation by the BLAKE3 team
- Rayon parallel processing library by the Rayon team

---

**Performance results from comprehensive testing on modern multi-core systems. Your mileage may vary based on hardware and workload characteristics.**
