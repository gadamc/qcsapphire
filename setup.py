# -*- coding: utf-8 -*-
import sys
from setuptools import setup, find_namespace_packages
from src.qcsapphire.__version__ import __version__

requirements = [
    'pyserial',
]

# The README.md file content is included in the package metadata as long description and will be
# automatically shown as project description on the PyPI once you release it there.
with open('README.md', 'r') as file:
    long_description = file.read()


setup(
    name='qcsapphire',  # Choose a custom name
    version=__version__,  # Automatically deduced from "VERSION" file (see above)
    packages=find_namespace_packages(where='src'),  # This should be enough for 95% of the use-cases
    package_dir={'': 'src'},  # same
    package_data={'': ['README.md'],  # include data files
                  },
    description='A package for communicating with the Quantum Composer Sapphire 9200 TTL pulse generator',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/gadamc/qcsapphire',

    license='GPLv3',  # License tag
    install_requires=requirements,  # package dependencies
    python_requires='~=3.8',  # Specify compatible Python versions
)
