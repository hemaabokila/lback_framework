from setuptools import setup, find_packages

setup(
    name='lback_framework',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'websockets',
    ],
    entry_points={
        'console_scripts': [
            'lback = lback.main:start_server',
        ],
    },
    author="Ibrahem Abo Kila",
    author_email="ibrahemabokila@gmail.com",
    description="A simple web framework",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/hemaabokila/lback_framework",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
