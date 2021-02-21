from setuptools import setup, find_packages

setup(
    name='clockify_kiss',
    version='1.0.1',
    py_modules=['clockify_kiss'],
    author='Sébastien Gérard',
    url='https://github.com/sebge2emasphere/clockify-kiss',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=[
        'click==6.7',
        'certifi==2018.8.13',
        'chardet==3.0.4',
        'click==6.7',
        'idna==2.7',
        'requests>=2.20.0',
        'urllib3==1.24.2',
        'tzlocal==2.0.0'
    ],
    entry_points={
        'console_scripts': [
            'clockifyKiss=kiss:main',
        ],
    }
)
