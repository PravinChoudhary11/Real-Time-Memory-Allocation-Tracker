from setuptools import setup, find_packages

setup(
    name="memory-tracker",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "tracemalloc",
        "pympler",
        "objgraph",
        "psutil",
        "pandas",
        "numpy",
        "scikit-learn",
        "dash",
        "plotly",
        "matplotlib",
        "networkx",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="Real-Time Memory Allocation Tracker for Python applications",
    keywords="memory, profiling, tracking, debugging",
    python_requires=">=3.8",
)