from setuptools import setup, find_packages

setup(
    name='bg_cli',
    version='0.1.0',
    packages=find_packages(),
    package_dir={'bg_cli': 'bg_cli'},
    package_data={'bg_cli': [
        'templates/python/*',
        'templates/javascript/*',
    ]},
    include_package_data=True,
    install_requires=[
        'Click>=8.0.0',
        'requests>=2.0.0',
        'pyyaml>=6.0',
        'python-dotenv>=0.20.0',
    ],
    entry_points={
        'console_scripts': [
            'bg-cli = bg_cli.bg_cli:cli',
        ],
    },
)
