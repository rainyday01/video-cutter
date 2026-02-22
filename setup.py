from setuptools import setup, find_packages

setup(
    name="video-cutter",
    version="1.0.0",
    description="A video cutting tool based on time ranges",
    author="Video Cutter",
    python_requires=">=3.8",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "video-cutter=src.main:main",
        ],
    },
    install_requires=[
        "PyQt6>=6.5.0",
        "openpyxl>=3.1.0",
        "python-dateutil>=2.8.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
