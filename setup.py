import setuptools


def get_long_description():
    with open("README.md", "r") as readme:
        return readme.read()


setuptools.setup(
    name="bakeup",
    version="0.1.0rc2",
    author="Renaud Gaspard",
    author_email="gaspardrenaud@hotmail.com",
    description="Cokking a backup has never been that easy",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/Renaud11232/bakeup",
    packages=setuptools.find_packages(),
    entry_points=dict(
        console_scripts=[
            "bakeup=bakeup.command_line:main"
        ]
    ),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Linux",
    ],
)
