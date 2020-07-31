""" Setup script to install the Ringing Room Bot. """

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("wheatley/version.txt", "r") as fh:
    version = fh.read()

setuptools.setup(
    name="wheatley",
    version=version,

    author="Ben White-Horne",
    author_email="kneasle@gmail.com",

    description="A program that will ring any set of bells in Ringing Room.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    url="https://github.com/Kneasle/wheatley/",

    license="MIT",
    platforms="any",

    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.6',
    install_requires=[
        "numpy",
        "requests",
        "python-socketio",
        "websocket-client"
    ],
    package_data={"wheatley": ["version.txt"]},

    entry_points={'console_scripts': ['wheatley = wheatley.main:main']}
)
