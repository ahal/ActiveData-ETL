# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import unicode_literals

import requests

from pyLibrary import aws
from pyLibrary import convert
from pyLibrary.debugs import startup
from pyLibrary.debugs.logs import Log
from pyLibrary.structs import wrap, Dict
from pyLibrary.thread.threads import Thread


DEBUG = True
DEBUG_SHOW_NO_LOG = False


next_key = {}  # TRACK THE NEXT KEY FOR EACH SOURCE KEY


def process_pulse_block(source_key, source, dest_bucket):
    """
    SIMPLE CONVERT pulse_block INTO S3 LOGFILES
    PREPEND WITH ETL HEADER AND PULSE ENVELOPE
    """
    output = []

    for i, line in enumerate(source.read().split("\n")):
        envelope = convert.json2value(line)
        if envelope._meta:
            pass
        elif envelope.locale:
            if DEBUG:
                Log.note("Line {{index}}: found pulse message stripped of envelope", {"index": i})
            envelope = Dict(data=envelope)
        elif envelope.source:
            continue
        elif envelope.pulse:
            if DEBUG:
                Log.note("Line {{index}}: found pulse array", {"index": i})
            # FEED THE ARRAY AS A SEQUENCE OF LINES FOR THIS METHOD TO CONTINUE PROCESSING
            def read():
                return convert.unicode2utf8("\n".join(convert.value2json(p) for p in envelope.pulse))

            temp = Dict(read=read)

            return process_pulse_block(source_key, temp, dest_bucket)
        else:
            Log.error("Line {{index}}: Do not know how to handle line\n{{line}}", {"line": line, "index": i})

        file_num = 0
        for name, url in envelope.data.blobber_files.items():
            try:
                if "structured" in name and name.endswith(".log"):
                    if url == None:
                        if DEBUG:
                            Log.note("Line {{index}}: found structured log with null nam", {"index": i})
                        continue

                    log_content = requests.get(url).content
                    if DEBUG:
                        Log.note("Line {{index}}: found structured log {{name}}", {"index": i, "name":name})

                    dest_key, dest_etl = etl_key(envelope, source_key, name)

                    dest_bucket.write(
                        dest_key,
                        convert.unicode2utf8(convert.value2json(dest_etl)) + b"\n" +
                        convert.unicode2utf8(line) + b"\n" +
                        log_content
                    )
                    file_num += 1
                    output.append(dest_key)
            except Exception, e:
                Log.error("Problem processing {{url}}", {"url": url}, e)

        if not file_num and DEBUG_SHOW_NO_LOG:
            Log.note("No structured log {{json}}", {"json": envelope.data})

    return output


def etl_key(envelope, source_key, name):
    num = next_key.get(source_key, 0)
    next_key[source_key] = num + 1
    dest_key = source_key + "." + unicode(num)

    if envelope.data.etl:
        dest_etl = wrap({
            "id": num,
            "name": name,
            "source": envelope.data.etl,
            "type": "join"
        })
    else:
        if source_key.endswith(".json"):
            Log.error("Not expected")

        dest_etl = wrap({
            "id": num,
            "name": name,
            "source": {
                "id": source_key
            },
            "type": "join"
        })
    return dest_key, dest_etl





def loop(work_queue, conn, dest, please_stop):
    while not please_stop:
        todo = work_queue.pop()
        if todo == None:
            return

        with conn.get_bucket(todo.bucket) as source:
            try:
                process_pulse_block(todo.key, source.get_key(todo.key), dest)
                work_queue.commit()
            except Exception, e:
                Log.warning("could not processs {{key}}", {"key": todo.key}, e)


def main():
    try:
        settings = startup.read_settings()
        Log.start(settings.debug)

        with startup.SingleInstance(flavor_id=settings.args.filename):
            with aws.Queue(settings.work_queue) as work_queue:
                with aws.s3.Connection(settings.aws) as conn:
                    with aws.s3.Bucket(settings.destination) as dest:
                        thread = Thread.run("main_loop", loop, work_queue, conn, dest)
                        Thread.wait_for_shutdown_signal(thread.please_stop)
                        thread.stop()
                        thread.join()
    except Exception, e:
        Log.error("Problem with etl", e)
    finally:
        Log.stop()


if __name__ == "__main__":
    main()
