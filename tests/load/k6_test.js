import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  scenarios: {
    // Scenario 1: Constant load test (300 users)
    constant_load: {
      executor: 'constant-vus',
      vus: 300,
      duration: '5m',
      tags: { scenario: 'constant' },
    },
    
    // Scenario 2: Ramping load test
    ramping_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 100 },  // Ramp up to 100 users
        { duration: '3m', target: 300 },  // Ramp up to 300 users
        { duration: '2m', target: 300 },  // Stay at 300 users
        { duration: '1m', target: 0 },    // Ramp down to 0
      ],
      tags: { scenario: 'ramping' },
      startTime: '5m',  // Start after constant load test
    },
    
    // Scenario 3: Spike test
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 50,
      stages: [
        { duration: '30s', target: 50 },   // Warm up
        { duration: '10s', target: 500 },  // Spike to 500 users
        { duration: '1m', target: 500 },   // Stay at 500
        { duration: '10s', target: 50 },   // Back to normal
      ],
      tags: { scenario: 'spike' },
      startTime: '12m',  // Start after ramping test
    },
  },
  
  thresholds: {
    http_req_duration: ['p(95)<1000'],  // 95% of requests must complete below 1s
    http_req_failed: ['rate<0.05'],     // Error rate must be below 5%
    errors: ['rate<0.05'],              // Custom error rate below 5%
  },
};

const BASE_URL = 'http://localhost:8000';

// Main test function
export default function() {
  const scenario = __ENV.SCENARIO || 'mixed';
  
  if (scenario === 'simple') {
    simpleTest();
  } else {
    mixedTest();
  }
}

function simpleTest() {
  // Simple ETH/USDT price check
  const response = http.get(`${BASE_URL}/api/v1/prices/eth-usdt`);
  
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response has price': (r) => {
      const body = JSON.parse(r.body);
      return body.price > 0;
    },
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  errorRate.add(!success);
  sleep(1);
}

function mixedTest() {
  // 80% ETH/USDT requests
  if (Math.random() < 0.8) {
    const response = http.get(`${BASE_URL}/api/v1/prices/eth-usdt`);
    
    check(response, {
      'ETH/USDT status is 200': (r) => r.status === 200,
      'ETH/USDT has valid price': (r) => {
        const body = JSON.parse(r.body);
        return body.price > 0 && body.symbol === 'eth';
      },
    });
  } 
  // 15% other trading pairs
  else if (Math.random() < 0.95) {
    const pairs = ['btc-usdt', 'bnb-usdt', 'sol-usdt', 'ada-usdt'];
    const pair = pairs[Math.floor(Math.random() * pairs.length)];
    
    const response = http.get(`${BASE_URL}/api/v1/prices/${pair}`);
    
    check(response, {
      'Other pair status is 200': (r) => r.status === 200,
    });
  }
  // 5% health checks
  else {
    const response = http.get(`${BASE_URL}/health/liveness`);
    
    check(response, {
      'Health check is 200': (r) => r.status === 200,
    });
  }
  
  // Variable sleep between requests
  sleep(Math.random() * 2 + 0.5);
}

// Setup function (run once per VU)
export function setup() {
  // Warm up the cache
  const response = http.get(`${BASE_URL}/api/v1/prices/eth-usdt`);
  check(response, {
    'Setup successful': (r) => r.status === 200,
  });
  
  return { startTime: new Date().toISOString() };
}

// Teardown function (run once at the end)
export function teardown(data) {
  console.log(`Test completed. Started at: ${data.startTime}`);
}

// Run with:
// k6 run tests/load/k6_test.js
// k6 run --vus 300 --duration 5m tests/load/k6_test.js
// k6 run --env SCENARIO=simple --vus 300 --duration 5m tests/load/k6_test.js
//
// Performance test with metrics output:
// k6 run --out json=results.json tests/load/k6_test.js
//
// Run specific scenario only:
// k6 run --scenario constant_load tests/load/k6_test.js
// k6 run --scenario spike_test tests/load/k6_test.js