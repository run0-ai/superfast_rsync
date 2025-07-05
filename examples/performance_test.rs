use superfast_rsync::{Signature, SignatureOptions, diff, apply, HashAlgorithm};
#[cfg(feature = "parallel")]
use superfast_rsync::diff_parallel;
use std::fs;
use std::time::Instant;
use std::io;
use clap::{Command, Arg};

#[derive(Debug)]
struct Config {
    original_file: String,
    modified_file: String,
    hash_algorithm: HashAlgorithm,
    block_size: u32,
    hash_size: u32,
}

fn parse_args() -> Config {
    let matches = Command::new("superfast_rsync_performance_test")
        .version("1.0")
        .about("Performance testing tool for superfast_rsync with BLAKE3 support")
        .arg(Arg::new("original")
            .long("original")
            .short('o')
            .value_name("FILE")
            .help("Original file path")
            .required(true))
        .arg(Arg::new("modified")
            .long("modified")
            .short('m')
            .value_name("FILE")
            .help("Modified file path")
            .required(true))
        .arg(Arg::new("hash")
            .long("hash")
            .short('a')
            .value_name("ALGORITHM")
            .help("Hash algorithm: md4, blake3")
            .value_parser(["md4", "blake3"])
            .default_value("blake3"))
        .arg(Arg::new("block-size")
            .long("block-size")
            .short('b')
            .value_name("BYTES")
            .help("Block size in bytes")
            .default_value("4096"))
        .arg(Arg::new("hash-size")
            .long("hash-size")
            .short('s')
            .value_name("BYTES")
            .help("Hash size in bytes (max: 16 for MD4, 32 for BLAKE3)")
            .default_value("16"))
        .get_matches();
    
    let original_file = matches.get_one::<String>("original").unwrap().clone();
    let modified_file = matches.get_one::<String>("modified").unwrap().clone();
    
    let hash_algo = match matches.get_one::<String>("hash").unwrap().as_str() {
        "blake3" => HashAlgorithm::Blake3,
        "md4" => HashAlgorithm::Md4,
        _ => unreachable!(), // clap ensures valid values
    };
    
    let block_size: u32 = matches.get_one::<String>("block-size").unwrap().parse().unwrap();
    let hash_size: u32 = matches.get_one::<String>("hash-size").unwrap().parse().unwrap();
    
    // Validate hash size
    let max_hash_size = hash_algo.max_hash_size();
    if hash_size > max_hash_size as u32 {
        eprintln!("Warning: hash size {} exceeds maximum {} for algorithm {:?}, using maximum", 
                  hash_size, max_hash_size, hash_algo);
    }
    let hash_size = hash_size.min(max_hash_size as u32);
    
    Config {
        original_file,
        modified_file,
        hash_algorithm: hash_algo,
        block_size,
        hash_size,
    }
}

pub fn main() -> io::Result<()> {
    let config = parse_args();
    
    // Load input files
    let original = fs::read(&config.original_file)?;
    let modified = fs::read(&config.modified_file)?;
    
    println!("🔧 Configuration:");
    println!("   Original file: {}", config.original_file);
    println!("   Modified file: {}", config.modified_file);
    println!("   Hash algorithm: {:?}", config.hash_algorithm);
    println!("   Block size: {} bytes", config.block_size);
    println!("   Hash size: {} bytes", config.hash_size);
    println!();
    
    println!("📄 File Statistics:");
    println!("   Original size: {} bytes ({:.2} MB)", original.len(), original.len() as f64 / 1024.0 / 1024.0);
    println!("   Modified size: {} bytes ({:.2} MB)", modified.len(), modified.len() as f64 / 1024.0 / 1024.0);
    println!("   Size difference: {} bytes", (original.len() as i64 - modified.len() as i64).abs());

    // Step 1: Create SignatureOptions with CLI parameters
    let sig_opts = SignatureOptions {
        block_size: config.block_size,
        crypto_hash_size: config.hash_size,
        hash_algorithm: config.hash_algorithm,
    };

    // Step 2: Generate signature from original
    let t0 = Instant::now();
    let signature = Signature::calculate(&original, sig_opts);
    let t_sig = t0.elapsed();

    // Step 3: Index the signature for fast lookup
    let indexed = signature.index();

    // Step 4: Generate delta between original and modified
    let mut delta = Vec::new();
    let t1 = Instant::now();
    
    #[cfg(feature = "parallel")]
    {
        // Use parallel diff if feature is enabled
        diff_parallel(&indexed, &modified, &mut delta).expect("parallel diff failed");
    }
    #[cfg(not(feature = "parallel"))]
    {
        // Use sequential diff
        diff(&indexed, &modified, &mut delta).expect("diff failed");
    }
    
    let t_diff = t1.elapsed();

    // Step 5: Apply delta to reconstruct modified
    let mut reconstructed = Vec::new();
    let t2 = Instant::now();
    apply(&original, &delta, &mut reconstructed).expect("apply failed");
    let t_apply = t2.elapsed();

    // Step 6: Verify exact match
    assert_eq!(reconstructed, modified);
    println!("✅ Reconstructed matches modified input.");

    // Calculate detailed statistics
    let delta_ratio = delta.len() as f64 * 100.0 / modified.len() as f64;
    let compression_ratio = (1.0 - delta.len() as f64 / modified.len() as f64) * 100.0;
    
    let sig_throughput = original.len() as f64 / t_sig.as_secs_f64() / 1024.0 / 1024.0; // MB/s
    let diff_throughput = modified.len() as f64 / t_diff.as_secs_f64() / 1024.0 / 1024.0; // MB/s
    let apply_throughput = original.len() as f64 / t_apply.as_secs_f64() / 1024.0 / 1024.0; // MB/s
    
    let total_memory = original.len() + modified.len() + delta.len() + reconstructed.len();
    let peak_memory = original.len() + modified.len() + delta.len() + reconstructed.len() + signature.serialized().len();

    // CPU cycles estimation (rough approximation)
    let cpu_freq_ghz = 3.0; // Assume 3GHz CPU - adjust based on your system
    let cycles_per_byte_sig = (t_sig.as_nanos() as f64 * cpu_freq_ghz) / original.len() as f64;
    let cycles_per_byte_diff = (t_diff.as_nanos() as f64 * cpu_freq_ghz) / modified.len() as f64;
    let cycles_per_byte_apply = (t_apply.as_nanos() as f64 * cpu_freq_ghz) / original.len() as f64;

    println!("\n📊 Performance Statistics:");
    println!("   Delta size: {} bytes ({:.2} MB)", delta.len(), delta.len() as f64 / 1024.0 / 1024.0);
    println!("   Delta ratio: {:.2}%", delta_ratio);
    println!("   Compression ratio: {:.2}%", compression_ratio);
    
    println!("\n⏱ Timing Statistics:");
    println!("   Signature generation: {:.2?} ({:.2} MB/s)", t_sig, sig_throughput);
    println!("   Delta generation: {:.2?} ({:.2} MB/s)", t_diff, diff_throughput);
    println!("   Delta application: {:.2?} ({:.2} MB/s)", t_apply, apply_throughput);
    println!("   Total processing time: {:.2?}", t_sig + t_diff + t_apply);
    
    println!("\n🖥️ CPU Statistics (estimated @ {:.1} GHz):", cpu_freq_ghz);
    println!("   Signature cycles/byte: {:.2}", cycles_per_byte_sig);
    println!("   Delta generation cycles/byte: {:.2}", cycles_per_byte_diff);
    println!("   Delta application cycles/byte: {:.2}", cycles_per_byte_apply);
    println!("   Total CPU cycles: {:.0}", (t_sig + t_diff + t_apply).as_nanos() as f64 * cpu_freq_ghz);
    
    println!("\n🧠 Memory Statistics:");
    println!("   Estimated total memory: {:.2} MB", total_memory as f64 / 1024.0 / 1024.0);
    println!("   Peak memory usage: {:.2} MB", peak_memory as f64 / 1024.0 / 1024.0);
    println!("   Signature memory: {:.2} MB", signature.serialized().len() as f64 / 1024.0 / 1024.0);

    // Optional output
    fs::write("patch_output.bin", &delta)?;
    fs::write("reconstructed_output.bin", &reconstructed)?;

    Ok(())
}

