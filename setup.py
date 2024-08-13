from setuptools import setup

setup(
    name='truecomercializadora',
    version='0.5.0',
    description='A comprehensive library to centralize the main functions used across applications and services',
    url='https://github.com/truecomercializadora/truecomercializadora.git',
    author='Ettore Aquino',
    author_email='ettore.aquino@truecomercializadora.com',
    license='GNU AGPLv3',
    packages=['truecomercializadora'],
    install_requires=[
        'gspread==5.11.0',
        'oauth2client==4.1.3',
        'google-auth-httplib2==0.1.1',
        'google-auth-oauthlib==0.4.6',
        'workalendar==17.0.0',
        'pyTelegramBotAPI==4.20.0',
        'urllib3==2.2.2',
        'requests==2.32.3'
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

