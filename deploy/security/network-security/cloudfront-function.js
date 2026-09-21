// CloudFront Function for Security Headers
// Adds security headers to all responses

function handler(event) {
    var response = event.response;
    var headers = response.headers;

    // Strict-Transport-Security
    headers['strict-transport-security'] = {
        value: 'max-age=31536000; includeSubDomains; preload'
    };

    // Content-Security-Policy
    headers['content-security-policy'] = {
        value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https:; frame-ancestors 'none';"
    };

    // X-Content-Type-Options
    headers['x-content-type-options'] = {
        value: 'nosniff'
    };

    // X-Frame-Options
    headers['x-frame-options'] = {
        value: 'DENY'
    };

    // X-XSS-Protection
    headers['x-xss-protection'] = {
        value: '1; mode=block'
    };

    // Referrer-Policy
    headers['referrer-policy'] = {
        value: 'strict-origin-when-cross-origin'
    };

    // Permissions-Policy
    headers['permissions-policy'] = {
        value: 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()'
    };

    // Cache-Control for security
    if (event.request.uri.includes('/api/')) {
        headers['cache-control'] = {
            value: 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0'
        };
    }

    // Remove server information
    delete headers['server'];
    delete headers['x-powered-by'];

    return response;
}