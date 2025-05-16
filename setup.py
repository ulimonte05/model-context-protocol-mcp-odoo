from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-odoo",
    version="0.1.0",
    author="Albert Gil López",
    author_email="albert.gil@yourtechtribe.com",
    description="Model Context Protocol server for Odoo integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourtechtribe/model-context-protocol-mcp-odoo",
    packages=['mcp_odoo_public'] + find_packages(),
    package_dir={'mcp_odoo_public': '.'},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastmcp>=1.6.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "asyncio>=3.4.3"
    ],
    entry_points={
        "console_scripts": [
            "mcp-odoo = mcp_odoo_public.__main__:main",
        ],
    },
) 