# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import division
from __future__ import unicode_literals

from pyLibrary.aws import s3
from pyLibrary.debugs.logs import Log
from pyLibrary.dot import Null, listwrap
from pyLibrary.jsons import ref
from pyLibrary.maths.randoms import Random
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase
from activedata_etl.sinks.s3_bucket import S3Bucket
from activedata_etl.transforms import pulse_block_to_perfherder_logs, perfherder_logs_to_perf_logs
from activedata_etl.transforms.perfherder_logs_to_perf_logs import stats

false = False
true = True

class TestUnittestLogsToSink(FuzzyTestCase):

    def test_specif_url(self):
        url = "http://queue.taskcluster.net/v1/task/Izw-lZINTFqQsnnrv5N1UQ/artifacts/public/test_info//mochitest-devtools-chrome-chunked_raw.log"