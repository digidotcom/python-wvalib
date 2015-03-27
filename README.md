Python WVA Library
==================

[Full Documentation](https://digidotcom.github.io/python-wvalib)

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
$ wva --help
Usage: wva [OPTIONS] COMMAND [ARGS]...

  Command-line interface for interacting with a WVA device

Options:
  --https / --no-https  Use HTTPS instead of HTTP
  --hostname TEXT       Force use of the specified hostname
  --username TEXT       Force use of the specified username
  --password TEXT       Force use of the specified password
  --config-dir TEXT     Directory containing wva configuration files
  --help                Show this message and exit.

Commands:
  cliconfig      View and clear CLI config
  delete         DELETE the specified URI Example: $ wva get...
  get            Perform an HTTP GET of the provided URI The...
  post           POST file data to a specific URI Note that...
  put            PUT file data to a specific URI Example: $...
  subscriptions  View and Edit subscriptions
  vehicle        Vehicle Data Commands
```

You can get help for a specific command by specifying `--help` after
the command.  For instance,

```
$ wva subscriptions --help
Usage: wva subscriptions [OPTIONS] COMMAND [ARGS]...

  View and Edit subscriptions

Options:
  --help  Show this message and exit.

Commands:
  add     Add a subscription with a given short_name...
  clear   Remove all registered subscriptions Example:...
  delete  Delete a specific subscription by short name
  graph   Present a live graph of the incoming...
  list    List short name of all current subscriptions
  listen  Output the contents of the WVA event stream...
  show    Show metadata for a specific subscription...
```

The first time you attempt to talk to a device, you will need
to provide credentials for talking to the device.  The CLI
application will then store those credentials in the file
`~/.wva/config.json` and attempt to use those credentials in
the future.  If the credentials are ever invalid, you will
be prompted to enter the credentials again.

You can clear the credentials that are stored by deleting
the wva configuration or by running the following command:

```
$ wva cliconfig clear
```

Library Usage and Examples
--------------------------

See the [Full API documentation](https://digidotcom.github.io/python-wvalib) for
full details on the API and its usage.  Here's some examples:

### Subscribe to event streams

```python
from wva import WVA
wva = WVA("<ip>", "user", "password")

# clear any existing subscriptions
for sub in wva.get_subscriptions():
    sub.delete()

# add subscriptions for some pieces of vehicle data
wva.get_subscription("speed").create("vehicle/data/VehicleSpeed", interval=3)
wva.get_subscription("rpm").create("vehicle/data/EngineSpeed", interval=5)

# receive vehicle data and print it
def data_received(data):
    print("<- {}".format(data))

es = wva.get_event_stream()
es.add_event_listner(data_received)
es.enable()
```

### Sample vehicle data

```python
from wva import WVA
from wva.exceptions import WVAHttpServiceUnavailableError

wva = WVA("<ip>", "user", "password")

# print out all available data elements and whether
# they currently have data or not
for name, element in wva.get_vehicle_data_elements().items():
    try:
        curval = element.sample()
    except WVAHttpServiceUnavailableError:
        print("{} (Unavailable)".format(name))
    else:
        print("{} = {} at {}".format(name, curval.value, curval.timestamp.ctime()))
```

### Make direct web services calls

```python
from wva import WVA

wva = WVA("<ip>", "user", "password")

client = wva.get_http_client()

# write a hello.py file to the python filesystem
client.put("/files/userfs/WEB/python/hello.py".format(relpath), "print 'Hello, World!'\n")

# print the contents of hello.py on the target to the screen
print(client.get("/files/userfs/WEB/python/hello.py"))

# delete hello.py
client.delete("/files/userfs/WEB/python/hello.py")
```

Contributing and Developer Information
--------------------------------------

Contributions to the project are very welcome.  Please submit any
issues you find on the github issue tracker.  If you have a change you
would like to have included in the library, please submit a pull
request.

Information for developers on coding style, how to run the tests,
etc. may be found in the [Developer's README](README-dev.md).

Support
-------

This library is in "Alpha" currently and is not tested beyond the unit
tests included in the code and basic developer testing.  Prior to a
1.0 release, the APIs may change in backwards incompatible ways at
each minor revision.

If you run into issues, please create an issue on the project's
[Github Page](https://github.com/digidotcom/python-wvalib).

License
-------

This software is open-source. Copyright (c), Digi International Inc., 2015.

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
If a copy of the MPL was not distributed with this file, you can obtain one at
http://mozilla.org/MPL/2.0/.

Digi, Digi International, the Digi logo, the Digi website, and Digi
Device Cloud are trademarks or registered trademarks of Digi
International, Inc. in the United States and other countries
worldwide. All other trademarks are the property of their respective
owners.

THE SOFTWARE AND RELATED TECHNICAL INFORMATION IS PROVIDED "AS IS"
WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL DIGI OR ITS
SUBSIDIARIES BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION IN CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
OF OR IN CONNECTION WITH THE SOFTWARE AND TECHNICAL INFORMATION
HEREIN, INCLUDING ALL SOURCE AND OBJECT CODES, IRRESPECTIVE OF HOW IT
IS USED. YOU AGREE THAT YOU ARE NOT PROHIBITED FROM RECEIVING THIS
SOFTWARE AND TECHNICAL INFORMATION UNDER UNITED STATES AND OTHER
APPLICABLE COUNTRY EXPORT CONTROL LAWS AND REGULATIONS AND THAT YOU
WILL COMPLY WITH ALL APPLICABLE UNITED STATES AND OTHER COUNTRY EXPORT
LAWS AND REGULATIONS WITH REGARD TO USE AND EXPORT OR RE-EXPORT OF THE
SOFTWARE AND TECHNICAL INFORMATION.
