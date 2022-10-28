from setuptools import setup

import os
def package_files(root, sub):
    paths = []
    directory = os.path.join(root,sub)
    print(directory)
    for (path, directories, filenames) in os.walk(directory):
        for filename in directories:
            paths.append(os.path.join(path, filename, '*')[len(root):])
            print(paths[-1])
    return paths

with open("readme.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="renderpyg",
    version="0.1.0",
    author="Michael C Palmer",
    author_email="michaelcpalmer1980@gmail.com",
    description="A pygame add-on with GPU texture rendering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mcpalmer1980/renderpyg",
    packages=['renderpyg'],
    package_data={
        "renderpyg": ["data/*.*"],},

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
