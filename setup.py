from setuptools import setup, find_namespace_packages

setup(
    name="disco-sui",
    version="0.1.0",
    packages=find_namespace_packages(include=["src.*"]),
    package_dir={"": "."},
    install_requires=[
        "openai",
        "smolagents[gradio]",
        "python-dotenv",
        "gradio>=5.13.2",
    ],
) 