from setuptools import setup

setup(name='twittytwister',
    version='0.1.1',
    description='Twitter client for Twisted Python',
    author='Dustin Sallings',
    author_email='dustin@spy.net',
    url='http://github.com/dustin/twitty-twister/',
    license='MIT',
    platforms='any',
    packages=['twittytwister'],
    install_requires=[
        'oauth',
        'simplejson',
        'Twisted',
        'treq',
    ]
)
