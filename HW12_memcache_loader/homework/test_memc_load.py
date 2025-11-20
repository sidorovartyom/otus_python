#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for concurrent memcache loader
"""
import unittest
import gzip
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import threading

from memc_load_concurrent import (
    parse_appsinstalled,
    insert_appsinstalled,
    MemcacheConnectionPool,
    Statistics,
    AppsInstalled,
    process_line,
    dot_rename
)
import appsinstalled_pb2


class TestParseAppsInstalled(unittest.TestCase):
    """Test parse_appsinstalled function"""

    def test_valid_line(self):
        """Test parsing valid TSV line"""
        line = "idfa\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,43,567,3,7,23"
        result = parse_appsinstalled(line)

        self.assertIsNotNone(result)
        self.assertEqual(result.dev_type, "idfa")
        self.assertEqual(result.dev_id, "1rfw452y52g2gq4g")
        self.assertAlmostEqual(result.lat, 55.55)
        self.assertAlmostEqual(result.lon, 42.42)
        self.assertEqual(result.apps, [1423, 43, 567, 3, 7, 23])

    def test_invalid_line_too_few_fields(self):
        """Test parsing line with too few fields"""
        line = "idfa\t1rfw452y52g2gq4g\t55.55"
        result = parse_appsinstalled(line)
        self.assertIsNone(result)

    def test_invalid_line_empty_device_type(self):
        """Test parsing line with empty device type"""
        line = "\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,43,567"
        result = parse_appsinstalled(line)
        self.assertIsNone(result)

    def test_invalid_geo_coords(self):
        """Test parsing line with invalid coordinates"""
        line = "idfa\t1rfw452y52g2gq4g\tinvalid\t42.42\t1423,43,567"
        result = parse_appsinstalled(line)
        self.assertIsNone(result)

    def test_mixed_valid_invalid_apps(self):
        """Test parsing line with mixed valid/invalid app IDs"""
        line = "idfa\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,abc,567,3"
        result = parse_appsinstalled(line)

        self.assertIsNotNone(result)
        # Should filter out invalid app IDs
        self.assertEqual(result.apps, [1423, 567, 3])


class TestInsertAppsInstalled(unittest.TestCase):
    """Test insert_appsinstalled function"""

    def test_dry_run_mode(self):
        """Test insert in dry run mode"""
        appsinstalled = AppsInstalled("idfa", "test_id", 55.0, 42.0, [1, 2, 3])
        result = insert_appsinstalled(None, appsinstalled, dry_run=True)
        self.assertTrue(result)

    def test_insert_with_mock_memcache(self):
        """Test actual insert with mocked memcache"""
        appsinstalled = AppsInstalled("idfa", "test_id", 55.0, 42.0, [1, 2, 3])
        mock_memc = Mock()
        mock_memc.set = Mock(return_value=True)

        result = insert_appsinstalled(mock_memc, appsinstalled, dry_run=False)

        self.assertTrue(result)
        mock_memc.set.assert_called_once()

        # Verify protobuf serialization
        call_args = mock_memc.set.call_args
        key, packed = call_args[0]

        self.assertEqual(key, "idfa:test_id")

        # Deserialize and verify
        ua = appsinstalled_pb2.UserApps()
        ua.ParseFromString(packed)
        self.assertAlmostEqual(ua.lat, 55.0)
        self.assertAlmostEqual(ua.lon, 42.0)
        self.assertEqual(list(ua.apps), [1, 2, 3])

    def test_insert_exception_handling(self):
        """Test exception handling during insert"""
        appsinstalled = AppsInstalled("idfa", "test_id", 55.0, 42.0, [1, 2, 3])
        mock_memc = Mock()
        mock_memc.set = Mock(side_effect=Exception("Connection error"))

        result = insert_appsinstalled(mock_memc, appsinstalled, dry_run=False)
        self.assertFalse(result)


class TestMemcacheConnectionPool(unittest.TestCase):
    """Test MemcacheConnectionPool class"""

    def test_get_connection_creates_new(self):
        """Test that get_connection creates new connection"""
        device_memc = {"idfa": "127.0.0.1:33013"}

        with patch('memc_load_concurrent.memcache.Client') as mock_client:
            pool = MemcacheConnectionPool(device_memc)
            conn = pool.get_connection("idfa")

            self.assertIsNotNone(conn)
            mock_client.assert_called_once()

    def test_get_connection_reuses_existing(self):
        """Test that get_connection reuses existing connection for same thread"""
        device_memc = {"idfa": "127.0.0.1:33013"}

        with patch('memc_load_concurrent.memcache.Client') as mock_client:
            pool = MemcacheConnectionPool(device_memc)

            conn1 = pool.get_connection("idfa")
            conn2 = pool.get_connection("idfa")

            # Should be called only once (reuse connection)
            self.assertEqual(mock_client.call_count, 1)
            self.assertEqual(conn1, conn2)

    def test_get_connection_unknown_device_type(self):
        """Test get_connection with unknown device type"""
        device_memc = {"idfa": "127.0.0.1:33013"}
        pool = MemcacheConnectionPool(device_memc)

        conn = pool.get_connection("unknown")
        self.assertIsNone(conn)

    def test_close_all_connections(self):
        """Test closing all connections"""
        device_memc = {"idfa": "127.0.0.1:33013"}

        with patch('memc_load_concurrent.memcache.Client') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            pool = MemcacheConnectionPool(device_memc)
            pool.get_connection("idfa")
            pool.close_all()

            # Verify disconnect was called
            mock_instance.disconnect_all.assert_called_once()


class TestStatistics(unittest.TestCase):
    """Test Statistics class"""

    def test_initial_values(self):
        """Test initial statistics values"""
        stats = Statistics()
        processed, errors = stats.get_stats()

        self.assertEqual(processed, 0)
        self.assertEqual(errors, 0)

    def test_increment_processed(self):
        """Test incrementing processed counter"""
        stats = Statistics()
        stats.inc_processed()
        stats.inc_processed()

        processed, errors = stats.get_stats()
        self.assertEqual(processed, 2)
        self.assertEqual(errors, 0)

    def test_increment_errors(self):
        """Test incrementing errors counter"""
        stats = Statistics()
        stats.inc_errors()

        processed, errors = stats.get_stats()
        self.assertEqual(processed, 0)
        self.assertEqual(errors, 1)

    def test_thread_safety(self):
        """Test thread-safe operations"""
        stats = Statistics()
        num_threads = 10
        increments_per_thread = 100

        def worker():
            for _ in range(increments_per_thread):
                stats.inc_processed()
                stats.inc_errors()

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        processed, errors = stats.get_stats()
        expected = num_threads * increments_per_thread

        self.assertEqual(processed, expected)
        self.assertEqual(errors, expected)


class TestDotRename(unittest.TestCase):
    """Test dot_rename function"""

    def test_dot_rename(self):
        """Test file renaming with dot prefix"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = os.path.join(tmpdir, "test.tsv.gz")
            with open(test_file, 'w') as f:
                f.write("test")

            # Rename
            dot_rename(test_file)

            # Check renamed file exists
            renamed_file = os.path.join(tmpdir, ".test.tsv.gz")
            self.assertTrue(os.path.exists(renamed_file))
            self.assertFalse(os.path.exists(test_file))


class TestProcessLine(unittest.TestCase):
    """Test process_line function"""

    def test_process_valid_line(self):
        """Test processing valid line"""
        line = "idfa\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,43,567"
        device_memc = {"idfa": "127.0.0.1:33013"}

        with patch('memc_load_concurrent.memcache.Client'):
            conn_pool = MemcacheConnectionPool(device_memc)
            stats = Statistics()

            process_line(line, conn_pool, stats, dry_run=True)

            processed, errors = stats.get_stats()
            self.assertEqual(processed, 1)
            self.assertEqual(errors, 0)

    def test_process_invalid_line(self):
        """Test processing invalid line"""
        line = "invalid_line"
        device_memc = {"idfa": "127.0.0.1:33013"}

        with patch('memc_load_concurrent.memcache.Client'):
            conn_pool = MemcacheConnectionPool(device_memc)
            stats = Statistics()

            process_line(line, conn_pool, stats, dry_run=True)

            processed, errors = stats.get_stats()
            self.assertEqual(processed, 0)
            self.assertEqual(errors, 1)

    def test_process_empty_line(self):
        """Test processing empty line"""
        line = ""
        device_memc = {"idfa": "127.0.0.1:33013"}

        with patch('memc_load_concurrent.memcache.Client'):
            conn_pool = MemcacheConnectionPool(device_memc)
            stats = Statistics()

            process_line(line, conn_pool, stats, dry_run=True)

            processed, errors = stats.get_stats()
            self.assertEqual(processed, 0)
            self.assertEqual(errors, 0)


if __name__ == '__main__':
    unittest.main()
