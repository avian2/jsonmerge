Merge a series of JSON documents
================================

This Python module allows you to merge a series of JSON documents into a
single one. A trivial example of this would be:

Document A::

    {
        "foo": 1
    }

Document B::

    {
        "bar": 2
    }

Result of the merge::

    {
        "foo": 1,
        "bar": 2,
    }

Real life documents typically involve more complicated merge operations.
For example, what happens when both A and B contain a *foo* property? Are
arrays in the document appended, replaced or merged item-by-item?

jsonmerge allows you to specify merge strategies for each object, array and
value in the document. The specification is based on JSON Schema. On each
level of the hierarchy, the *mergeStrategy* keyword specifies the merge
strategy used for that instance.

*mergeOptions* keyword specifies any options for the selected strategy.


Module content
--------------

The module exports a Merger class::

    >>> from jsonmerge import Merger

    # load schema document
    >>> schema = {}
    >>> merger = Merger(schema)

    # start with an empty base document
    >>> base = None

    # load version 1 of the document and merge it into base)
    >>> v1 = {'foo': 1}
    >>> base = merger.merge(base, v1)

    # load version 2 of the document and merge it into base)
    >>> v2 = {'bar': 2}
    >>> base = merger.merge(base, v2)

    >>> base
    {'foo': 1, 'bar': 2}

The module can also make a schema for the merged document::

    >>> merger.get_schema()
    {}


Merge strategies
----------------

These are the currently implemented merge strategies. Here *base* refers to
the old document you are merging changes into and *head* refers to the
newer document.

overwrite
  Overwrite with the value in *base* with value in *head*. Works with any
  type.

append
  Append arrays. Works only with arrays.

objectMerge
  Merge objects. Resulting objects have properties from both *base* and
  *head*. Any properties that are present both in *base* and *head* are
  merged based on the strategy specified further down in the hierarchy
  (e.g. in *properties*, *patternProperties* or *additionalProperties*
  schema keywords).

version
  Changes the type of the value to an array. New values are appended to the
  array in the form of an object with a *value* property. This way all
  values seen during the merge are preserved.

  You can limit the length of the list using the *limit* option in the
  *mergeOptions* keyword.

If a merge strategy is not specified in the schema, *objectMerge* is used
to objects and *overwrite* for all other values.


Limitations
-----------

Schemas that do not have a well-defined type (e.g. schemas using *allOf*,
*anyOf* and *oneOf*) do not work well. Documents conforming to such schemas
could require merging, for example, a string to an object.


Requirements
------------

You need *jsonschema* (https://pypi.python.org/pypi/jsonschema) module
installed.


Installation
------------

You install Unidecode, as you would install any Python module, by running
these commands::

    python setup.py install
    python setup.py test


Source
------

The latest version is available on GitHub: https://github.com/avian2/jsonmerge


License
-------

Copyright 2014, Tomaz Solc <tomaz.solc@tablix.org>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

..
    vim: tw=75
