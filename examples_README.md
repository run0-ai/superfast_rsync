# Superfast rsync Examples

This directory contains examples demonstrating how to use the `superfast_rsync` library.

## Available Examples

### Basic Usage (`basic_usage.rs`)
A simple example that demonstrates the core rsync algorithm:
- Generating signatures from original data
- Creating deltas between original and modified data
- Applying deltas to reconstruct modified data
- Verifying reconstruction accuracy

**Run with:**
```bash
cargo run --release --example basic_usage
```

### Performance Test (`performance_test.rs`)
A comprehensive performance testing tool that:
- Tests with large files (generated test data)
- Measures throughput and compression ratios
- Supports different hash algorithms (BLAKE3, MD4)
- Configurable block sizes and hash sizes
- Detailed performance statistics

**Run with:**
```bash
# Basic run with default settings
cargo run --release --example performance_test

# Custom configuration
cargo run --release --example performance_test -- --hash blake3 --block-size 4096 --hash-size 16
```

## Test Data

The performance test requires test data files. If they don't exist, they will be automatically generated using the `generate_test_data.py` script.

## Building Examples

To build all examples:
```bash
cargo build --release --examples
```

To build a specific example:
```bash
cargo build --release --example basic_usage
cargo build --release --example performance_test
```

## Example Output

### Basic Usage Example
```
🚀 Superfast rsync - Basic Usage Example
==========================================
Original data: Hello, this is the original data that we want to sync efficiently!
Modified data: Hello, this is the modified data that we want to sync efficiently!

📝 Generating signature from original data...
✅ Signature generated successfully
🔍 Generating delta between original and modified data...
✅ Delta generated successfully
   Delta size: 45 bytes
   Original size: 67 bytes
   Modified size: 67 bytes
   Compression ratio: 32.8%
🔄 Applying delta to reconstruct modified data...
✅ Delta applied successfully
✅ Verification successful: reconstructed data matches modified data!

🎉 Basic usage example completed successfully!
```

### Performance Test Example
```
🔧 Configuration:
   Hash algorithm: Blake3
   Block size: 4096 bytes
   Hash size: 16 bytes

📄 File Statistics:
   Original size: 1048576 bytes (1.00 MB)
   Modified size: 1048576 bytes (1.00 MB)

📊 Performance Statistics:
   Delta size: 524288 bytes (0.50 MB)
   Delta ratio: 50.00%
   Compression ratio: 50.00%

⏱ Timing Statistics:
   Signature generation: 2.34ms (447.69 MB/s)
   Delta generation: 1.23ms (852.50 MB/s)
   Delta application: 0.89ms (1178.18 MB/s)
``` 