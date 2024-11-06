from setuptools import setup, find_namespace_packages

setup(
    name='KPFTranslator',
    version='2.0.0dev',    
    description='KPFTranslator',
    url='https://github.com/KeckObservatory/KPFTranslator',
    author='Josh Walawender',
    author_email='jwalawender@keck.hawaii.edu',
    license='BSD 2-clause',
#     packages=find_namespace_packages(where='kpf', include=['kpf']),
    packages=['kpf',
              'kpf.ObservingBlocks',
              'kpf.utils',
              ],
    package_data={"kpf.ObservingBlocks": ["*.yaml"]},
    include_package_data=True,
    install_requires=['numpy'],

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',  
        'Operating System :: POSIX :: Linux',        
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)