from copy import deepcopy

import pytest

from jsonmerge import Merger, merge
from jsonmerge.resolver import LocalRefResolver
from jsonschema.exceptions import RefResolutionError
from jsonschema.validators import RefResolver


@pytest.mark.parametrize('path', [('',), ('', '', 'value'), ('outer', ''), ('', 'a/b', '~key', '')])
@pytest.mark.parametrize('base_exists', [False, True])
def test_merge_empty_keys(path, base_exists):
    base, head, expected = {'old': 1}, {'new': 2}, {'old': 1, 'new': 2}
    for key in reversed(path):
        base, head, expected = {key: base}, {key: head}, {key: expected}
    before = deepcopy((base, head))
    assert merge(base if base_exists else None, head) == (expected if base_exists else head)
    assert (base, head) == before


@pytest.mark.parametrize('schema', [
    {'properties': {'': {'mergeStrategy': 'append', 'type': 'array'}}},
    {'definitions': {'': {'mergeStrategy': 'append', 'type': 'array'}}, 'properties': {'': {'$ref': '#/definitions/'}}},
])
def test_schema_with_empty_property_or_reference(schema):
    merger = Merger(schema)
    assert merger.merge({'': [1]}, {'': [2]}) == {'': [1, 2]}
    result_schema = merger.get_schema()
    assert 'mergeStrategy' not in repr(result_schema)


def test_cached_schema_with_empty_key_reference():
    merger = Merger({'$ref': 'http://example.test/schema#/definitions/'})
    merger.cache_schema({'id': 'http://example.test/schema', 'definitions': {'': {'mergeStrategy': 'append'}}})
    assert merger.merge([1], [2]) == [1, 2]


@pytest.mark.parametrize('fragment, expected', [
    ('', {'': {'': 'nested', 'a/b': [10, 20]}, 'plain': 30}),
    ('/', {'': 'nested', 'a/b': [10, 20]}),
    ('//', 'nested'),
    ('//a~1b/1', 20),
    ('/plain', 30),
])
def test_resolver_preserves_empty_pointer_tokens(fragment, expected):
    document = {'': {'': 'nested', 'a/b': [10, 20]}, 'plain': 30}
    resolver = LocalRefResolver('', document)
    with resolver.resolving('#' + fragment) as resolved:
        assert resolved == expected


def test_missing_empty_key_raises_resolution_error():
    with pytest.raises(RefResolutionError):
        LocalRefResolver('', {'key': 1}).resolve('#/')


def test_fragment_escaping_and_percent_encoding():
    document = {'': {'a/b': {'m~n': {'space key': {'%2F': 7}}}}}
    resolver = LocalRefResolver('', document)
    with resolver.resolving('#//a~1b/m~0n/space%20key/%252F') as resolved:
        assert resolved == 7


@pytest.mark.parametrize('fragment, expected', [
    ('#/a~1b', 'slash-key'),
    ('#/a%2Fb', 'nested'),
    ('#%2Fa%2Fb', 'nested'),
    ('#/~01', 'tilde-one'),
    ('#/%2F', 'empty-pair'),
    ('#/array/0/', 'array-empty'),
])
def test_pointer_decoding_order_and_array_indices(fragment, expected):
    document = {'a/b': 'slash-key', 'a': {'b': 'nested'}, '~1': 'tilde-one',
                '': {'': 'empty-pair'}, 'array': [{'': 'array-empty'}]}
    with LocalRefResolver('', document).resolving(fragment) as resolved:
        assert resolved == expected


@pytest.mark.parametrize('fragment', ['#/array/2', '#/array/missing', '#/array/0/missing'])
def test_missing_array_or_object_entries_keep_resolution_error(fragment):
    with pytest.raises(RefResolutionError):
        LocalRefResolver('', {'array': [{}]}).resolve(fragment)


def test_legacy_root_array_options_still_work():
    assert Merger({'mergeStrategy': 'arrayMergeById', 'mergeOptions': {'idRef': '/'}}).merge([1, 2], [2, 3]) == [1, 2, 3]
    assert Merger({'mergeStrategy': 'append', 'mergeOptions': {'sortByRef': '/'}}).merge([3], [1, 2]) == [1, 2, 3]


def test_legacy_non_pointer_id_reference_still_works():
    schema = {'mergeStrategy': 'arrayMergeById', 'mergeOptions': {'idRef': 'id'}}
    assert Merger(schema).merge([{'id': 1, 'a': 2}], [{'id': 1, 'b': 3}]) == [{'id': 1, 'a': 2, 'b': 3}]


@pytest.mark.parametrize('keyword, anchor', [('id', '#item'), ('$anchor', 'item'), ('$dynamicAnchor', 'item')])
def test_anchor_resolution_matches_upstream_support(keyword, anchor):
    document = {'definitions': {'value': {keyword: anchor, 'type': 'string'}}}
    resolver = LocalRefResolver('', document)
    try:
        _, expected = RefResolver('', document).resolve('#item')
    except RefResolutionError:
        # Older jsonschema releases do not support named anchors.
        with pytest.raises(RefResolutionError):
            resolver.resolve('#item')
    else:
        with resolver.resolving('#item') as resolved:
            assert resolved is expected


@pytest.mark.skipif(not hasattr(RefResolver, '_find_in_subschemas'), reason='Upstream resolver does not search embedded resources')
def test_embedded_resource_keeps_empty_pointer_token():
    document = {'definitions': {'nested': {'$id': 'http://example.test/inner', '': 42}}}
    resolver = LocalRefResolver('http://example.test/root', document)
    with resolver.resolving('http://example.test/inner#/') as resolved:
        assert resolved == 42
