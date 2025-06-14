from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="goodbooks_recommender",
    version="0.1.0",
    author="Swanand",
    author_email="swanand@example.com",
    description="A hybrid book recommendation system using content-based and collaborative filtering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Swanand/GoodBooksRecommender",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "goodbooks-pipeline=run_pipeline:main",
        ],
    },
    include_package_data=True,
    package_data={
        "goodbooks_recommender": ["data/*", "models/*", "reports/*"],
    },
)