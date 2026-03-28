from setuptools import find_packages, setup


setup(
    name="whistleclipboard",
    version="0.1.0",
    description="Learnable whistle-driven clipboard shortcuts.",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.26",
        "sounddevice>=0.4.6",
    ],
    entry_points={
        "console_scripts": [
            "whistleclipboard=whistleclipboard.main:main",
        ]
    },
)
