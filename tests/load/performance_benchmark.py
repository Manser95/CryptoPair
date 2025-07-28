#!/usr/bin/env python3
"""
Performance benchmarking script for Crypto Pairs API
Runs multiple load testing tools and compares results
"""

import asyncio
import aiohttp
import time
import statistics
import json
import argparse
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor


class PerformanceBenchmark:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
    
    async def single_request(self, session: aiohttp.ClientSession, endpoint: str) -> Dict[str, Any]:
        """Make a single HTTP request and measure response time"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                response_time = time.time() - start_time
                body = await response.text()
                return {
                    'status': response.status,
                    'response_time': response_time * 1000,  # Convert to ms
                    'success': response.status == 200,
                    'size': len(body)
                }
        except Exception as e:
            return {
                'status': 0,
                'response_time': (time.time() - start_time) * 1000,
                'success': False,
                'error': str(e),
                'size': 0
            }
    
    async def concurrent_requests(self, concurrent_users: int, duration: int, endpoint: str = "/api/v1/prices/eth-usdt") -> Dict[str, Any]:
        """Run concurrent requests for specified duration"""
        print(f"Running {concurrent_users} concurrent users for {duration}s on {endpoint}")
        
        results = []
        start_time = time.time()
        
        connector = aiohttp.TCPConnector(limit=concurrent_users * 2)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            
            while time.time() - start_time < duration:
                # Create batch of concurrent requests
                batch_tasks = [
                    self.single_request(session, endpoint) 
                    for _ in range(concurrent_users)
                ]
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, dict):
                        results.append(result)
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
        
        return self.analyze_results(results, duration)
    
    def analyze_results(self, results: List[Dict[str, Any]], duration: int) -> Dict[str, Any]:
        """Analyze performance test results"""
        if not results:
            return {'error': 'No results to analyze'}
        
        response_times = [r['response_time'] for r in results if 'response_time' in r]
        successful_requests = [r for r in results if r.get('success', False)]
        
        total_requests = len(results)
        successful_count = len(successful_requests)
        error_count = total_requests - successful_count
        
        analysis = {
            'duration': duration,
            'total_requests': total_requests,
            'successful_requests': successful_count,
            'failed_requests': error_count,
            'success_rate': (successful_count / total_requests * 100) if total_requests > 0 else 0,
            'requests_per_second': total_requests / duration,
            'successful_rps': successful_count / duration,
        }
        
        if response_times:
            analysis.update({
                'response_time_min': min(response_times),
                'response_time_max': max(response_times),
                'response_time_avg': statistics.mean(response_times),
                'response_time_median': statistics.median(response_times),
                'response_time_p95': self.percentile(response_times, 95),
                'response_time_p99': self.percentile(response_times, 99)
            })
        
        return analysis
    
    def percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def run_benchmark_suite(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        print("🚀 Starting Performance Benchmark Suite")
        print("=" * 50)
        
        test_scenarios = [
            {'name': 'Light Load', 'users': 10, 'duration': 30},
            {'name': 'Moderate Load', 'users': 50, 'duration': 60},
            {'name': 'Heavy Load', 'users': 100, 'duration': 60},
            {'name': 'Stress Test', 'users': 300, 'duration': 30},
        ]
        
        endpoints_to_test = [
            '/api/v1/prices/eth-usdt',
            '/api/v1/prices/btc-usdt',
            '/health/liveness'
        ]
        
        benchmark_results = {}
        
        for scenario in test_scenarios:
            print(f"\n📊 Running {scenario['name']}...")
            scenario_results = {}
            
            for endpoint in endpoints_to_test:
                print(f"  Testing {endpoint}...")
                result = await self.concurrent_requests(
                    scenario['users'], 
                    scenario['duration'], 
                    endpoint
                )
                scenario_results[endpoint] = result
            
            benchmark_results[scenario['name']] = scenario_results
            
            # Print summary for this scenario
            self.print_scenario_summary(scenario['name'], scenario_results)
        
        return benchmark_results
    
    def print_scenario_summary(self, scenario_name: str, results: Dict[str, Any]):
        """Print summary for a test scenario"""
        print(f"\n  📈 {scenario_name} Results:")
        
        for endpoint, data in results.items():
            if 'error' in data:
                print(f"    {endpoint}: ERROR - {data['error']}")
                continue
                
            print(f"    {endpoint}:")
            print(f"      RPS: {data['successful_rps']:.1f}")
            print(f"      Success Rate: {data['success_rate']:.1f}%")
            print(f"      Avg Response: {data.get('response_time_avg', 0):.1f}ms")
            print(f"      P95 Response: {data.get('response_time_p95', 0):.1f}ms")
    
    def generate_report(self, results: Dict[str, Any], output_file: str = None):
        """Generate detailed performance report"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'base_url': self.base_url,
            'results': results,
            'summary': self.generate_summary(results)
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Full report saved to: {output_file}")
        
        return report
    
    def generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall performance summary"""
        all_rps = []
        all_success_rates = []
        all_avg_response_times = []
        
        for scenario_name, scenario_data in results.items():
            for endpoint, data in scenario_data.items():
                if 'error' not in data:
                    all_rps.append(data['successful_rps'])
                    all_success_rates.append(data['success_rate'])
                    if 'response_time_avg' in data:
                        all_avg_response_times.append(data['response_time_avg'])
        
        summary = {}
        if all_rps:
            summary['max_rps'] = max(all_rps)
            summary['avg_rps'] = statistics.mean(all_rps)
        
        if all_success_rates:
            summary['avg_success_rate'] = statistics.mean(all_success_rates)
            summary['min_success_rate'] = min(all_success_rates)
        
        if all_avg_response_times:
            summary['avg_response_time'] = statistics.mean(all_avg_response_times)
            summary['max_response_time'] = max(all_avg_response_times)
        
        return summary


async def main():
    parser = argparse.ArgumentParser(description='Performance benchmark for Crypto Pairs API')
    parser.add_argument('--url', default='http://localhost:8000', help='Base URL for the API')
    parser.add_argument('--output', help='Output file for detailed results (JSON)')
    parser.add_argument('--quick', action='store_true', help='Run quick benchmark (shorter duration)')
    
    args = parser.parse_args()
    
    benchmark = PerformanceBenchmark(args.url)
    
    if args.quick:
        print("🏃 Running quick benchmark...")
        result = await benchmark.concurrent_requests(50, 30)
        print("\n📊 Quick Benchmark Results:")
        print(f"  Successful RPS: {result['successful_rps']:.1f}")
        print(f"  Success Rate: {result['success_rate']:.1f}%")
        print(f"  Avg Response Time: {result.get('response_time_avg', 0):.1f}ms")
        print(f"  P95 Response Time: {result.get('response_time_p95', 0):.1f}ms")
    else:
        results = await benchmark.run_benchmark_suite()
        report = benchmark.generate_report(results, args.output)
        
        print("\n🎯 Overall Performance Summary:")
        summary = report['summary']
        print(f"  Max RPS Achieved: {summary.get('max_rps', 0):.1f}")
        print(f"  Average Success Rate: {summary.get('avg_success_rate', 0):.1f}%")
        print(f"  Average Response Time: {summary.get('avg_response_time', 0):.1f}ms")


if __name__ == "__main__":
    asyncio.run(main())