from setuptools import find_packages, setup


setup(
    name="voiceclipboard",
    version="0.1.0",
    description="Learnable microphone-driven clipboard shortcuts.",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.26",
        "sounddevice>=0.4.6",
    ],
    entry_points={
        "console_scripts": [
            "voiceclipboard=voiceclipboard.main:main",
        ]
    },
)
