// CloudFront Function for request processing
function handler(event) {
    var request = event.request;
    var headers = request.headers;

    // Add security headers
    headers['x-frame-options'] = { value: 'DENY' };
    headers['x-content-type-options'] = { value: 'nosniff' };
    headers['x-xss-protection'] = { value: '1; mode=block' };
    headers['strict-transport-security'] = { value: 'max-age=31536000; includeSubDomains; preload' };
    headers['referrer-policy'] = { value: 'strict-origin-when-cross-origin' };
    headers['content-security-policy'] = {
        value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.dmlog.com; frame-ancestors 'none';"
    };

    // Add request ID header
    headers['x-request-id'] = { value: generateRequestId() };

    // Add timestamp header
    headers['x-edge-timestamp'] = { value: Date.now().toString() };

    // Handle CORS for API requests
    if (request.uri.startsWith('/api/')) {
        headers['access-control-allow-origin'] = { value: 'https://dmlog.com' };
        headers['access-control-allow-methods'] = { value: 'GET, POST, PUT, DELETE, OPTIONS' };
        headers['access-control-allow-headers'] = { value: 'Content-Type, Authorization, X-Requested-With' };
        headers['access-control-allow-credentials'] = { value: 'true' };
        headers['access-control-max-age'] = { value: '86400' };
    }

    // Handle preflight requests
    if (request.method === 'OPTIONS') {
        return {
            statusCode: 200,
            statusDescription: 'OK',
            headers: headers,
            body: ''
        };
    }

    // Add user agent analysis
    var userAgent = headers['user-agent'] ? headers['user-agent'].value : '';
    if (userAgent.includes('bot') || userAgent.includes('crawler')) {
        headers['x-user-type'] = { value: 'bot' };
    } else if (userAgent.includes('mobile')) {
        headers['x-user-type'] = { value: 'mobile' };
    } else {
        headers['x-user-type'] = { value: 'desktop' };
    }

    // Geographic routing hints
    if (event.context && event.context.geolocation) {
        var geo = event.context.geolocation;
        headers['x-geo-country'] = { value: geo.country || 'unknown' };
        headers['x-geo-region'] = { value: geo.region || 'unknown' };
        headers['x-geo-city'] = { value: geo.city || 'unknown' };
    }

    // Device detection
    if (event.context && event.context.device) {
        headers['x-device-type'] = { value: event.context.device.type || 'unknown' };
    }

    return request;
}

function generateRequestId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0;
        var v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}