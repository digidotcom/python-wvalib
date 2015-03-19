Developer's Guide
=================

For general documentation for this library, plese refer to
[README.md](README.md).  The content here is targetted for
developer's looking to make changes to the code itself.

Please note that this library is licensed under the terms of the MPL
v2.0, so you are free to make changes to the library without having to
contribute those changes back (see https://www.mozilla.org/MPL/2.0/).
That being said, contributions are welcome and would be greatly
appreciated.

Setting up your development environment
---------------------------------------

We recommend that developer's use
[virtualenv](https://virtualenv.pypa.io/en/latest/) and
[pip](https://pypi.python.org/pypi/pip) for development.  With those
tools installed and the code checked out, the following can be done to
get a basic development environment set up (under Linux).  The same
basic instructions should apply to any OS but may require some tweaks:

```
$ virtualenv env
$ source env/bin/activate
$ pip install -r dev-requirements.txt
```

The last line will install all requirements for both the library and
dependencies for running the tests.

Running the Tests
-----------------

The quickest way to run the unittests for the library is to do the
following (with your virtualenv activiated):

```
$ nosetests .
```

As the library supports multiple versions of the interpreter, there is
also a script included which aids in testing the code against all
supported versions of the interpreter.  This script makes use of
[pyenv](https://github.com/yyuu/pyenv) and
[tox](https://tox.readthedocs.org/en/latest/).  This testing script is
only supported under Linux.  Since pyenv must download and build all
required interpreters from source, it may take quite a while to run
the first time.

```
$ ./toxtests.sh
```

If you run into problems, you may need to install some additional
dependencies as described
[in the pyenv documentation](https://github.com/yyuu/pyenv/wiki/Common-build-problems).

Once you have run toxtests.sh successfully once, you can quickly test
with a specific version of the interpreter by running nosetests out of
the tox environment for the desired version of the interpreter:

```
$ .tox/py34/bin/nosetests .
```

Coding Standards
----------------

All contributions to the library must comply with the style guidelines
documented in [PEP8](https://www.python.org/dev/peps/pep-0008/).  The
[pep8 checker](https://pypi.python.org/pypi/pep8) may be used to
ensure that problems are found prior to code review.
