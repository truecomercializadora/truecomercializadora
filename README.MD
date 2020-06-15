# TRUE COMERCIALIZADORA PYTHON LIBRARY

A comprehensive library to centralize the main functions used across applications and services.

A lot of the company services share common functions and datasets. It is also usual for them to compare results between each other. Having a centralized library makes sure updates in datasets and functions will affect all the services and applications across the enterprise, avoiding miscalculations and errors.

## INSTALLATION

``` pip install git+https://github.com/truecomercializadora/truecomercializadora.git ```

Where `bitbucket_username` should be your username in bitbucket with access to the **truecomercializadora** library.

Keep in mind that this library grows fast, so make sure your application points to the proper version, otherwise you are risking failure. Example:

```pip install git+https://github.com/truecomercializadora/truecomercializadora.git@v0.2.2```

It is extremely important to **ALWAYS** deploy the package in a version, as the _master_ branch will always be pointing to the latest version. This way, the library user could choose to install the default version (latest) or a specific version.

## UPGRADE

In order to upgrade the installed library to the latest version:

```pip install git+https://github.com/truecomercializadora/truecomercializadora.git --upgrade```


## CONSIDERATIONS AND LIBRARY STRUCTURE

### Utils
Should contain generic code, code that could be used outside the enterprise domain. Utils need to be organized according to their subject, e.g Datetime, Files, Zipfiles, Http, Math. Or according to a specific external library, such as `boto3`, `zipfile`, `requests` and etc.

___
[`utils_datetime`](truecomercializadora/utils_datetime.py)

___
[`utils_files`](truecomercializadora/utils_files.py)

___
[`utils_gsheets`](truecomercializadora/utils_gsheets.py):

 - **credentials.json**
  
    Necessary for the utility to work. The file is used in order to authenticate the library. Keep it inside the root directory of your project as it will not be packaged within the library.

[`utils_http`](truecomercializadora/utils_http.py)

### AWS Utils
Some tools are specific to the AWS domain. This tools are related to specific services within the vendor which are accessible through `boto3` python library:

[utils_s3](truecomercializadora/utils_s3.py)

[utils_ses](truecomercializadora/utils_ses.py)


### Domain Specific Modules
Should contain code to be reused based on a specific subject. The size of the module does not matter as long as it is consistend with the sub-domain under its care.
___
[`ons`](truecomercializadora/ons.py)
___
[`decomp`](truecomercializadora/decomp.py)

[`encadeado`](truecomercializadora/encadeado.py)

[`prevs`](truecomercializadora/prevs.py)

[`dadger`](truecomercializadora/dadger.py)

[`ccee`](truecomercializadora/ccee.py)

### TYPES!
Whenever possible, avoid using Python specific data types in function returns. Imagine a context where this library might be in use in a serverless application, publish and request operations can only use strings, `datatetime.date`, `datetime.dateime`, `numpy.ndarray` etc, cannot be parsed to `str` using `json.dumps()` or other typical method so, avoid returning theses types in a context where such functions might be used to publish a message or post to a REST API.

### Files