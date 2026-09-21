'use strict';

// Lambda@Edge function for content transformation
exports.handler = (event, context, callback) => {
    const request = event.Records[0].cf.request;
    const headers = request.headers;

    // Add custom headers for tracking
    headers['x-edge-location'] = [{
        key: 'X-Edge-Location',
        value: event.Records[0].cf.config.edgeLocation || 'unknown'
    }];

    headers['x-edge-request-id'] = [{
        key: 'X-Edge-Request-ID',
        value: context.awsRequestId
    }];

    // Add A/B testing headers
    const abTestGroup = getABTestGroup(request);
    headers['x-ab-test-group'] = [{
        key: 'X-AB-Test-Group',
        value: abTestGroup
    }];

    // Handle feature flags
    const featureFlags = getFeatureFlags(request);
    headers['x-feature-flags'] = [{
        key: 'X-Feature-Flags',
        value: JSON.stringify(featureFlags)
    }];

    // Add cache key optimization
    if (request.uri.includes('/api/')) {
        // Add user context to cache key for personalized content
        const userId = getUserIdFromHeaders(headers);
        if (userId) {
            headers['x-user-cache-key'] = [{
                key: 'X-User-Cache-Key',
                value: userId
            }];
        }
    }

    // Handle static asset optimization
    if (isStaticAsset(request.uri)) {
        // Add asset versioning
        const assetVersion = getAssetVersion(request.uri);
        if (assetVersion) {
            headers['x-asset-version'] = [{
                key: 'X-Asset-Version',
                value: assetVersion
            }];
        }
    }

    // Add performance monitoring headers
    headers['x-edge-start-time'] = [{
        key: 'X-Edge-Start-Time',
        value: Date.now().toString()
    }];

    // Handle mobile optimization
    if (isMobileRequest(request)) {
        headers['x-mobile-optimized'] = [{
            key: 'X-Mobile-Optimized',
            value: 'true'
        }];
    }

    // Handle bot requests
    if (isBotRequest(request)) {
        // Serve reduced content for bots
        headers['x-bot-content'] = [{
            key: 'X-Bot-Content',
            value: 'reduced'
        }];
    }

    // Add security headers
    headers['x-edge-security-score'] = [{
        key: 'X-Edge-Security-Score',
        value: calculateSecurityScore(request).toString()
    }];

    // Handle content compression hints
    if (shouldCompress(request)) {
        headers['x-content-compression'] = [{
            key: 'X-Content-Compression',
            value: 'gzip'
        }];
    }

    // Add latency optimization hints
    const latencyHint = getLatencyHint(request);
    if (latencyHint) {
        headers['x-latency-hint'] = [{
            key: 'X-Latency-Hint',
            value: latencyHint
        }];
    }

    callback(null, request);
};

// Helper functions
function getABTestGroup(request) {
    const cookies = request.cookies || [];
    const abTestCookie = cookies.find(cookie => cookie.name === 'dmlog_ab_test');

    if (abTestCookie) {
        return abTestCookie.value;
    }

    // Assign new user to a test group
    const groups = ['control', 'variant-a', 'variant-b'];
    const randomIndex = Math.floor(Math.random() * groups.length);
    return groups[randomIndex];
}

function getFeatureFlags(request) {
    const flags = {
        'new-dashboard': false,
        'enhanced-search': false,
        'real-time-updates': false,
        'advanced-analytics': false
    };

    const cookies = request.cookies || [];
    const featureFlagsCookie = cookies.find(cookie => cookie.name === 'dmlog_features');

    if (featureFlagsCookie) {
        try {
            const cookieFlags = JSON.parse(decodeURIComponent(featureFlagsCookie.value));
            return { ...flags, ...cookieFlags };
        } catch (e) {
            // Ignore invalid cookie format
        }
    }

    // Enable features based on A/B test group
    const abTestGroup = getABTestGroup(request);
    if (abTestGroup === 'variant-a') {
        flags['new-dashboard'] = true;
        flags['enhanced-search'] = true;
    } else if (abTestGroup === 'variant-b') {
        flags['real-time-updates'] = true;
        flags['advanced-analytics'] = true;
    }

    return flags;
}

function getUserIdFromHeaders(headers) {
    const authHeader = headers['authorization'] && headers['authorization'][0];
    if (authHeader && authHeader.value.startsWith('Bearer ')) {
        try {
            // Extract user ID from JWT token (simplified)
            const token = authHeader.value.substring(7);
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.sub || payload.user_id;
        } catch (e) {
            // Invalid token
        }
    }

    return null;
}

function isStaticAsset(uri) {
    const staticExtensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf'];
    return staticExtensions.some(ext => uri.includes(ext));
}

function getAssetVersion(uri) {
    // Extract version from query parameters or path
    const url = new URL(uri, 'https://example.com');
    const version = url.searchParams.get('v');

    if (version) {
        return version;
    }

    // Extract from path pattern /assets/v1.2.3/file.js
    const versionMatch = uri.match(/\/v?(\d+\.\d+\.\d+)\//);
    return versionMatch ? versionMatch[1] : null;
}

function isMobileRequest(request) {
    const userAgent = request.headers['user-agent'] && request.headers['user-agent'][0];
    return userAgent && userAgent.value.toLowerCase().includes('mobile');
}

function isBotRequest(request) {
    const userAgent = request.headers['user-agent'] && request.headers['user-agent'][0];
    if (!userAgent) return false;

    const botPatterns = [
        /bot/i, /crawler/i, /spider/i, /scraper/i,
        /curl/i, /wget/i, /python/i, /java/i, /node/i
    ];

    return botPatterns.some(pattern => pattern.test(userAgent.value));
}

function calculateSecurityScore(request) {
    let score = 100;

    // Deduct points for suspicious patterns
    const userAgent = request.headers['user-agent'] && request.headers['user-agent'][0];
    if (isBotRequest(request)) {
        score -= 10;
    }

    // Check for suspicious query parameters
    const uri = request.uri.toLowerCase();
    if (uri.includes('sql') || uri.includes('script') || uri.includes('<')) {
        score -= 30;
    }

    // Check for unusual headers
    const suspiciousHeaders = ['x-forwarded-for', 'x-real-ip', 'x-originating-ip'];
    const headerCount = Object.keys(request.headers).length;
    if (headerCount > 20) {
        score -= 10;
    }

    return Math.max(0, score);
}

function shouldCompress(request) {
    const acceptEncoding = request.headers['accept-encoding'] && request.headers['accept-encoding'][0];
    return acceptEncoding && acceptEncoding.value.includes('gzip');
}

function getLatencyHint(request) {
    const uri = request.uri;

    if (uri.includes('/api/')) {
        return 'low-latency'; // API calls need fast response
    } else if (isStaticAsset(uri)) {
        return 'cache-optimal'; // Static assets can be cached heavily
    } else {
        return 'balanced'; // Balanced approach for regular content
    }
}