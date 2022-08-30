from setuptools import find_packages, setup

setup(
    name="functionary",
    version="0.1.0",
    packages=find_packages(),
    package_dir={"functionary": "functionary"},
    package_data={
        "functionary": [
            "templates/python/*",
            "templates/javascript/*",
        ]
    },
    include_package_data=True,
    install_requires=[
        "Click>=8.0.0",
        "requests>=2.0.0",
        "rich>=12.5.0",
        "pyyaml>=6.0",
        "python-dotenv>=0.20.0",
    ],
    entry_points={
        "console_scripts": [
            "functionary = functionary.functionary:cli",
        ],
    },
)
