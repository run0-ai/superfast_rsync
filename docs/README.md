# Superfast rsync Documentation

This directory contains comprehensive documentation for the `superfast_rsync` library.

## Documentation Structure

### API Documentation (`api/`)
- Complete API reference
- Generated from code documentation
- Available at `target/doc/superfast_rsync/index.html`

### Examples (`examples/`)
- Code examples and tutorials
- Step-by-step guides
- Best practices

### Performance (`performance/`)
- Performance analysis and benchmarks
- Optimization guides
- Comparison with other implementations

## Building Documentation

To generate the documentation:
```bash
cargo doc --release --no-deps
```

To view the documentation in your browser:
```bash
cargo doc --open
```

## Documentation Standards

- All public APIs should be documented with `///` comments
- Examples should be included in documentation comments
- Performance characteristics should be noted where relevant
- Error conditions should be clearly documented

## Contributing to Documentation

When adding new features:
1. Add comprehensive documentation comments
2. Include usage examples
3. Update relevant documentation files
4. Test that documentation builds correctly 