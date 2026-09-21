'use strict';

// Lambda@Edge function for API request processing
exports.handler = (event, context, callback) => {
    const request = event.Records[0].cf.request;
    const response = event.Records[0].cf.response || null;

    // If this is an origin request
    if (!response) {
        handleOriginRequest(event, callback);
    } else {
        // If this is an origin response
        handleOriginResponse(event, callback);
    }
};

function handleOriginRequest(event, callback) {
    const request = event.Records[0].cf.request;
    const headers = request.headers;

    // Add API-specific headers
    headers['x-api-version'] = [{
        key: 'X-API-Version',
        value: 'v1'
    }];

    headers['x-edge-request-time'] = [{
        key: 'X-Edge-Request-Time',
        value: Date.now().toString()
    }];

    // API rate limiting headers
    const clientId = getClientId(request);
    headers['x-client-id'] = [{
        key: 'X-Client-ID',
        value: clientId
    }];

    // Add request transformation
    const transformedRequest = transformAPIRequest(request);

    // Add caching strategy hints
    addCachingHints(transformedRequest);

    // Add security validation
    if (!validateAPIRequest(transformedRequest)) {
        const errorResponse = {
            status: '403',
            statusDescription: 'Forbidden',
            headers: {
                'content-type': [{
                    key: 'Content-Type',
                    value: 'application/json'
                }],
                'x-error': [{
                    key: 'X-Error',
                    value: 'Invalid API request'
                }]
            },
            body: JSON.stringify({
                error: 'Forbidden',
                message: 'Invalid API request',
                timestamp: new Date().toISOString()
            })
        };
        callback(null, errorResponse);
        return;
    }

    callback(null, transformedRequest);
}

function handleOriginResponse(event, callback) {
    const response = event.Records[0].cf.response;
    const headers = response.headers;

    // Add response processing headers
    headers['x-edge-response-time'] = [{
        key: 'X-Edge-Response-Time',
        value: Date.now().toString()
    }];

    // Add caching headers based on response
    addResponseCachingHeaders(response);

    // Add CORS headers for API responses
    addCORSHeaders(response);

    // Add API response transformation
    transformAPIResponse(response);

    // Add security headers
    addSecurityHeaders(response);

    // Add performance monitoring headers
    addPerformanceHeaders(response);

    callback(null, response);
}

// Helper functions
function getClientId(request) {
    const headers = request.headers;

    // Try to get client ID from various sources
    const apiKey = headers['x-api-key'] && headers['x-api-key'][0];
    const authHeader = headers['authorization'] && headers['authorization'][0];
    const clientIp = headers['x-forwarded-for'] && headers['x-forwarded-for'][0];

    if (apiKey) {
        return 'api-key-' + apiKey.value.substring(0, 8);
    } else if (authHeader) {
        return 'auth-' + authHeader.value.substring(0, 8);
    } else if (clientIp) {
        return 'ip-' + clientIp.value.split('.')[0] + '.' + clientIp.value.split('.')[1];
    }

    return 'anonymous';
}

function transformAPIRequest(request) {
    const headers = request.headers;
    const querystring = request.querystring;

    // Add request ID
    headers['x-request-id'] = [{
        key: 'X-Request-ID',
        value: generateRequestId()
    }];

    // Parse and validate query parameters
    if (querystring) {
        const params = new URLSearchParams(querystring);

        // Add parameter validation
        if (params.has('limit')) {
            const limit = parseInt(params.get('limit'));
            if (limit > 1000) {
                params.set('limit', '1000'); // Enforce maximum limit
            }
        }

        // Add pagination hints
        if (params.has('page') && params.has('limit')) {
            headers['x-pagination-info'] = [{
                key: 'X-Pagination-Info',
                value: JSON.stringify({
                    page: params.get('page'),
                    limit: params.get('limit')
                })
            }];
        }

        // Rebuild querystring
        request.querystring = params.toString();
    }

    // Add method transformation hints
    if (request.method === 'GET' && request.uri.includes('/search')) {
        headers['x-search-hints'] = [{
            key: 'X-Search-Hints',
            value: JSON.stringify({
                queryType: 'search',
                optimizeFor: 'relevance'
            })
        }];
    }

    return request;
}

function addCachingHints(request) {
    const headers = request.headers;
    const uri = request.uri;

    // Different caching strategies for different endpoints
    if (uri.includes('/api/v1/logs')) {
        // Logs are relatively static, can be cached for longer
        headers['x-cache-hint'] = [{
            key: 'X-Cache-Hint',
            value: 'long-term'
        }];
    } else if (uri.includes('/api/v1/metrics')) {
        // Metrics change frequently, shorter cache
        headers['x-cache-hint'] = [{
            key: 'X-Cache-Hint',
            value: 'short-term'
        }];
    } else if (uri.includes('/api/v1/users')) {
        // User data is sensitive, no caching
        headers['x-cache-hint'] = [{
            key: 'X-Cache-Hint',
            value: 'no-cache'
        }];
    }
}

function validateAPIRequest(request) {
    const headers = request.headers;
    const uri = request.uri;
    const method = request.method;

    // Basic validation
    if (!uri.startsWith('/api/')) {
        return false;
    }

    // Check for required headers
    if (method === 'POST' || method === 'PUT') {
        const contentType = headers['content-type'];
        if (!contentType || !contentType[0].value.includes('application/json')) {
            return false;
        }
    }

    // Check request size
    const contentLength = headers['content-length'];
    if (contentLength) {
        const size = parseInt(contentLength[0].value);
        if (size > 10 * 1024 * 1024) { // 10MB limit
            return false;
        }
    }

    // Check for suspicious patterns
    const suspiciousPatterns = [
        /<script/i,
        /javascript:/i,
        /on\w+\s*=/i,
        /union\s+select/i
    ];

    for (const pattern of suspiciousPatterns) {
        if (pattern.test(uri) || pattern.test(JSON.stringify(headers))) {
            return false;
        }
    }

    return true;
}

function addResponseCachingHeaders(response) {
    const headers = response.headers;
    const status = response.status;

    // Add caching headers based on response status
    if (status === '200') {
        headers['cache-control'] = [{
            key: 'Cache-Control',
            value: 'public, max-age=300' // 5 minutes
        }];

        headers['etag'] = [{
            key: 'ETag',
            value: generateETag(response.body || '')
        }];
    } else if (status === '304') {
        headers['cache-control'] = [{
            key: 'Cache-Control',
            value: 'public, max-age=3600' // 1 hour for 304 responses
        }];
    } else {
        // Don't cache error responses
        headers['cache-control'] = [{
            key: 'Cache-Control',
            value: 'no-cache, no-store, must-revalidate'
        }];
    }
}

function addCORSHeaders(response) {
    const headers = response.headers;

    headers['access-control-allow-origin'] = [{
        key: 'Access-Control-Allow-Origin',
        value: 'https://dmlog.com'
    }];

    headers['access-control-allow-methods'] = [{
        key: 'Access-Control-Allow-Methods',
        value: 'GET, POST, PUT, DELETE, OPTIONS'
    }];

    headers['access-control-allow-headers'] = [{
        key: 'Access-Control-Allow-Headers',
        value: 'Content-Type, Authorization, X-Requested-With, X-API-Key'
    }];

    headers['access-control-expose-headers'] = [{
        key: 'Access-Control-Expose-Headers',
        value: 'X-Total-Count, X-Page-Count, X-Request-ID'
    }];

    headers['access-control-max-age'] = [{
        key: 'Access-Control-Max-Age',
        value: '86400'
    }];
}

function transformAPIResponse(response) {
    const headers = response.headers;
    const body = response.body;

    // Add response metadata
    if (body && response.status === '200') {
        try {
            const jsonData = JSON.parse(body);

            // Add metadata to response
            const enhancedData = {
                ...jsonData,
                _metadata: {
                    timestamp: new Date().toISOString(),
                    version: '1.0',
                    requestId: headers['x-request-id'] ? headers['x-request-id'][0].value : null
                }
            };

            response.body = JSON.stringify(enhancedData);

            // Update content length
            headers['content-length'] = [{
                key: 'Content-Length',
                value: response.body.length.toString()
            }];
        } catch (e) {
            // Not JSON, leave as is
        }
    }

    // Add compression hint
    headers['x-content-compressed'] = [{
        key: 'X-Content-Compressed',
        value: 'false'
    }];
}

function addSecurityHeaders(response) {
    const headers = response.headers;

    headers['x-content-type-options'] = [{
        key: 'X-Content-Type-Options',
        value: 'nosniff'
    }];

    headers['x-frame-options'] = [{
        key: 'X-Frame-Options',
        value: 'DENY'
    }];

    headers['x-xss-protection'] = [{
        key: 'X-XSS-Protection',
        value: '1; mode=block'
    }];

    headers['strict-transport-security'] = [{
        key: 'Strict-Transport-Security',
        value: 'max-age=31536000; includeSubDomains; preload'
    }];
}

function addPerformanceHeaders(response) {
    const headers = response.headers;

    // Add server timing information
    const serverTiming = [
        'edge;dur=' + (Date.now() - parseInt(headers['x-edge-request-time'] ? headers['x-edge-request-time'][0].value : Date.now())),
        'api;desc="API processing"'
    ];

    headers['server-timing'] = [{
        key: 'Server-Timing',
        value: serverTiming.join(', ')
    }];

    // Add performance hints
    headers['x-performance-hint'] = [{
        key: 'X-Performance-Hint',
        value: JSON.stringify({
            compressible: true,
            cacheable: response.status === '200',
            streamable: false
        })
    }];
}

function generateRequestId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function generateETag(content) {
    const crypto = require('crypto');
    return crypto.createHash('md5').update(content).digest('hex');
}