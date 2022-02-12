from setuptools import setup, find_packages

setup(
    name="ingestion",
    version="0.0.1",
    author="Don Isiko",
    author_email="isikodon@gmail.com",
    description="A demo application created to accompany a Python course.",
    keywords="learn python cloud academy",
    url="http://cloudacademy.com",
    packages=find_packages(), # automatically finds packages included in our distribution
    entry_points={"console_scripts": [
        "ingestiond=ingest.backend:main" # executing ingestiond in terminal will run main of backend.py
    ]},
    install_requires=[ # specify dependencies
        "spacy==2.3.2",
        "pydantic==1.5.1",
        "spacy-lookups-data==0.3.2"
    ],
    extras_require={ # specify additional dependencies using extra requires, this is for dev mode
        "dev": [
            "pytest==5.4.3",
        ]
    }

)