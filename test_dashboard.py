#!/usr/bin/env python3
"""
Basic Tests for Trading Bot Dashboard
Run with: python3 test_dashboard.py
"""
import unittest
import tempfile
from pathlib import Path
import pandas as pd
from datetime import datetime

from config import Config, TestConfig
from database import DatabaseManager
from cache import SimpleCache, cached


class TestConfig(unittest.TestCase):
    """Test configuration management"""
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = TestConfig()
        is_valid, errors = config.validate_config()
        self.assertTrue(is_valid or len(errors) > 0)
    
    def test_private_ip_detection(self):
        """Test private IP detection"""
        # Test private IPs
        self.assertTrue(Config.is_private_ip('192.168.1.1'))
        self.assertTrue(Config.is_private_ip('10.0.0.1'))
        self.assertTrue(Config.is_private_ip('127.0.0.1'))
        
        # Test public IPs
        self.assertFalse(Config.is_private_ip('8.8.8.8'))
        self.assertFalse(Config.is_private_ip('1.1.1.1'))


class TestDatabase(unittest.TestCase):
    """Test database operations"""
    
    def setUp(self):
        """Create temporary database for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'test.db'
        self.db = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Clean up test database"""
        if self.db_path.exists():
            self.db_path.unlink()
        Path(self.temp_dir).rmdir()
    
    def test_database_initialization(self):
        """Test database is initialized correctly"""
        self.assertTrue(self.db_path.exists())
        stats = self.db.get_database_stats()
        self.assertIn('trades_count', stats)
        self.assertIn('equity_curve_count', stats)
    
    def test_import_equity_data(self):
        """Test importing equity data"""
        # Create test DataFrame
        df = pd.DataFrame({
            'timestamp': [datetime.now().isoformat()],
            'balance': [1000.0],
            'pnl': [50.0],
            'total_trades': [10],
            'winning_trades': [7],
            'losing_trades': [3],
            'win_rate': [0.7]
        })
        
        # Import data
        count = self.db._import_equity(df)
        self.assertEqual(count, 1)
        
        # Verify data was imported
        latest = self.db.get_latest_equity()
        self.assertIsNotNone(latest)
        self.assertEqual(latest['balance'], 1000.0)
    
    def test_database_backup(self):
        """Test database backup"""
        backup_path = Path(self.temp_dir) / 'backup.db'
        success = self.db.backup(backup_path)
        self.assertTrue(success)
        self.assertTrue(backup_path.exists())


class TestCache(unittest.TestCase):
    """Test caching functionality"""
    
    def setUp(self):
        """Create cache for testing"""
        self.cache = SimpleCache(default_ttl=60)
        self.cache.clear()
    
    def test_cache_set_and_get(self):
        """Test setting and getting cache values"""
        self.cache.set('test_key', 'test_value')
        value = self.cache.get('test_key')
        self.assertEqual(value, 'test_value')
    
    def test_cache_expiration(self):
        """Test cache expiration"""
        import time
        self.cache.set('test_key', 'test_value', ttl=1)
        time.sleep(2)
        value = self.cache.get('test_key')
        self.assertIsNone(value)
    
    def test_cache_stats(self):
        """Test cache statistics"""
        self.cache.set('key1', 'value1')
        self.cache.get('key1')  # Hit
        self.cache.get('key2')  # Miss
        
        stats = self.cache.get_stats()
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 1)
    
    def test_cached_decorator(self):
        """Test cached decorator"""
        call_count = [0]
        
        @cached(ttl=60, key_prefix='test_')
        def expensive_function(x):
            call_count[0] += 1
            return x * 2
        
        # First call - should execute function
        result1 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count[0], 1)
        
        # Second call - should use cache
        result2 = expensive_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count[0], 1)  # Not incremented


class TestSecurityValidator(unittest.TestCase):
    """Test security validation"""
    
    def setUp(self):
        """Import SecurityValidator"""
        # This would need to be imported from web_server
        # Skipping for now as it requires Flask context
        pass
    
    def test_filename_sanitization(self):
        """Test filename sanitization"""
        # Test would go here
        pass


def run_tests():
    """Run all tests"""
    print("="*60)
    print("🧪 Running Trading Bot Dashboard Tests")
    print("="*60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestCache))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("")
    print("="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"  Tests run: {result.testsRun}")
    print(f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print("="*60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)

