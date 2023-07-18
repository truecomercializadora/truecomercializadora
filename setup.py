from setuptools import setup

setup(
    name='truecomercializadora',
    version='0.3.1',
    description='A comprehensive library to centralize the main functions used across applications and services',
    url='https://github.com/truecomercializadora/truecomercializadora.git',
    author='Ettore Aquino',
    author_email='ettore.aquino@truecomercializadora.com',
    license='GNU AGPLv3',
    packages=['truecomercializadora'],
    install_requires=[
        'gspread',
        'oauth2client',
        'numpy',
        'pandas',
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib',
    ],
    classifiers=[
        'Development Status :: 0 - Beta',
        'Programming Language :: Python :: 3.7',
        'Topic :: Comercializacao Energia :: Data Processing',
      ],
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['nose'],
    zip_safe=False
)

