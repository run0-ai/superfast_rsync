#!/usr/bin/env python3
"""
Comprehensive testing script for superfast_rsync.
Generates test data, runs performance tests, and interprets results.
"""

import os
import random
import struct
import glob
import csv
import subprocess
import time
from datetime import datetime

def generate_file_pair(base_name, size_mb, delta_percent, output_dir="/tmp"):
    """Generate a pair of original and modified files with specified size and delta percentage."""
    size_bytes = size_mb * 1024 * 1024
    chunk_size = 1024 * 1024  # 1MB chunks
    
    original_path = os.path.join(output_dir, f"{base_name}_original.bin")
    modified_path = os.path.join(output_dir, f"{base_name}_modified.bin")
    
    print(f"\nGenerating {base_name} files ({size_mb}MB, {delta_percent}% delta)...")
    
    # Generate original file
    with open(original_path, "wb") as f:
        remaining = size_bytes
        while remaining > 0:
            chunk_size_actual = min(chunk_size, remaining)
            chunk = os.urandom(chunk_size_actual)
            f.write(chunk)
            remaining -= chunk_size_actual
    
    # Generate modified file with specified delta percentage
    with open(modified_path, "wb") as f:
        # Calculate how much to keep from original
        keep_size = int(size_bytes * (1 - delta_percent / 100.0))
        
        # Read the portion to keep from original
        with open(original_path, "rb") as orig_f:
            keep_data = orig_f.read(keep_size)
            f.write(keep_data)
        
        # Generate random data for the rest
        remaining = size_bytes - keep_size
        while remaining > 0:
            chunk_size_actual = min(chunk_size, remaining)
            chunk = os.urandom(chunk_size_actual)
            f.write(chunk)
            remaining -= chunk_size_actual
    
    print(f"  Original: {original_path} ({size_bytes} bytes)")
    print(f"  Modified: {modified_path} ({size_bytes} bytes)")
    print(f"  Data kept: {keep_size} bytes ({keep_size / 1024 / 1024:.2f} MB)")
    print(f"  Random data: {size_bytes - keep_size} bytes ({(size_bytes - keep_size) / 1024 / 1024:.2f} MB)")
    
    return original_path, modified_path

def run_performance_test(original_file, modified_file, hash_algo, block_size, hash_size, use_parallel=False):
    """Run a single performance test and return the results."""
    cmd = [
        "cargo", "run", "--example", "performance_test",
    ]
    
    if use_parallel:
        cmd.extend(["--features", "parallel"])
    
    cmd.extend([
        "--", "--original", original_file,
        "--modified", modified_file,
        "--hash", hash_algo,
        "--block-size", str(block_size),
        "--hash-size", str(hash_size)
    ])
    
    print(f"  Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout, result.stderr, None
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode

def parse_performance_output(output):
    """Parse the performance test output to extract key metrics."""
    metrics = {}
    
    # Extract file sizes
    for line in output.split('\n'):
        if "Original size:" in line:
            metrics['original_size_mb'] = float(line.split('(')[1].split('MB')[0].strip())
        elif "Modified size:" in line:
            metrics['modified_size_mb'] = float(line.split('(')[1].split('MB')[0].strip())
        elif "Delta size:" in line:
            metrics['delta_size_mb'] = float(line.split('(')[1].split('MB')[0].strip())
        elif "Delta ratio:" in line:
            metrics['delta_ratio_percent'] = float(line.split('%')[0].split(':')[1].strip())
        elif "Compression ratio:" in line:
            metrics['compression_ratio_percent'] = float(line.split('%')[0].split(':')[1].strip())
        elif "Signature generation:" in line:
            # Extract time and throughput
            time_part = line.split('(')[0].split(':')[1].strip()
            throughput_part = line.split('(')[1].split('MB/s')[0].strip()
            metrics['signature_time'] = time_part
            metrics['signature_throughput_mbps'] = float(throughput_part)
        elif "Delta generation:" in line:
            time_part = line.split('(')[0].split(':')[1].strip()
            throughput_part = line.split('(')[1].split('MB/s')[0].strip()
            metrics['delta_time'] = time_part
            metrics['delta_throughput_mbps'] = float(throughput_part)
        elif "Delta application:" in line:
            time_part = line.split('(')[0].split(':')[1].strip()
            throughput_part = line.split('(')[1].split('MB/s')[0].strip()
            metrics['apply_time'] = time_part
            metrics['apply_throughput_mbps'] = float(throughput_part)
        elif "Signature cycles/byte:" in line:
            metrics['cpu_sig'] = float(line.split(':')[1].strip())
        elif "Delta generation cycles/byte:" in line:
            metrics['cpu_diff'] = float(line.split(':')[1].strip())
        elif "Delta application cycles/byte:" in line:
            metrics['cpu_apply'] = float(line.split(':')[1].strip())
        elif "Total CPU cycles:" in line:
            metrics['cpu_total'] = float(line.split(':')[1].strip())
        elif "Peak memory usage:" in line:
            metrics['peak_ram_mb'] = float(line.split(':')[1].split('MB')[0].strip())
    
    return metrics

def run_comprehensive_performance_tests(test_files, output_dir):
    """Run comprehensive performance tests on all test files."""
    # 3 file sizes × 2 blake3 block sizes × 2 (seq+par) + 1 md4 = 13 tests
    hash_algorithms = ["blake3"]
    block_sizes = [4096, 16384]
    hash_sizes = [16]
    total_tests = len(test_files) * len(hash_algorithms) * len(block_sizes) * len(hash_sizes) * 2 + len(test_files)  # ×2 for blake3 seq+par, +1 for md4_seq
    current_test = 0
    print(f"\n🚀 Starting comprehensive performance tests ({total_tests} total configurations)...")
    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(output_dir, f"performance_results_{timestamp}.csv")
    for test_file in test_files:
        print(f"\n📁 Testing {test_file['name']} files ({test_file['size_mb']}MB, {test_file['delta_percent']}% delta)")
        # Sequential BLAKE3 runs
        for hash_algo in hash_algorithms:
            algo_hash_sizes = hash_sizes
            for hash_size in algo_hash_sizes:
                for block_size in block_sizes:
                    current_test += 1
                    print(f"\n  Test {current_test}/{total_tests}: {hash_algo} sequential (hash={hash_size}, block={block_size})")
                    if not os.path.exists(test_file['original_path']) or not os.path.exists(test_file['modified_path']):
                        print(f"    ❌ File not found.")
                        continue
                    stdout, stderr, error_code = run_performance_test(
                        test_file['original_path'],
                        test_file['modified_path'],
                        hash_algo,
                        block_size,
                        hash_size,
                        use_parallel=False
                    )
                    if error_code is not None:
                        print(f"    ❌ Test failed with error code {error_code}")
                        if stderr:
                            print(f"    Error: {stderr}")
                        continue
                    metrics = parse_performance_output(stdout)
                    if not metrics:
                        print(f"    ⚠️  Could not parse results")
                        continue
                    result = {
                        'timestamp': datetime.now().isoformat(),
                        'test_name': test_file['name'],
                        'file_size_mb': test_file['size_mb'],
                        'delta_percent': test_file['delta_percent'],
                        'hash_algorithm': f"{hash_algo}_seq",
                        'block_size': block_size,
                        'hash_size': hash_size,
                        **metrics
                    }
                    results.append(result)
                    print(f"    ✅ Success: {metrics.get('compression_ratio_percent', 0):.1f}% compression")
        # Parallel BLAKE3 runs
        for hash_algo in hash_algorithms:
            algo_hash_sizes = hash_sizes
            for hash_size in algo_hash_sizes:
                for block_size in block_sizes:
                    current_test += 1
                    print(f"\n  Test {current_test}/{total_tests}: {hash_algo} parallel (hash={hash_size}, block={block_size})")
                    if not os.path.exists(test_file['original_path']) or not os.path.exists(test_file['modified_path']):
                        print(f"    ❌ File not found.")
                        continue
                    stdout, stderr, error_code = run_performance_test(
                        test_file['original_path'],
                        test_file['modified_path'],
                        hash_algo,
                        block_size,
                        hash_size,
                        use_parallel=True
                    )
                    if error_code is not None:
                        print(f"    ❌ Test failed with error code {error_code}")
                        if stderr:
                            print(f"    Error: {stderr}")
                        continue
                    metrics = parse_performance_output(stdout)
                    if not metrics:
                        print(f"    ⚠️  Could not parse results")
                        continue
                    result = {
                        'timestamp': datetime.now().isoformat(),
                        'test_name': test_file['name'],
                        'file_size_mb': test_file['size_mb'],
                        'delta_percent': test_file['delta_percent'],
                        'hash_algorithm': f"{hash_algo}_par",
                        'block_size': block_size,
                        'hash_size': hash_size,
                        **metrics
                    }
                    results.append(result)
                    print(f"    ✅ Success: {metrics.get('compression_ratio_percent', 0):.1f}% compression")
        # Sequential MD4 run for comparison
        current_test += 1
        print(f"\n  Test {current_test}/{total_tests}: md4 sequential (hash=16, block=4096)")
        stdout, stderr, error_code = run_performance_test(
            test_file['original_path'],
            test_file['modified_path'],
            "md4",
            4096,
            16,
            use_parallel=False
        )
        if error_code is not None:
            print(f"    ❌ Test failed with error code {error_code}")
            if stderr:
                print(f"    Error: {stderr}")
            continue
        metrics = parse_performance_output(stdout)
        if not metrics:
            print(f"    ⚠️  Could not parse results")
            continue
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_file['name'],
            'file_size_mb': test_file['size_mb'],
            'delta_percent': test_file['delta_percent'],
            'hash_algorithm': "md4_seq",
            'block_size': 4096,
            'hash_size': 16,
            **metrics
        }
        results.append(result)
        print(f"    ✅ Success: {metrics.get('compression_ratio_percent', 0):.1f}% compression")
    if results:
        fieldnames = [
            'timestamp', 'test_name', 'file_size_mb', 'delta_percent',
            'hash_algorithm', 'block_size', 'hash_size',
            'original_size_mb', 'modified_size_mb', 'delta_size_mb',
            'delta_ratio_percent', 'compression_ratio_percent',
            'signature_time', 'signature_throughput_mbps',
            'delta_time', 'delta_throughput_mbps',
            'apply_time', 'apply_throughput_mbps',
            'cpu_sig', 'cpu_diff', 'cpu_apply', 'cpu_total',
            'peak_ram_mb'
        ]
        with open(results_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\n📊 Results saved to: {results_file}")
        print(f"✅ Completed {len(results)} successful tests")
        return results_file, results
    else:
        print(f"\n❌ No successful tests completed")
        return None, []

def analyze_performance_results(results_file, results):
    """Analyze performance results and provide user-friendly insights."""
    print(f"\n🔍 Analyzing performance results...")
    print(f"  📊 Analyzing: {results_file}")
    
    if not results:
        print("  ❌ No results found to analyze.")
        return
    
    print(f"\n📈 Performance Analysis Summary:")
    print(f"  Total tests analyzed: {len(results)}")
    
    # Group results by file size
    size_groups = {}
    for result in results:
        size = int(result['file_size_mb'])
        if size not in size_groups:
            size_groups[size] = []
        size_groups[size].append(result)
    
    # Analyze each file size group
    for size_mb in sorted(size_groups.keys()):
        group_results = size_groups[size_mb]
        print(f"\n📁 File Size: {size_mb}MB")
        
        # Find best configurations for this file size
        best_compression = max(group_results, key=lambda x: float(x['compression_ratio_percent']))
        best_throughput = max(group_results, key=lambda x: float(x['delta_throughput_mbps']))
        
        print(f"  🏆 Best compression: {best_compression['hash_algorithm']} "
              f"(block={best_compression['block_size']}, hash={best_compression['hash_size']}) "
              f"- {float(best_compression['compression_ratio_percent']):.1f}% compression")
        
        print(f"  ⚡ Best throughput: {best_throughput['hash_algorithm']} "
              f"(block={best_throughput['block_size']}, hash={best_throughput['hash_size']}) "
              f"- {float(best_throughput['delta_throughput_mbps']):.1f} MB/s")
    
    # Overall recommendations
    print(f"\n💡 General Recommendations:")
    
    # Analyze block size impact
    block_size_analysis = {}
    for result in results:
        block_size = int(result['block_size'])
        if block_size not in block_size_analysis:
            block_size_analysis[block_size] = []
        block_size_analysis[block_size].append(float(result['compression_ratio_percent']))
    
    best_block_size = max(block_size_analysis.keys(), 
                        key=lambda x: sum(block_size_analysis[x]) / len(block_size_analysis[x]))
    print(f"  📦 Optimal block size: {best_block_size} bytes "
          f"(avg compression: {sum(block_size_analysis[best_block_size]) / len(block_size_analysis[best_block_size]):.1f}%)")
    
    # Analyze hash algorithm impact
    algo_analysis = {}
    for result in results:
        algo = result['hash_algorithm']
        if algo not in algo_analysis:
            algo_analysis[algo] = []
        algo_analysis[algo].append(float(result['compression_ratio_percent']))
    
    best_algo = max(algo_analysis.keys(), 
                   key=lambda x: sum(algo_analysis[x]) / len(algo_analysis[x]))
    print(f"  🔐 Best hash algorithm: {best_algo} "
          f"(avg compression: {sum(algo_analysis[best_algo]) / len(algo_analysis[best_algo]):.1f}%)")
    
    # File size specific recommendations
    print(f"\n📋 File Size Specific Recommendations:")
    
    small_files = [r for r in results if int(r['file_size_mb']) <= 50]
    medium_files = [r for r in results if 50 < int(r['file_size_mb']) <= 500]
    large_files = [r for r in results if int(r['file_size_mb']) > 500]
    
    if small_files:
        best_small = max(small_files, key=lambda x: float(x['compression_ratio_percent']))
        print(f"  📄 Small files (≤50MB): Use {best_small['hash_algorithm']} "
              f"with {best_small['block_size']} byte blocks")
    
    if medium_files:
        best_medium = max(medium_files, key=lambda x: float(x['compression_ratio_percent']))
        print(f"  📄 Medium files (50-500MB): Use {best_medium['hash_algorithm']} "
              f"with {best_medium['block_size']} byte blocks")
    
    if large_files:
        best_large = max(large_files, key=lambda x: float(x['compression_ratio_percent']))
        print(f"  📄 Large files (>500MB): Use {best_large['hash_algorithm']} "
              f"with {best_large['block_size']} byte blocks")
    
    # Performance vs compression trade-offs
    print(f"\n⚖️  Performance vs Compression Trade-offs:")
    
    # Find configurations with best compression vs best speed
    all_compression = [(r, float(r['compression_ratio_percent'])) for r in results]
    all_speed = [(r, float(r['delta_throughput_mbps'])) for r in results]
    
    best_compression_config = max(all_compression, key=lambda x: x[1])
    best_speed_config = max(all_speed, key=lambda x: x[1])
    
    print(f"  🎯 Best compression: {best_compression_config[1]:.1f}% "
          f"({best_compression_config[0]['hash_algorithm']}, "
          f"block={best_compression_config[0]['block_size']})")
    
    print(f"  🚀 Best speed: {best_speed_config[1]:.1f} MB/s "
          f"({best_speed_config[0]['hash_algorithm']}, "
          f"block={best_speed_config[0]['block_size']})")
    
    # Memory usage considerations
    print(f"\n🧠 Memory Usage Considerations:")
    print(f"  • Larger block sizes reduce memory overhead but may reduce compression")
    print(f"  • BLAKE3 uses more memory than MD4 but provides better security")
    print(f"  • For large files, consider using larger block sizes to reduce memory usage")
    
    # Delta percentage impact
    print(f"\n📊 Delta Percentage Impact:")
    delta_groups = {}
    for result in results:
        delta_pct = int(result['delta_percent'])
        if delta_pct not in delta_groups:
            delta_groups[delta_pct] = []
        delta_groups[delta_pct].append(float(result['compression_ratio_percent']))
    
    for delta_pct in sorted(delta_groups.keys()):
        avg_compression = sum(delta_groups[delta_pct]) / len(delta_groups[delta_pct])
        print(f"  • {delta_pct}% delta: {avg_compression:.1f}% avg compression")
    
    # Print CPU and RAM summary table
    print(f"\n🖥️ CPU & Memory Summary Table:")
    print(f"{'File':<8} {'Algo':<6} {'Block':<6} {'Comp%':<7} {'CPU_sig':<8} {'CPU_diff':<8} {'CPU_apply':<9} {'CPU_total':<10} {'PeakRAM(MB)':<11}")
    for r in results:
        print(f"{r['test_name']:<8} {r['hash_algorithm']:<6} {r['block_size']:<6} {float(r.get('compression_ratio_percent',0)):<7.1f} {r.get('cpu_sig','-'):<8} {r.get('cpu_diff','-'):<8} {r.get('cpu_apply','-'):<9} {r.get('cpu_total','-'):<10} {r.get('peak_ram_mb','-'):<11}")
    
    print(f"\n✅ Performance analysis complete!")

def main():
    """Main function that orchestrates the entire testing workflow."""
    print("🚀 Starting comprehensive superfast_rsync testing workflow...")
    
    # Ensure output directory exists
    output_dir = "/tmp"
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n📁 Step 1: Generating test file pairs with different sizes and delta percentages...")
    
    # Generate three variants with optimized sizes for faster testing:
    # 1. Small files (5MB) with low delta (10%)
    # 2. Medium files (25MB) with medium delta (50%)
    # 3. Large files (100MB) with high delta (80%)
    
    variants = [
        ("small", 5, 10),     # 5MB, 10% delta
        ("medium", 25, 50),   # 25MB, 50% delta
        ("large", 100, 80),   # 100MB, 80% delta
    ]
    
    file_pairs = []
    
    for base_name, size_mb, delta_percent in variants:
        original_path, modified_path = generate_file_pair(base_name, size_mb, delta_percent, output_dir)
        file_pairs.append((base_name, original_path, modified_path, size_mb, delta_percent))
    
    print(f"\n✅ Generated {len(variants)} file pairs in {output_dir}:")
    for base_name, original_path, modified_path, size_mb, delta_percent in file_pairs:
        print(f"  {base_name}: {size_mb}MB, {delta_percent}% delta")
        print(f"    Original: {original_path}")
        print(f"    Modified: {modified_path}")
    
    # Save file list for easy reference
    test_files_path = os.path.join(output_dir, "test_files.txt")
    with open(test_files_path, "w") as f:
        f.write("# Test file pairs for superfast_rsync performance testing\n")
        f.write("# Format: name, original_path, modified_path, size_mb, delta_percent\n")
        for base_name, original_path, modified_path, size_mb, delta_percent in file_pairs:
            f.write(f"{base_name},{original_path},{modified_path},{size_mb},{delta_percent}\n")
    
    print(f"\n📝 File list saved to: {test_files_path}")
    
    # Convert file pairs to test_files format for performance testing
    test_files = []
    for base_name, original_path, modified_path, size_mb, delta_percent in file_pairs:
        test_files.append({
            'name': base_name,
            'original_path': original_path,
            'modified_path': modified_path,
            'size_mb': size_mb,
            'delta_percent': delta_percent
        })
    
    print(f"\n📋 Step 2: Running comprehensive performance tests...")
    
    # Run performance tests
    results_file, results = run_comprehensive_performance_tests(test_files, output_dir)
    
    if results_file and results:
        print(f"\n📊 Step 3: Analyzing performance results...")
        analyze_performance_results(results_file, results)
        
        print(f"\n🎉 Comprehensive testing workflow completed successfully!")
        print(f"📁 Test files: {output_dir}")
        print(f"📊 Results: {results_file}")
        print(f"📝 Summary: {test_files_path}")
    else:
        print(f"\n❌ Performance testing failed. Check the output above for errors.")

if __name__ == "__main__":
    main()

