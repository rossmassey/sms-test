"""
Performance and load tests for the SMS Outreach Backend.
Run with: python -m pytest tests/test_performance.py -v
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
VALID_API_KEY = "sms_backend_2025_secure_key_xyz789"

class TestPerformance:
    """Performance tests for the API."""
    
    def test_health_check_response_time(self):
        """Test that health check responds quickly."""
        start_time = time.time()
        response = client.get("/")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 1.0, f"Health check took {response_time:.2f}s, should be under 1s"
    
    def test_concurrent_health_checks(self):
        """Test handling multiple concurrent health check requests."""
        def make_request():
            return client.get("/")
        
        # Run 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
            end_time = time.time()
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Should complete within reasonable time
        total_time = end_time - start_time
        assert total_time < 5.0, f"10 concurrent requests took {total_time:.2f}s"
    
    def test_auth_validation_performance(self):
        """Test that authentication validation is fast."""
        headers = {"X-API-Key": VALID_API_KEY}
        
        start_time = time.time()
        response = client.get("/customers", headers=headers)
        end_time = time.time()
        
        # Should respond quickly even if Firebase fails
        # Note: First request may be slower due to Firebase initialization
        response_time = end_time - start_time
        assert response_time < 10.0, f"Auth validation took {response_time:.2f}s"
    
    def test_invalid_auth_performance(self):
        """Test that invalid auth is rejected quickly."""
        headers = {"X-API-Key": "invalid_key"}
        
        start_time = time.time()
        response = client.get("/customers", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 401
        response_time = end_time - start_time
        assert response_time < 0.5, f"Invalid auth rejection took {response_time:.2f}s"
    
    def test_large_request_handling(self):
        """Test handling of large request payloads."""
        headers = {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
        
        # Create a large customer with many tags
        large_customer = {
            "name": "Test Customer with Very Long Name " * 10,
            "phone": "+1234567890",
            "notes": "Very long notes " * 100,  # ~1600 characters
            "tags": [f"tag_{i}" for i in range(100)]  # 100 tags
        }
        
        start_time = time.time()
        response = client.post("/customers", headers=headers, json=large_customer)
        end_time = time.time()
        
        # Should handle large requests (may fail due to Firebase but shouldn't timeout)
        response_time = end_time - start_time
        assert response_time < 5.0, f"Large request took {response_time:.2f}s"
        assert response.status_code in [200, 422, 500]  # Valid responses

class TestScalability:
    """Test scalability considerations."""
    
    def test_pagination_performance(self):
        """Test that pagination parameters don't slow down requests significantly."""
        headers = {"X-API-Key": VALID_API_KEY}
        
        # Test different pagination parameters
        test_cases = [
            "/customers?limit=10&offset=0",
            "/customers?limit=100&offset=0",
            "/customers?limit=10&offset=100",
            "/messages?limit=50&offset=0",
            "/messages?customer_id=test&limit=20&offset=10"
        ]
        
        for endpoint in test_cases:
            start_time = time.time()
            response = client.get(endpoint, headers=headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response_time < 3.0, f"Paginated request {endpoint} took {response_time:.2f}s"
            assert response.status_code in [200, 500]  # Valid responses
    
    def test_concurrent_different_endpoints(self):
        """Test handling concurrent requests to different endpoints."""
        headers = {"X-API-Key": VALID_API_KEY}
        
        def make_requests():
            endpoints = [
                ("/", "GET", {}),
                ("/customers", "GET", headers),
                ("/messages", "GET", headers),
                ("/customers/search/phone?phone=+1234567890", "GET", headers)
            ]
            
            results = []
            for endpoint, method, req_headers in endpoints:
                if method == "GET":
                    response = client.get(endpoint, headers=req_headers)
                    results.append(response.status_code)
            return results
        
        # Run concurrent requests to different endpoints
        with ThreadPoolExecutor(max_workers=5) as executor:
            start_time = time.time()
            futures = [executor.submit(make_requests) for _ in range(5)]
            all_results = [future.result() for future in futures]
            end_time = time.time()
        
        # Should complete within reasonable time
        total_time = end_time - start_time
        assert total_time < 10.0, f"Concurrent mixed requests took {total_time:.2f}s"
        
        # All requests should get valid responses
        for results in all_results:
            for status_code in results:
                assert status_code in [200, 401, 404, 500]  # Valid status codes

class TestMemoryUsage:
    """Test memory usage patterns."""
    
    def test_request_memory_cleanup(self):
        """Test that requests don't leak memory."""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        headers = {"X-API-Key": VALID_API_KEY}
        
        # Make many requests
        for i in range(50):
            client.get("/", headers={})
            client.get("/customers", headers=headers)
            
            # Force garbage collection periodically
            if i % 10 == 0:
                gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.2f}MB"

class TestErrorHandlingPerformance:
    """Test performance under error conditions."""
    
    def test_404_response_time(self):
        """Test that 404 responses are fast."""
        headers = {"X-API-Key": VALID_API_KEY}
        
        start_time = time.time()
        response = client.get("/nonexistent-endpoint", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 404
        response_time = end_time - start_time
        assert response_time < 0.5, f"404 response took {response_time:.2f}s"
    
    def test_validation_error_performance(self):
        """Test that validation errors are handled quickly."""
        headers = {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
        
        invalid_data = {"invalid": "data"}
        
        start_time = time.time()
        response = client.post("/customers", headers=headers, json=invalid_data)
        end_time = time.time()
        
        assert response.status_code == 422  # Validation error
        response_time = end_time - start_time
        assert response_time < 1.0, f"Validation error response took {response_time:.2f}s"
    
    def test_multiple_auth_failures(self):
        """Test handling multiple authentication failures quickly."""
        invalid_headers = {"X-API-Key": "definitely_invalid_key"}
        
        start_time = time.time()
        for _ in range(20):
            response = client.get("/customers", headers=invalid_headers)
            assert response.status_code == 401
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / 20
        assert avg_time < 0.1, f"Average auth failure response time: {avg_time:.3f}s"

class TestDatabasePerformance:
    """Test database-related performance."""
    
    @pytest.mark.integration
    def test_database_connection_performance(self):
        """Test database connection establishment time."""
        from app.database import get_firestore_client
        
        # Test multiple database client retrievals
        start_time = time.time()
        for _ in range(10):
            try:
                client = get_firestore_client()
            except Exception:
                # Expected if Firebase not configured
                pass
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / 10
        assert avg_time < 0.5, f"Average database client retrieval: {avg_time:.3f}s"

# Performance test configuration
def pytest_configure(config):
    """Configure performance test markers."""
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "memory: mark test as memory intensive")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
