from setuptools import setup, find_packages

setup(
    name="OmniLauncher-MC",
    version="1.0.0",
    author="OmniNodeCo",
    author_email="contact@omninodeco.dev",
    description="A modern Minecraft launcher built with Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/OmniNodeCo/OmniLauncher-MC",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "customtkinter>=5.2.0",
        "Pillow>=10.0.0",
        "requests>=2.31.0",
        "minecraft-launcher-lib>=6.4",
    ],
    entry_points={
        "console_scripts": [
            "omnilauncher-mc=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)