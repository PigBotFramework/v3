from setuptools import setup,find_packages

setup(
    name='pbf',
    version='0.1',
    author='xzyStudio',
    author_email='gingmzmzx@gmail.com',
    description='The cli of PigBotFramework.',
    install_requires=[
        'click'
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts':[
            'pbf=pbf_tools.cli:cli'
        ]
    }
)