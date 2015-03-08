# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import unicode_literals
from math import log10
from pyLibrary import convert
from pyLibrary.aws import s3

from pyLibrary.debugs.logs import Log
from pyLibrary.dot import wrap, Dict, literal_field
from pyLibrary.maths import Math
from pyLibrary.meta import use_settings
from pyLibrary.queries import qb
from pyLibrary.queries.unique_index import UniqueIndex
from pyLibrary.testing import fuzzytestcase
from pyLibrary.times.timer import Timer
from testlog_etl import etl2key, key2etl


class S3Bucket(object):

    @use_settings
    def __init__(
        self,
        bucket,  # NAME OF THE BUCKET
        aws_access_key_id,  # CREDENTIAL
        aws_secret_access_key,  # CREDENTIAL
        region=None,  # NAME OF AWS REGION, REQUIRED FOR SOME BUCKETS
        public=False,
        debug=False,
        settings=None
    ):
        self.bucket = s3.Bucket(settings)
        self.settings = settings

    def __getattr__(self, item):
        return getattr(self.bucket, item)

    def keys(self, prefix):
        metas = self.bucket.metas(prefix=prefix)
        output = []
        for m in metas:
            for line in self.bucket.read_lines(m.key):
                try:
                    id = convert.json2value(line)._id
                    if id == None:
                        continue

                    output.append(id)
                except Exception, _:
                    pass
        return set(output)

    def find_keys(self, start, count, filter=None):
        digits = int(Math.ceiling(log10(count - 1)))
        prefix = unicode(start)[:-digits]

        metas = self.bucket.metas(prefix=prefix)
        return set(metas.key)

    def find_largest_key(self):
        """
        FIND LARGEST VERSION NUMBER (with dots (.) and colons(:)) IN
        THE KEYS OF AN S3 BUCKET.
        """
        with Timer("Full scan for max key"):
            maxi = 0
            for k in self.bucket.bucket.list(delimiter=":"):
                maxi = max(maxi, int(k.name[:-1]))
            return maxi

    def extend(self, documents):
        parts = Dict()
        for d in wrap(documents):
            parent_key = etl2key(key2etl(d.id).source)
            d.value._id = d.id
            parts[literal_field(parent_key)] += [d.value]

        for k, docs in parts.items():
            self._extend(k, docs)

        return parts.keys()


    def _extend(self, key, documents):
        meta = self.bucket.get_meta(key)
        if meta is not None:
            documents = UniqueIndex(keys="etl.id", data=documents)
            old_docs = UniqueIndex(keys="etl.id", data=map(convert.json2value, self.bucket.read_lines(key)))
            residual = old_docs - documents
            # IS IT CHEAPER TO SEE IF THERE IS A DIFF, RATHER THAN WRITE NEW DATA TO S3?
            if residual:
                documents = documents | residual
            else:
                try:
                    fuzzytestcase.assertAlmostEqual(old_docs._data, documents._data)
                    return
                except Exception, _:
                    pass

        self.bucket.write_lines(key, map(convert.value2json, documents))

    def add(self, dco):
        Log.error("Not supported")


def key_prefix(key):
    return key.split(":")[0].split(".")[0]
