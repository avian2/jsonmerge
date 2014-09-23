# vim:ts=4 sw=4 expandtab softtabstop=4

class JSONValue(object):
    def __init__(self, val, ref='#'):
        assert not isinstance(val, JSONValue)
        self.val = val
        self.ref = ref

    def _subval(self, val, key):
        return JSONValue(val, ref=self.ref+'/'+str(key))

    def __getitem__(self, key):
        return self._subval(self.val[key], key)

    def get(self, key, *args):
        r = self.val.get(key, *args)
        if r is None:
            return None
        else:
            return self._subval(r, key)

    def __repr__(self):
        return 'JSONValue(%r,%r)' % (self.val, self.ref)

    def iteritems(self):
        for k, v in self.val.iteritems():
            yield (k, self._subval(v, k))

    def items(self):
        return list(self.iteritems())

    def __iter__(self):
        for i, v in enumerate(self.val):
            yield self._subval(v, i)
