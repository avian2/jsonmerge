Merge a series of JSON documents
================================

This Python module allows you to merge a series of JSON documents into a
single one.

This problem often occurs for example when different authors fill in
different parts of a common document and you need to construct a document
that includes contributions from all the authors. It also helps when
dealing with consecutive versions of a document where different fields get
updated over time.

Consider a trivial example with two documents::

    >>> base = {
    ...         "foo": 1,
    ...         "bar": [ "one" ],
    ...      }

    >>> head = {
    ...         "bar": [ "two" ],
    ...         "baz": "Hello, world!"
    ...     }

We call the document we are merging changes into *base* and the changed
document *head*. To merge these two documents using *jsonmerge*::

    >>> from pprint import pprint

    >>> from jsonmerge import merge
    >>> result = merge(base, head)

    >>> pprint(result, width=40)
    {'bar': ['two'],
     'baz': 'Hello, world!',
     'foo': 1}

As you can see, when encountering an JSON object, *jsonmerge* by default
returns fields that appear in either *base* or *head* document. For other
JSON types, it simply replaces the older value. These principles are also
applied in case of multiple nested JSON objects.

In a more realistic use case however, you might want to apply different
*merge strategies* to different parts of the document. You can tell
*jsonmerge* how to do that using a syntax based on `JSON schema`_.

If you already have schemas for your document, you can simply expand them
with some additional keywords. Apart from the custom keywords described
below, *jsonmerge* by default uses the schema syntax defined in the `Draft
4`_ of the JSON schema specification.

You use the *mergeStrategy* schema keyword to specify the strategy. The
default two strategies mentioned above are called *objectMerge* for objects
and *overwrite* for all other types.

Let's say you want to specify that the merged *bar* field in the example
document above should contain elements from all documents, not just the
latest one. You can do this with a schema like this::

    >>> schema = {
    ...             "properties": {
    ...                 "bar": {
    ...                     "mergeStrategy": "append"
    ...                 }
    ...             }
    ...         }

    >>> from jsonmerge import Merger
    >>> merger = Merger(schema)
    >>> result = merger.merge(base, head)

    >>> pprint(result, width=40)
    {'bar': ['one', 'two'],
     'baz': 'Hello, world!',
     'foo': 1}

Another common example is when you need to keep a versioned list of values
that appeared in the series of documents::

    >>> schema = {
    ...             "properties": {
    ...                 "foo": {
    ...                     "type": "object",
    ...                     "mergeStrategy": "version",
    ...                     "mergeOptions": { "limit": 5 }
    ...                 }
    ...             },
    ...             "additionalProperties": False
    ...         }
    >>> from jsonmerge import Merger
    >>> merger = Merger(schema)

    >>> rev1 = {
    ...     'foo': {
    ...         'greeting': 'Hello, World!'
    ...     }
    ... }

    >>> rev2 = {
    ...     'foo': {
    ...         'greeting': 'Howdy, World!'
    ...     }
    ... }

    >>> base = None
    >>> base = merger.merge(base, rev1, merge_options={
    ...                     'version': {
    ...                         'metadata': {
    ...                             'revision': 1
    ...                         }
    ...                     }
    ...                 })
    >>> base = merger.merge(base, rev2, merge_options={
    ...                     'version': {
    ...                         'metadata': {
    ...                             'revision': 2
    ...                         }
    ...                     }
    ...                 })
    >>> pprint(base, width=55)
    {'foo': [{'revision': 1,
              'value': {'greeting': 'Hello, World!'}},
             {'revision': 2,
              'value': {'greeting': 'Howdy, World!'}}]}

Note that we use the *mergeOptions* keyword in the schema to supply
additional options to the merge strategy. In this case, we tell the
*version* strategy to retain only 5 most recent versions of this field.

We also used the *merge_options* argument to supply some options that are
specific to each call of the *merge* method. Options specified this
way are applied to all invocations of a specific strategy in a schema (in
contrast to *mergeOptions*, which applies only to the strategy invocation
in that specific location in the schema). Options specified in
*mergeOptions* schema keyword override the options specified in the
*merge_options* argument.

The *metadata* option for the *version* strategy can contain some document
meta-data that is included for each version of the field. *metadata* can
contain an arbitrary JSON object.

Example above also demonstrates how *jsonmerge* is typically used when
merging more than two documents. Typically you start with an empty *base*
and then consecutively merge different *heads* into it.

A common source of problems are documents that do not match the schema used
for merging. *jsonmerge* by itself does not validate input documents. It
only uses the schema to obtain necessary information to apply appropriate merge
strategies. Since the default strategies are used for parts of the
document that are not covered by the schema it's easy to get unexpected
output without any obvious errors raised by *jsonmerge*.

In the following example, the property *Foo* (uppercase F) does not match
*foo* (lowercase f) in the schema and hence the *version* strategy is not
applied as with previous two revisions::

    >>> rev3 = {
    ...     'Foo': {
    ...         'greeting': 'Howdy, World!'
    ...     }
    ... }

    >>> base = merger.merge(base, rev3, merge_options={
    ...                     'version': {
    ...                         'metadata': {
    ...                             'revision': 3
    ...                         }
    ...                     }
    ...                 })

    >>> pprint(base, width=55)
    {'Foo': {'greeting': 'Howdy, World!'},
     'foo': [{'revision': 1,
              'value': {'greeting': 'Hello, World!'}},
             {'revision': 2,
              'value': {'greeting': 'Howdy, World!'}}]}

Hence it is recommended to validate the input documents against the schema
before passing them to *jsonmerge*. This practice is even more effective if
the schema is filled in with more information than strictly necessary for
*jsonmerge* (e.g. adding information about types, restrict valid object
properties with *additionalProperties*, etc.)::

    >>> from jsonschema import validate
    >>> validate(rev1, schema)
    >>> validate(rev2, schema)
    >>> validate(rev3, schema)
    Traceback (most recent call last):
        ...
    jsonschema.exceptions.ValidationError: Additional properties are not allowed ('Foo' was unexpected)

If you care about well-formedness of your documents, you might also want to
obtain a schema for the documents that the *merge* method creates.
*jsonmerge* provides a way to automatically generate it from a schema for
the input document::

    >>> result_schema = merger.get_schema()

    >>> pprint(result_schema, width=80)
    {'additionalProperties': False,
     'properties': {'foo': {'items': {'properties': {'value': {'type': 'object'}}},
                            'maxItems': 5,
                            'type': 'array'}}}

Note that because of the *version* strategy, the type of the *foo* field
changed from *object* to *array*.


Merge strategies
----------------

These are the currently implemented merge strategies.

overwrite
  Overwrite with the value in *base* with value in *head*. Works with any
  type.

discard
  Keep the value in *base*, even if *head* contains a different value.
  Works with any type.

  By default, if *base* does not contain any value (i.e. that part of the
  document is undefined), the value after merge is kept undefined. This can
  be changed with the *keepIfUndef* option. If this option is *true*, then
  the value from *head* will be retained in this case. This is useful if
  you are merging a series of documents and want to keep the value that
  first appears in the series, but want to discard further modifications.

append
  Append arrays. Works only with arrays.

  You can specify a *sortByRef* merge option to indicate the key that will
  be used to sort the items in the array. This option can be an arbitrary
  *JSON pointer*. When resolving the pointer the root is placed at the
  root of the array item. Sort order can be reversed by setting the
  *sortReverse* option.

arrayMergeById
  Merge arrays, identifying items to be merged by an ID field. Resulting
  arrays have items from both *base* and *head* arrays.  Any items that
  have identical an ID are merged based on the strategy specified further
  down in the hierarchy.

  By default, array items are expected to be objects and ID of the item is
  obtained from the *id* property of the object.

  You can specify an arbitrary *JSON pointer* to point to the ID of the
  item using the *idRef* merge option. When resolving the pointer, document
  root is placed at the root of the array item (e.g. by default, *idRef* is
  '/id'). You can also set *idRef* to '/' to treat an array of integers or
  strings as a set of unique values.

  Array items in *head* for which the ID cannot be identified (e.g. *idRef*
  pointer is invalid) are ignored.

  You can specify an additional item ID to be ignored using the *ignoreId*
  merge option.

  A compound ID can be specified by setting *idRef* to an array of
  pointers. In that case, if *any* pointer in the array is invalid for an
  object in *head*, the object is ignored. If using an array for *idRef*
  and if *ignoreId* option is also defined, *ignoreId* must be an array as
  well.

  You can specify a *sortByRef* merge option to indicate the key that will
  be used to sort the items in the array. This option can be an arbitrary
  *JSON pointer*. The pointer is resolved in the same way as *idRef*. Sort
  order can be reversed by setting the *sortReverse* option.

arrayMergeByIndex
  Merge array items by their index in the array. Similarly to
  *arrayMergeById* strategy, the resulting arrays have items from both
  *base* and *head* arrays. Items that occur at identical positions in both
  arrays will be merged based on the strategy specified further down in the
  hierarchy.

objectMerge
  Merge objects. Resulting objects have properties from both *base* and
  *head*. Any properties that are present both in *base* and *head* are
  merged based on the strategy specified further down in the hierarchy
  (e.g. in *properties*, *patternProperties* or *additionalProperties*
  schema keywords).

  The *objClass* option allows one to request a different dictionary class
  to be used to hold the JSON object. The possible values are names that
  correspond to specific Python classes. Built-in names include
  *OrderedDict*, to use the collections.OrderedDict class, or *dict*,
  which uses the Python's dict built-in. If not specified, *dict* is
  used by default.

  Note that additional classes or a different default can be configured via
  the Merger() constructor (see below).

version
  Changes the type of the value to an array. New values are appended to the
  array in the form of an object with a *value* property. This way all
  values seen during the merge are preserved.

  You can add additional properties to the appended object using the
  *metadata* option. Additionally, you can use *metadataSchema* option to
  specify the schema for the object in the *metadata* option.

  You can limit the length of the list using the *limit* option in the
  *mergeOptions* keyword.

  By default, if a *head* document contains the same value as the *base*,
  document, no new version will be appended. You can change this by setting
  *ignoreDups* option to *false*.

If a merge strategy is not specified in the schema, *objectMerge* is used
for objects and *overwrite* for all other values (but see also the section
below regarding keywords that apply subschemas).

You can implement your own strategies by making subclasses of
jsonmerge.strategies.Strategy and passing them to Merger() constructor
(see below).


The Merger Class
----------------

The Merger class allows you to further customize the merging of JSON
data by allowing you to:

- set the schema containing the merge strategy configuration,
- provide additional strategy implementations,
- set a default class to use for holding JSON object data and
- configure additional JSON object classes selectable via the *objClass*
  merge option.

The Merger constructor takes the following arguments (all optional, except
schema):

schema
   The JSON Schema that contains the merge strategy directives
   provided as a JSON object.  An empty dictionary should be provided
   if no strategy configuration is needed.

strategies
   A dictionary mapping strategy names to instances of Strategy
   classes.  These will be combined with the built-in strategies
   (overriding them with the instances having the same name).

objclass_def
   The name of a supported dictionary-like class to hold JSON data by
   default in the merged result. The name must match a built-in name or one
   provided in the *objclass_menu* parameter.

objclass_menu
   A dictionary providing additional classes to use as JSON object
   containers.  The keys are names that can be used as values for the
   *objectMerge* strategy's *objClass* option or the *objclass_def*
   argument. Each value is a function or class that produces an instance of
   the JSON object container. It must support an optional dictionary-like
   object as a parameter which initializes its contents.

validatorclass
    A *jsonschema.Validator* subclass. This can be used to specify which
    JSON Schema draft version will be used during merge. Some details such
    as reference resolution are different between versions. By default, the
    Draft 4 validator is used.


Support for keywords that apply subschemas
------------------------------------------

Complex merging of documents with schemas that use keywords *allOf*,
*anyOf* and *oneOf* can be problematic. Such documents do not have a
well-defined type and might require merging of two values of different
types, which will fail for some strategies. In such cases *get_schema()*
might also return schemas that never validate.

The *overwrite* strategy is usually the safest choice for such schemas.

If you explicitly define a merge strategy at the same level as *allOf*,
*anyOf* or *oneOf* keyword, then *jsonmerge* will use the defined strategy
and not further process any subschemas under those keywords. The
strategy however will descend as usual (e.g. *objectMerge* will take into
account subschemas under the *properties* keyword at the same level as
*allOf*).

If a merge strategy is not explicitly defined and an *allOf* or *anyOf*
keyword is present, *jsonmerge* will raise an error.

If a merge strategy is not explicitly defined and an *oneOf* keyword is
present, *jsonmerge* will continue on the branch of *oneOf* that validates
both *base* and *head*. If no branch validates, it will raise an error.

You can define more complex behaviors by defining for your own strategy
that defines what to do in such cases. See docstring documentation for the
*Strategy* class on how to do that.


Security considerations
-----------------------

A JSON schema document can contain *$ref* references to external schemas.
*jsonmerge* resolves URIs in these references using the mechanisms provided
by the *jsonschema* module. External references can cause HTTP or similar
network requests to be performed.

If *jsonmerge* is used on untrusted input, this may lead to vulnerabilities
similar to the XML External Entity (XXE) attack.


Requirements
------------

*jsonmerge* supports Python 2 (2.7) and Python 3 (3.5 and newer).

You need *jsonschema* (https://pypi.python.org/pypi/jsonschema) module
installed.


Installation
------------

To install the latest *jsonmerge* release from the Python package index::

    pip install jsonmerge


Source
------

The latest development version is available on GitHub:
https://github.com/avian2/jsonmerge

To install from source, run the following from the top of the source
distribution::

    pip install .

*jsonmerge* uses `Tox`_ for testing. To run the test suite run::

    tox


Reporting bugs and contributing code
------------------------------------

Thank you for contributing to *jsonmerge*! Free software wouldn't be
possible without contributions from users like you. However, please consider
that I maintain this project in my free time. Hence I ask you to follow
this simple etiquette to minimize the amount of effort needed to include
your contribution.

Please use `GitHub issues`_ to report bugs. Make sure that your report
includes:

* A *minimal*, but complete, code example that reproduces the problem,
  including any JSON data required to run it. It should be something I can
  copy-paste into a .py file and run.
* Relevant version of *jsonmerge* - either release number on PyPi or git
  commit hash.
* Copy of the traceback, in case you are reporting an unhandled exception.
* Example of what you think should be the correct output, in case you are
  reporting wrong result of a merge or schema generation.

Please use `GitHub pull requests`_ to contribute code. Make sure that your
pull request:

* Passes all existing tests and includes new tests that cover added code.
* Updates *README.rst* to document added functionality.


License
-------

Copyright 2022, Tomaz Solc <tomaz.solc@tablix.org>

The MIT License (MIT)

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

.. _JSON schema: http://json-schema.org
.. _Draft 4: http://json-schema.org/specification-links.html#draft-4
.. _Tox: https://tox.readthedocs.io/en/latest/
.. _GitHub issues: https://github.com/avian2/jsonmerge/issues
.. _GitHub pull requests: https://github.com/avian2/jsonmerge/pulls

..
    vim: tw=75 ts=4 sw=4 expandtab softtabstop=4
