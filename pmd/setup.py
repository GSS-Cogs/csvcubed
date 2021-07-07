from setuptools import setup, find_packages

setup(
    version="0.0.1",
    install_requires=[
        "appdirs==1.4.4",
        "attrs==21.2.0",
        "behave==1.2.6",
        "black==19.10b0; python_version >= '3.6'",
        "cached-property==1.5.2",
        "cerberus==1.3.4",
        "certifi==2021.5.30",
        "chardet==4.0.0",
        "click==8.0.1",
        "colorama==0.4.4",
        "csvw==1.11.0",
        "distlib==0.3.2",
        "docker==5.0.0",
        "idna==2.10",
        "isodate==0.6.0",
        "nose==1.3.7",
        "numpy==1.20.3",
        "orderedmultidict==1.0.1",
        "packaging==20.9",
        "pandas==1.2.4",
        "parse==1.19.0",
        "parse-type==0.5.2",
        "pathspec==0.8.1",
        "pep517==0.10.0",
        "pip-shims==0.5.3",
        "pipenv-setup==3.1.1",
        "pipfile==0.0.2",
        "plette[validation]==0.2.3",
        "pyparsing==2.4.7",
        "python-dateutil==2.8.1",
        "pytz==2021.1",
        "rdflib==5.0.0",
        "rdflib-jsonld==0.5.0",
        "regex==2021.4.4",
        "requests==2.25.1",
        "requirementslib==1.5.16",
        "rfc3986==1.5.0",
        "six==1.16.0",
        "toml==0.10.2",
        "tomlkit==0.7.2",
        "typed-ast==1.4.3",
        "uritemplate==3.0.1",
        "urllib3==1.26.5",
        "vistir==0.5.2",
        "websocket-client==1.1.0",
        "wheel==0.36.2",
    ],
    name="pmd",
    packages=find_packages(exclude=["tests"]),
    entry_points={"console_scripts": ["pmdutils=pmd.main:main"]},
)
