# vim:ts=4 sw=4 expandtab softtabstop=4
from jsonschema.validators import RefResolver, urldefrag, urljoin
from jsonschema.exceptions import RefResolutionError
try:
    from collections.abc import Sequence
except ImportError:  # Python 2
    from collections import Sequence
try:
    from urllib.parse import unquote
except ImportError:  # Python 2
    from urllib import unquote

class LocalRefResolver(RefResolver):
    # We want to have a class that is the same as jsonschema's RefResolver
    # except:
    #
    #  * No caching for resolves. We are changing the schema as we walk through
    #    it, so with caching you can get outdated resolves.
    #
    #  * Provide a _is_remote_ref() method to check if a $ref points to an
    #    external reference.

    def __init__(self, *args, **kwargs):
        kwargs["remote_cache"] = self.resolve_from_url
        super(LocalRefResolver, self).__init__(*args, **kwargs)

    def resolve(self, ref):
        url = urljoin(self.resolution_scope, ref)
        if not urldefrag(url)[1].endswith('/'):
            return super(LocalRefResolver, self).resolve(ref)

        # RefResolver strips trailing slashes from the URL, including empty
        # property names in a JSON pointer. Keep those names intact.
        find = getattr(self, '_find_in_subschemas', None)
        if find is not None:
            match = find(url)
            if match is not None:
                return match
        return url, self.resolve_from_url(url)

    def resolve_fragment(self, document, fragment):
        pointer = unquote(fragment)
        if not pointer.startswith('/'):
            return super(LocalRefResolver, self).resolve_fragment(document, fragment)

        # Remove only the pointer's initial separator, not empty first tokens.
        for part in pointer[1:].split('/'):
            part = part.replace('~1', '/').replace('~0', '~')
            if isinstance(document, Sequence):
                try:
                    part = int(part)
                except ValueError:
                    pass
            try:
                document = document[part]
            except (TypeError, LookupError):
                raise RefResolutionError("Unresolvable JSON pointer: %r" % fragment)
        return document

    def is_remote_ref(self, ref):
        url = urljoin(self.resolution_scope, ref)
        url, fragment = urldefrag(url)
        return url != self.base_uri
