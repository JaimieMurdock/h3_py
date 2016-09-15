import setuptools
import glob

setuptools.setup(
        name='h3_py',
        version='1.0.dev1',
        description='Heritrix automation via REST API',
        url='https://github.com/adam-miller/h3_py',
        author='Adam Miller',
        author_email='adam@archive.org',
        long_description=open('README.rst').read(),
        license='Apache License 2.0',
        packages=['h3_py'],
        install_requires=['lxml>=3.6.4', 'PyYAML>=3.11', 'requests>=2.11.1'],
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python :: 3.4',
            'Topic :: System :: Archiving',
        ],
        entry_points={
            'console_scripts': [
                'h3_control=h3_py.h3_control:main',
            ],
        },
        data_files=[(
            'config',['config/config.yaml'])
        ])