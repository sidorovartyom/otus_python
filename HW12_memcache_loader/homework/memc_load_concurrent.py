#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Concurrent memcache loader using threading for improved performance.
Loads mobile app tracker logs into memcache cluster.
"""
import os
import gzip
import sys
import glob
import logging
import collections
from optparse import OptionParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading

# brew install protobuf
# protoc  --python_out=. ./appsinstalled.proto
# pip install protobuf
import appsinstalled_pb2
# pip install python-memcached
import memcache

NORMAL_ERR_RATE = 0.01
AppsInstalled = collections.namedtuple("AppsInstalled", ["dev_type", "dev_id", "lat", "lon", "apps"])


class MemcacheConnectionPool:
    """Thread-safe memcache connection pool"""

    def __init__(self, device_memc):
        """
        Args:
            device_memc: dict mapping device types to memcache addresses
        """
        self.device_memc = device_memc
        self._connections = {}
        self._lock = threading.Lock()

    def get_connection(self, dev_type):
        """Get or create memcache connection for device type"""
        thread_id = threading.get_ident()
        key = (dev_type, thread_id)

        with self._lock:
            if key not in self._connections:
                memc_addr = self.device_memc.get(dev_type)
                if memc_addr:
                    self._connections[key] = memcache.Client([memc_addr], socket_timeout=3)

        return self._connections.get(key)

    def close_all(self):
        """Close all connections"""
        with self._lock:
            for conn in self._connections.values():
                try:
                    conn.disconnect_all()
                except:
                    pass
            self._connections.clear()


class Statistics:
    """Thread-safe statistics counter"""

    def __init__(self):
        self.processed = 0
        self.errors = 0
        self._lock = threading.Lock()

    def inc_processed(self):
        with self._lock:
            self.processed += 1

    def inc_errors(self):
        with self._lock:
            self.errors += 1

    def get_stats(self):
        with self._lock:
            return self.processed, self.errors


def dot_rename(path):
    """Rename file by prefixing with dot"""
    head, fn = os.path.split(path)
    # atomic in most cases
    os.rename(path, os.path.join(head, "." + fn))


def insert_appsinstalled(memc_conn, appsinstalled, dry_run=False):
    """
    Insert app installation data into memcache

    Args:
        memc_conn: memcache connection
        appsinstalled: AppsInstalled namedtuple
        dry_run: if True, only log without actual insertion

    Returns:
        bool: True if successful, False otherwise
    """
    ua = appsinstalled_pb2.UserApps()
    ua.lat = appsinstalled.lat
    ua.lon = appsinstalled.lon
    key = "%s:%s" % (appsinstalled.dev_type, appsinstalled.dev_id)
    ua.apps.extend(appsinstalled.apps)
    packed = ua.SerializeToString()

    try:
        if dry_run:
            logging.debug("%s -> %s" % (key, str(ua).replace("\n", " ")))
            return True
        else:
            if memc_conn is None:
                return False
            memc_conn.set(key, packed)
            return True
    except Exception as e:
        logging.exception("Cannot write to memc: %s" % e)
        return False


def parse_appsinstalled(line):
    """
    Parse line from TSV file

    Args:
        line: TSV line string

    Returns:
        AppsInstalled namedtuple or None if parsing failed
    """
    line_parts = line.strip().split("\t")
    if len(line_parts) < 5:
        return None

    dev_type, dev_id, lat, lon, raw_apps = line_parts
    if not dev_type or not dev_id:
        return None

    try:
        apps = [int(a.strip()) for a in raw_apps.split(",") if a.strip()]
    except ValueError:
        apps = [int(a.strip()) for a in raw_apps.split(",") if a.strip().isdigit()]
        logging.info("Not all user apps are digits: `%s`" % line)

    try:
        lat, lon = float(lat), float(lon)
    except ValueError:
        logging.info("Invalid geo coords: `%s`" % line)
        return None

    return AppsInstalled(dev_type, dev_id, lat, lon, apps)


def process_line(line, conn_pool, stats, dry_run):
    """
    Process single line: parse and insert into memcache

    Args:
        line: TSV line
        conn_pool: MemcacheConnectionPool instance
        stats: Statistics instance
        dry_run: dry run mode flag
    """
    line = line.strip()
    if not line:
        return

    appsinstalled = parse_appsinstalled(line)
    if not appsinstalled:
        stats.inc_errors()
        return

    memc_conn = conn_pool.get_connection(appsinstalled.dev_type)
    if not memc_conn:
        stats.inc_errors()
        logging.error("Unknown device type: %s" % appsinstalled.dev_type)
        return

    ok = insert_appsinstalled(memc_conn, appsinstalled, dry_run)
    if ok:
        stats.inc_processed()
    else:
        stats.inc_errors()


def process_file_concurrent(fn, conn_pool, dry_run, workers=4):
    """
    Process single file with concurrent workers

    Args:
        fn: filename path
        conn_pool: MemcacheConnectionPool instance
        dry_run: dry run mode
        workers: number of worker threads

    Returns:
        tuple: (processed_count, errors_count)
    """
    stats = Statistics()
    logging.info('Processing %s' % fn)

    with gzip.open(fn, 'rt') as fd:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all lines to thread pool
            futures = []
            for line in fd:
                future = executor.submit(process_line, line, conn_pool, stats, dry_run)
                futures.append(future)

            # Wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.exception("Error processing line: %s" % e)
                    stats.inc_errors()

    return stats.get_stats()


def main(options):
    """Main processing function"""
    device_memc = {
        "idfa": options.idfa,
        "gaid": options.gaid,
        "adid": options.adid,
        "dvid": options.dvid,
    }

    # Create connection pool
    conn_pool = MemcacheConnectionPool(device_memc)

    try:
        # Process files in chronological order
        files = sorted(glob.glob(options.pattern))
        logging.info("Found %d files to process" % len(files))

        for fn in files:
            processed, errors = process_file_concurrent(
                fn,
                conn_pool,
                options.dry,
                workers=options.workers
            )

            if not processed:
                logging.info("Empty file: %s" % fn)
                dot_rename(fn)
                continue

            err_rate = float(errors) / processed if processed else 0
            if err_rate < NORMAL_ERR_RATE:
                logging.info("Acceptable error rate (%.2f%%). Successful load" % (err_rate * 100))
            else:
                logging.error("High error rate (%.2f%% > %.2f%%). Failed load" %
                            (err_rate * 100, NORMAL_ERR_RATE * 100))

            # Rename processed file
            dot_rename(fn)
            logging.info("File %s processed: %d records, %d errors" % (fn, processed, errors))

    finally:
        # Cleanup connections
        conn_pool.close_all()


def prototest():
    """Test protobuf serialization"""
    sample = "idfa\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,43,567,3,7,23\ngaid\t7rfw452y52g2gq4g\t55.55\t42.42\t7423,424"
    for line in sample.splitlines():
        dev_type, dev_id, lat, lon, raw_apps = line.strip().split("\t")
        apps = [int(a) for a in raw_apps.split(",") if a.isdigit()]
        lat, lon = float(lat), float(lon)
        ua = appsinstalled_pb2.UserApps()
        ua.lat = lat
        ua.lon = lon
        ua.apps.extend(apps)
        packed = ua.SerializeToString()
        unpacked = appsinstalled_pb2.UserApps()
        unpacked.ParseFromString(packed)
        assert ua == unpacked


if __name__ == '__main__':
    op = OptionParser()
    op.add_option("-t", "--test", action="store_true", default=False)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("--dry", action="store_true", default=False)
    op.add_option("--pattern", action="store", default="/data/appsinstalled/*.tsv.gz")
    op.add_option("--idfa", action="store", default="127.0.0.1:33013")
    op.add_option("--gaid", action="store", default="127.0.0.1:33014")
    op.add_option("--adid", action="store", default="127.0.0.1:33015")
    op.add_option("--dvid", action="store", default="127.0.0.1:33016")
    op.add_option("-w", "--workers", action="store", type="int", default=4,
                  help="Number of worker threads (default: 4)")
    (opts, args) = op.parse_args()

    logging.basicConfig(
        filename=opts.log,
        level=logging.INFO if not opts.dry else logging.DEBUG,
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S'
    )

    if opts.test:
        prototest()
        logging.info("Prototest passed!")
        sys.exit(0)

    logging.info("Memc loader started with options: %s" % opts)
    try:
        main(opts)
    except Exception as e:
        logging.exception("Unexpected error: %s" % e)
        sys.exit(1)
