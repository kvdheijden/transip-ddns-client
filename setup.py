import setuptools
import importlib

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name='ddns_kvdheijden',
    version=getattr(importlib.import_module('ddns'), '__version__'),
    description='dynamic DNS updater',
    url='https://github.com/kvdheijden/ddns',
    author='kvdheijden',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
    ],
    keywords='dynamic dns ddns',
    project_urls={
        'Documentation': '',
        'Funding': '',
        'Say Thanks!': '',
        'Source': 'https://github.com/kvdheijden/ddns/',
        'Tracker': 'https://github.com/kvdheijden/ddns/issues',
    },
    packages=setuptools.find_packages(include=['ddns', 'ddns.*']),
    py_modules=[],
    install_requires=['requests~=2.25.1'],
    python_requires='>=3.7',
    package_data={},
    data_files=[],
    entry_points={},
    author_email='koen@kvdheijden.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
)
