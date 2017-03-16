# vim:ts=4 sw=4 expandtab softtabstop=4

class JSONValue(object):
    def __init__(self, val=None, ref='#', undef=False):
        assert not isinstance(val, JSONValue)
        self.val = val
        self.ref = ref
        self.undef = undef

    def is_undef(self):
        return self.undef

    def _ref_escape(self, key):
        return key.replace('~', '~0').replace('/', '~1')

    def _subval(self, key, **kwargs):
        return JSONValue(ref=self.ref+'/'+self._ref_escape(str(key)), **kwargs)

    def __getitem__(self, key):
        return self._subval(key, val=self.val[key])

    def get(self, key, *args):
        r = self.val.get(key, *args)
        if r is None:
            return self._subval(key, undef=True)
        else:
            return self._subval(key, val=r)

    def __repr__(self):
        if self.is_undef():
            return 'JSONValue(undef=True)'
        else:
            return 'JSONValue(%r,%r)' % (self.val, self.ref)

    def items(self):
        for k, v in self.val.items():
            yield (k, self._subval(k, val=v))

    def __iter__(self):
        assert isinstance(self.val, list)

        for i, v in enumerate(self.val):
            yield self._subval(i, val=v)

    def __eq__(self, other):
        return self.val == other.val and self.ref == other.ref

    def __ne__(self, other):
        return self.val != other.val or self.ref != other.ref
