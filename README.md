Python WVA Library
==================

This library contains a set of classes and functions for performing common
operations using the WVA Web Services API.  It contains both general
web services helpers (using the Python requests library) as well
as more specific helpers.

In addition, packaged with the library is a command-line utility
using the API that serves as both an example of how the library
may be used as well as a convenient tool for developer use.

Installation
------------

The library may be installed using pip by doing the following:

    pip install wva

This will install both the library and command-line application.

CLI Usage
---------

Help for the CLI application can be obtained by running the
application with the `--help` option.  This will show the available
commands:

```
# Get General Help
$ wva --help
<TBD>

# Get help for a specific command
$ wva <command> --help
```

The first time you attempt to talk to a device, you will need
to provide credentials for talking to the device.  The CLI
application will then store those credentials in the file
`~/.wva/credentials` and attempt to use those credentials in
the future.  If the credentials are ever invalid, you will
be prompted to enter the credentials again.

You can clear the credentials that are stored by deleting
the wva configuration or by running the following command:

```
$ wva --clear-credentials
```

To avoid having to enter credentials at all (and avoid the lookup
with the stored config), you may execute commands with the following
syntax:

```
$ wva --user="user" --password="password" <command>
```

Library Usage
-------------

Full API documentation for the library may be found at <TODO: doc link>.
Basic usage of the library looks something like this:

```python
from wva import WVA

wva = WVA("<ip>", "user", "password")
# ...
```

License
-------

This software is open-source. Copyright (c), Digi International Inc., 2015.

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
If a copy of the MPL was not distributed with this file, you can obtain one at
http://mozilla.org/MPL/2.0/.
