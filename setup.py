from setuptools import setup, find_packages

setup(
    name='bg_cli',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['Click'],
    entry_points={
        'console_scripts': [
            'bg-cli = cli.bg_cli:cli',
        ],
    },
)
