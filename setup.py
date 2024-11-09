from setuptools import setup, find_packages

setup(
    name="expense-tracker",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'tkcalendar',
        'matplotlib',
        'pandas',
    ],
    entry_points={
        'console_scripts': [
            'expense-tracker=expense_tracker_gui:main',
        ],
    },
    author="Rajarshi Pattanayak",
    author_email="pattanayakrajarshi@gmail.com",
    description="A simple expense tracking application with GUI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Rajarshi-pattanayak/expense-tracker",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
