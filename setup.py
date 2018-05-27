"""A setuptools based setup module.
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='floopcli',
    version='0.0.1a6',
    description='sensor development and testing tools',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/ForwardLoopLLC/floopcli',
    author='Forward Loop LLC',
    author_email='nick@forward-loop.com', 
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='sensor development devops',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=[
            'argparse==1.4.0',
            'mypy==0.590',
            'pytest==3.5.1',
            'pytest-cov==2.5.1',
            'pyyaml==3.12',
            'sphinx==1.7.4',
            'sphinx-tabs==1.1.7'
            ],  
    # If there are data files included in your packages that need to be
    # installed, specify them here.
    #
    # If using Python 2.6 or earlier, then these have to be included in
    # MANIFEST.in as well.
    #package_data={  # Optional
    #    'sample': ['package_data.dat'],
    #},

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    #
    # For example, the following would provide a command called `sample` which
    # executes the function `main` from this package when invoked:
    entry_points={
        'console_scripts': [
            'floop=floopcli.__main__:main'
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/ForwardLoopLLC/floopcli/issues',
        'Source': 'https://github.com/ForwardLoopLLC/floopcli/issues',
    },
)
