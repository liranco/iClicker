from setuptools import setup, find_packages

setup(
    name='iClicker',
    version='1',
    packages=find_packages(),
    url='https://github.com/saligal/iClicker',
    license='',
    author='Liran Cohen',
    author_email='saligal777@gmail.com',
    description='iClicker!',
    install_requires=[
        'PySide',
        'pyserial'
    ]
)
