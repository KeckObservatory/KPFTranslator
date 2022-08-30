from setuptools import setup, find_packages

NAME = 'kpf_translator'
VERSION = '0.1.1'
RELEASE = 'dev' not in VERSION
AUTHOR = "Josh Walawender"
AUTHOR_EMAIL = "jwalawender@keck.hawaii.edu"
LICENSE = "3-clause BSD"
DESCRIPTION = "The KPF Translator Module"

scripts = []

# Define entry points for command-line scripts
entry_points = {
    'console_scripts': [
        "kpftranslator = ddoitranslatormodule.cli_interface:main",
    ]
    }

setup(name=NAME,
      provides=NAME,
      version=VERSION,
      license=LICENSE,
      description=DESCRIPTION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      packages=find_packages(),
      package_dir={"": "."},
      package_data={'kpf': ['*']},
      scripts=scripts,
      entry_points=entry_points,
      install_requires=[],
      python_requires=">=3.6"
      )
