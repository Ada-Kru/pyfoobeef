import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyfoobeef",
    version="0.9.0.1",
    author="Adam Krueger",
    author_email="adamkru@gmail.com",
    description=(
        "Allows control of the Foobar2000 and DeaDBeeF media players in "
        "Python through the beefweb plugin."
    ),
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/Ada-Kru/pyfoobeef",
    keywords="Foobar2000 DeaDBeeF Media Player Beefweb Music Audio",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Natural Language :: English",
    ],
    python_requires=">=3.6",
    install_requires=["urllib3", "aiohttp>=3", "aiohttp-sse-client"],
    test_suite="tests",
    tests_require=["asynctest"],
)
