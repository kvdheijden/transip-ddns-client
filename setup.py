import setuptools
import importlib

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = f.read().split()

base_url = 'https://github.com/kvdheijden/transip-ddns-client'

setuptools.setup(
    name='transipddnsclient',
    version=getattr(importlib.import_module('transipddnsclient'), '__version__'),
    description='TransIP dDNS Client',
    url=base_url,
    author='kvdheijden',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7'
    ],
    keywords='dynamic dns transip ddns',
    project_urls={
        'Documentation': base_url + '/wiki',
        'Source': base_url,
        'Tracker': base_url + '/issues',
    },
    packages=setuptools.find_packages(include=['transipddnsclient', 'transipddnsclient.*']),
    py_modules=[],
    install_requires=requirements,
    python_requires='>=3.7',
    package_data={},
    data_files=[],
    entry_points={},
    author_email='koen@kvdheijden.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
)
