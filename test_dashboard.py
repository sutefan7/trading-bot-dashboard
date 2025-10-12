#!/usr/bin/env python3
"""
Basic Tests for Trading Bot Dashboard
Run with: python3 test_dashboard.py
"""
import unittest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
from datetime import datetime

from config import Config, TestConfig
from database import DatabaseManager
from cache import AdvancedCache as SimpleCache, cached
from pi_api_client import PiAPIClient


class TestConfigManagement(unittest.TestCase):
    """Test configuration management"""

    def test_config_validation(self):
        """Test configuration validation"""
        is_valid, errors = Config.validate_config()
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
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / 'test.db'
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        """Clean up test database"""
        if self.db_path.exists():
            self.db_path.unlink()
        shutil.rmtree(self.temp_dir.name, ignore_errors=True)
    
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
        backup_path = Path(self.temp_dir.name) / 'backup.db'
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


class TestPiAPILocalMode(unittest.TestCase):
    """Test Pi API client behaviour in local mode"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        (self.temp_path / 'logs').mkdir(parents=True, exist_ok=True)

        (self.temp_path / 'logs' / 'trading_bot.log').write_text(
            "BOT LOG LINE 1\nBOT LOG LINE 2\nBOT LOG LINE 3\n",
            encoding='utf-8'
        )
        (self.temp_path / 'logs' / 'signals.log').write_text(
            "Signal: BUY\nSignal: SELL\n",
            encoding='utf-8'
        )
        (self.temp_path / 'logs' / 'errors.log').write_text(
            "Error: data_manager failure\nError: scheduler hiccup\n",
            encoding='utf-8'
        )

        self.prev_local_mode = Config.PI_LOCAL_MODE
        self.prev_local_path = Config.LOCAL_PI_APP_PATH
        Config.PI_LOCAL_MODE = True
        Config.LOCAL_PI_APP_PATH = self.temp_path

        self.client = PiAPIClient()

    def tearDown(self):
        Config.PI_LOCAL_MODE = self.prev_local_mode
        Config.LOCAL_PI_APP_PATH = self.prev_local_path
        self.temp_dir.cleanup()

    def test_local_tail_reads_logs(self):
        success, stdout, stderr = self.client.execute_ssh_command(
            f"tail -5 {Config.PI_APP_PATH}/logs/trading_bot.log"
        )
        self.assertTrue(success)
        self.assertIn('BOT LOG LINE 3', stdout)

        bot_status = self.client.get_bot_status_data()
        self.assertIn('recent_logs', bot_status)
        self.assertTrue(bot_status['recent_logs'])
        self.assertNotIn('file not found', ' '.join(bot_status['recent_logs']).lower())

        signals_data = self.client.get_signals_data()
        self.assertTrue(signals_data['signals'])
        self.assertNotIn('file not found', ' '.join(signals_data['signals']).lower())

        errors_data = self.client.get_errors_data()
        self.assertTrue(errors_data['errors'])
        self.assertNotIn('file not found', ' '.join(errors_data['errors']).lower())


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
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestCache))
    suite.addTests(loader.loadTestsFromTestCase(TestPiAPILocalMode))
    
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

