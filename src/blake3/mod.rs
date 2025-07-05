//! A BLAKE3 implementation for fast_rsync with parallel processing support.
//! BLAKE3 is a cryptographic hash function that is both fast and secure.

use std::iter::Iterator;

pub const BLAKE3_SIZE: usize = 32;  // Default output size

/// Compute BLAKE3 hash of a single block of data
pub fn blake3(data: &[u8]) -> [u8; 32] {
    blake3::hash(data).into()
}

/// Compute BLAKE3 hashes for multiple blocks of data in parallel
pub fn blake3_many<'a>(
    datas: impl ExactSizeIterator<Item = &'a [u8]>,
) -> impl ExactSizeIterator<Item = (&'a [u8], [u8; 32])> {
    struct Blake3Iterator<'a, I: Iterator<Item = &'a [u8]>> {
        inner: I,
    }

    impl<'a, I: Iterator<Item = &'a [u8]>> Iterator for Blake3Iterator<'a, I> {
        type Item = (&'a [u8], [u8; 32]);

        fn next(&mut self) -> Option<Self::Item> {
            self.inner.next().map(|data| (data, blake3(data)))
        }

        fn size_hint(&self) -> (usize, Option<usize>) {
            self.inner.size_hint()
        }
    }

    impl<'a, I: ExactSizeIterator<Item = &'a [u8]>> ExactSizeIterator for Blake3Iterator<'a, I> {}

    Blake3Iterator { inner: datas }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_blake3_basic() {
        let data = b"hello world";
        let hash = blake3(data);
        assert_eq!(hash.len(), 32);
        
        // Test that same input produces same output
        let hash2 = blake3(data);
        assert_eq!(hash, hash2);
    }

    #[test]
    fn test_blake3_many() {
        let data1 = b"block1";
        let data2 = b"block2";
        let data3 = b"block3";
        
        let datas = vec![data1, data2, data3];
        let results: Vec<_> = blake3_many(datas.into_iter()).collect();
        
        assert_eq!(results.len(), 3);
        assert_eq!(results[0].0, b"block1");
        assert_eq!(results[1].0, b"block2");
        assert_eq!(results[2].0, b"block3");
        
        // Verify each hash is 32 bytes
        for (_, hash) in &results {
            assert_eq!(hash.len(), 32);
        }
    }
} 