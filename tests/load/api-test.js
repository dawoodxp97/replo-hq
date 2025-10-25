import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
export const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up to 10 users
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 20 }, // Ramp up to 20 users
    { duration: '5m', target: 20 }, // Stay at 20 users
    { duration: '2m', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.1'],    // Error rate must be below 10%
    errors: ['rate<0.1'],             // Custom error rate must be below 10%
  },
};

// Base URL for the API
const BASE_URL = __ENV.API_URL || 'https://api-staging.yourdomain.com';

// Test data
const testUser = {
  email: `test-${Math.random().toString(36).substring(7)}@example.com`,
  password: 'TestPassword123!',
};

let authToken = '';

export function setup() {
  // Health check
  const healthResponse = http.get(`${BASE_URL}/health`);
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
  });

  // Create test user and get auth token
  const signupResponse = http.post(`${BASE_URL}/api/auth/signup`, JSON.stringify(testUser), {
    headers: { 'Content-Type': 'application/json' },
  });

  if (signupResponse.status === 201) {
    const loginResponse = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify(testUser), {
      headers: { 'Content-Type': 'application/json' },
    });

    if (loginResponse.status === 200) {
      const loginData = JSON.parse(loginResponse.body);
      authToken = loginData.access_token;
    }
  }

  return { authToken };
}

export default function (data) {
  const token = data.authToken || authToken;
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };

  // Test scenarios
  const scenarios = [
    testHealthEndpoint,
    testAuthenticatedEndpoints,
    testProjectOperations,
    testUserOperations,
  ];

  // Randomly select a scenario
  const scenario = scenarios[Math.floor(Math.random() * scenarios.length)];
  scenario(headers);

  sleep(1);
}

function testHealthEndpoint() {
  const response = http.get(`${BASE_URL}/health`);
  
  const success = check(response, {
    'health endpoint status is 200': (r) => r.status === 200,
    'health endpoint response time < 200ms': (r) => r.timings.duration < 200,
  });

  errorRate.add(!success);
}

function testAuthenticatedEndpoints(headers) {
  // Test user profile endpoint
  const profileResponse = http.get(`${BASE_URL}/api/users/me`, { headers });
  
  const success = check(profileResponse, {
    'profile endpoint status is 200': (r) => r.status === 200,
    'profile endpoint response time < 500ms': (r) => r.timings.duration < 500,
    'profile response has user data': (r) => {
      try {
        const data = JSON.parse(r.body);
        return data.email !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  errorRate.add(!success);
}

function testProjectOperations(headers) {
  // Get projects list
  const projectsResponse = http.get(`${BASE_URL}/api/projects`, { headers });
  
  let success = check(projectsResponse, {
    'projects list status is 200': (r) => r.status === 200,
    'projects list response time < 1000ms': (r) => r.timings.duration < 1000,
  });

  errorRate.add(!success);

  // Create a test project
  const newProject = {
    name: `Test Project ${Math.random().toString(36).substring(7)}`,
    description: 'Load test project',
    repository_url: 'https://github.com/test/repo',
  };

  const createResponse = http.post(`${BASE_URL}/api/projects`, JSON.stringify(newProject), { headers });
  
  success = check(createResponse, {
    'project creation status is 201': (r) => r.status === 201,
    'project creation response time < 2000ms': (r) => r.timings.duration < 2000,
  });

  errorRate.add(!success);

  // If project was created successfully, test getting it
  if (createResponse.status === 201) {
    try {
      const projectData = JSON.parse(createResponse.body);
      const projectId = projectData.id;

      const getProjectResponse = http.get(`${BASE_URL}/api/projects/${projectId}`, { headers });
      
      success = check(getProjectResponse, {
        'get project status is 200': (r) => r.status === 200,
        'get project response time < 500ms': (r) => r.timings.duration < 500,
      });

      errorRate.add(!success);

      // Clean up - delete the test project
      const deleteResponse = http.del(`${BASE_URL}/api/projects/${projectId}`, null, { headers });
      
      check(deleteResponse, {
        'project deletion status is 204': (r) => r.status === 204,
      });
    } catch (e) {
      console.error('Error parsing project creation response:', e);
      errorRate.add(true);
    }
  }
}

function testUserOperations(headers) {
  // Update user profile
  const updateData = {
    name: `Test User ${Math.random().toString(36).substring(7)}`,
  };

  const updateResponse = http.put(`${BASE_URL}/api/users/me`, JSON.stringify(updateData), { headers });
  
  const success = check(updateResponse, {
    'user update status is 200': (r) => r.status === 200,
    'user update response time < 1000ms': (r) => r.timings.duration < 1000,
  });

  errorRate.add(!success);

  // Get user settings
  const settingsResponse = http.get(`${BASE_URL}/api/users/me/settings`, { headers });
  
  const settingsSuccess = check(settingsResponse, {
    'user settings status is 200': (r) => r.status === 200,
    'user settings response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!settingsSuccess);
}

export function teardown(data) {
  // Clean up test data if needed
  if (data.authToken) {
    // Could delete test user or clean up test data here
    console.log('Teardown completed');
  }
}

export function handleSummary(data) {
  return {
    'summary.json': JSON.stringify(data, null, 2),
    stdout: `
Load Test Summary:
==================
Total Requests: ${data.metrics.http_reqs.values.count}
Failed Requests: ${data.metrics.http_req_failed.values.rate * 100}%
Average Response Time: ${data.metrics.http_req_duration.values.avg}ms
95th Percentile: ${data.metrics.http_req_duration.values['p(95)']}ms
Max Response Time: ${data.metrics.http_req_duration.values.max}ms

Thresholds:
-----------
${Object.entries(data.thresholds).map(([key, value]) => 
  `${key}: ${value.ok ? '✓ PASS' : '✗ FAIL'}`
).join('\n')}
    `,
  };
}