#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os
import re

with open("README.md", "r", encoding="utf8") as fh:
    readme = fh.read()

package = "tapi2"

test_requirements = [
    'responses>=0.5',
    'mock>=1.3,<1.4'
]

def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, "__init__.py")).read()
    return re.search("^__version__ = ['\"]([^'\"]+)['\"]", init_py, re.MULTILINE).group(
        1
    )


setup(
    name="tapi-wrapper2",
    version=get_version(package),
    description='Python API client generator',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Filipe Ximenes',
    author_email='filipeximenes@gmail.com',
    url="https://github.com/pavelmaksimov/tapi-wrapper",
    packages=[package],
    include_package_data=True,
    install_requires=['requests'],
    license="MIT",
    zip_safe=False,
    keywords="tapi,wrapper,api",
    python_requires='>=3.5',
)
