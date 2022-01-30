from distutils.core import setup

readme = ''
with open('README.md', encoding='utf-8') as fp:
    readme = fp.read()

setup(
    name='pyzandronum',
    version='0.2.0',
    license='MIT',
    description='Simple Python module for Zandronum server talking.',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='hat_kid',
    url='https://github.com/thehatkid/pyzandronum',
    packages=['pyzandronum'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Typing :: Typed'
    ]
)
