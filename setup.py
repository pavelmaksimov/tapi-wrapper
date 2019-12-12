#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os
import re

try:
    import pypandoc

    readme = pypandoc.convert("README.md", "rst")
except (IOError, ImportError):
    readme = ""

package = "tapi"
requirements = ["requests[security]>=2.6", "arrow>=0.6.0,<1", "six>=1"]


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, "__init__.py")).read()
    return re.search("^__version__ = ['\"]([^'\"]+)['\"]", init_py, re.MULTILINE).group(
        1
    )


setup(
    name="tapi-wrapper",
    version=get_version(package),
    description="Обертка для написания библиотек для API",
    long_description=readme,
    author="Pavel Maksimov",
    author_email="vur21@ya.ru",
    url="https://github.com/pavelmaksimov/tapi-wrapper",
    packages=["tapi"],
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords="tapi,tapioca,wrapper,api",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires='>=3.5',
)
