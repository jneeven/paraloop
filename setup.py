from setuptools import find_packages, setup


def requires(filename: str):
    return open(filename).read().splitlines()


setup(
    name="paraloop",
    version="0.0.1.dev1",
    author="Jelmer Neeven",
    author_email="jelmer@neeven.tech",
    license="MIT",
    description="Simple Python for-loop parallelization",
    keywords="for loop parallel multiprocess python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    platforms=["Linux"],
    packages=find_packages(),
    install_requires=requires("requirements.txt"),
    extras_require={"dev": requires("dev-requirements.txt")},
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
