from distutils.core import setup

setup(
    name='pyzigate',
    packages=['pyzigate'],
    version='0.1.3.post1',
    description='Interface library for ZiGate (http://zigate./fr)',
    author='Frédéric HARS & Vesa YLIKYLÄ',
    author_email='frederic.hars@gmail.com',
    url='https://github.com/elric91/ZiGate',
    download_url='https://github.com/elric91/ZiGate/archive/v0.1.3.tar.gz',
    keywords=['zigate', 'zigbee', 'python3'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3',
)
