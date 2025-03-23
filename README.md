# Real-Time Memory Allocation Tracker

A comprehensive tool for monitoring, analyzing, and visualizing memory usage in Python applications during execution.

## Features

- Real-time tracking of memory allocations and deallocations
- Memory leak detection and analysis
- Object lifetime monitoring
- Allocation source identification with stack traces
- Interactive visualizations and dashboards
- Low-overhead profiling suitable for production use

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from memory_tracker import MemoryTracker

# Initialize the tracker
tracker = MemoryTracker()

# Start tracking
tracker.start()

# Your code here
# ...

# Stop tracking
tracker.stop()

# Generate report
tracker.generate_report("memory_report")

# Launch interactive dashboard
tracker.launch_dashboard()
```

## Examples

See the `examples/` directory for complete usage examples:

- `simple_example.py`: Basic usage of the memory tracker
- `memory_leak_example.py`: Detecting and analyzing memory leaks
- `multi_threaded_example.py`: Tracking memory in multi-threaded applications

## Documentation

For detailed documentation and API reference, see the [docs/](docs/) directory.

## License

MIT