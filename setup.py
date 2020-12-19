import setuptools

with open("readme.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="renderpy",
    version="0.0.1",
    author="Michael C Palmer",
    author_email="michaelcpalmer1980@gmail.com",
    description="A pygame add-on with GPU texture rendering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/",
    packages=setuptools.find_packages(),
    package_data={
        "renderpy": ["data/*.*"],},

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
