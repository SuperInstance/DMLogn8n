/**
 * Main entry point for D&D AR/VR WebXR Application
 * Handles initialization, routing, and global state management
 */

import { VRTabletop } from './VRTabletop.js';
import { ARCharacterView } from './ARCharacterView.js';
import { ARVRCore } from '../../core/ARVRCore.js';
import { MixedRealityFeatures } from '../../core/MixedRealityFeatures.js';
import { CrossPlatformSupport } from '../../core/CrossPlatformSupport.js';
import { PerformanceOptimization } from '../../core/PerformanceOptimization.js';

// Global app state
window.DNDApp = {
    vrTabletop: null,
    arCharacterView: null,
    arvrCore: null,
    mixedReality: null,
    crossPlatform: null,
    performanceOptimizer: null,
    currentMode: 'unknown',
    isInitialized: false
};

// DOM elements
const loadingScreen = document.getElementById('loading-screen');
const progressBar = document.getElementById('progress-bar');
const loadingText = document.querySelector('.loading-text');

/**
 * Main application initialization
 */
async function initializeApp() {
    try {
        console.log('🎮 Initializing D&D AR/VR Application...');
        showLoading('Detecting device capabilities...');

        // Initialize core systems
        await initializeCoreSystems();

        // Detect capabilities and choose mode
        const capabilities = await detectCapabilities();
        const mode = determineAppMode(capabilities);

        // Initialize the appropriate experience
        await initializeExperience(mode);

        // Setup global event handlers
        setupEventHandlers();

        // Hide loading screen
        hideLoadingScreen();

        // Mark as initialized
        window.DNDApp.isInitialized = true;
        window.DNDApp.currentMode = mode;

        console.log(`✅ D&D AR/VR Application initialized in ${mode} mode`);

        // Show welcome message
        showWelcomeMessage(mode);

    } catch (error) {
        console.error('❌ Failed to initialize application:', error);
        showError(error);
    }
}

/**
 * Initialize core framework systems
 */
async function initializeCoreSystems() {
    showLoading('Initializing core systems...');
    updateProgress(10);

    // Initialize ARVR Core
    window.DNDApp.arvrCore = new ARVRCore({
        container: document.body,
        enableVR: true,
        enableAR: true,
        enableHandTracking: true,
        targetFPS: 90,
        antialias: true,
        alpha: true
    });

    await window.DNDApp.arvrCore.initialize();
    updateProgress(25);

    // Initialize cross-platform support
    showLoading('Setting up platform support...');
    window.DNDApp.crossPlatform = new CrossPlatformSupport(window.DNDApp.arvrCore, {
        enableQuestSupport: true,
        enableHoloLensSupport: true,
        enableARKitSupport: true,
        enableARCoreSupport: true,
        autoDetectDevice: true
    });

    await window.DNDApp.crossPlatform.initialize();
    updateProgress(40);

    // Initialize performance optimization
    showLoading('Optimizing performance...');
    window.DNDApp.performanceOptimizer = new PerformanceOptimization(window.DNDApp.arvrCore, {
        targetFPS: 90,
        enableAdaptiveQuality: true,
        enableComfortSettings: true,
        enableMotionSicknessPrevention: true,
        enableLatencyOptimization: true
    });

    await window.DNDApp.performanceOptimizer.initialize();
    updateProgress(55);

    // Initialize mixed reality features
    showLoading('Loading mixed reality features...');
    window.DNDApp.mixedReality = new MixedRealityFeatures(window.DNDApp.arvrCore, {
        enableHolograms: true,
        enableEnvironmentalEffects: true,
        enablePortals: true,
        enableMagicItems: true,
        maxHolograms: 10,
        maxEffects: 20
    });

    await window.DNDApp.mixedReality.initialize();
    updateProgress(70);
}

/**
 * Detect device capabilities
 */
async function detectCapabilities() {
    showLoading('Detecting device capabilities...');
    updateProgress(75);

    const deviceInfo = window.DNDApp.crossPlatform.getDeviceCapabilities();

    console.log('📱 Device capabilities detected:', deviceInfo);

    // Show device info in console for debugging
    console.log(`Device Type: ${deviceInfo.type}`);
    console.log(`Platform: ${deviceInfo.platform}`);
    console.log(`VR Support: ${deviceInfo.isVR}`);
    console.log(`AR Support: ${deviceInfo.isAR}`);
    console.log(`Hand Tracking: ${deviceInfo.hasHandTracking}`);
    console.log(`Eye Tracking: ${deviceInfo.hasEyeTracking}`);

    return deviceInfo;
}

/**
 * Determine which experience mode to use
 */
function determineAppMode(capabilities) {
    const urlParams = new URLSearchParams(window.location.search);
    const forcedMode = urlParams.get('mode');

    // Force mode if specified in URL
    if (forcedMode) {
        switch (forcedMode.toLowerCase()) {
            case 'vr':
                return 'vr';
            case 'ar':
                return 'ar';
            case 'web':
                return 'web';
        }
    }

    // Auto-detect based on capabilities
    if (capabilities.isVR && capabilities.type === 'meta-quest') {
        return 'vr';
    } else if (capabilities.isAR && (capabilities.type === 'ios-device' || capabilities.type === 'android-device')) {
        return 'ar';
    } else if (capabilities.isVR || capabilities.isAR) {
        return 'webxr';
    } else {
        return 'web';
    }
}

/**
 * Initialize the appropriate experience based on mode
 */
async function initializeExperience(mode) {
    showLoading(`Loading ${mode.toUpperCase()} experience...`);
    updateProgress(80);

    switch (mode) {
        case 'vr':
            await initializeVRExperience();
            break;
        case 'ar':
            await initializeARExperience();
            break;
        case 'webxr':
            await initializeWebXRExperience();
            break;
        case 'web':
            await initializeWebExperience();
            break;
        default:
            throw new Error(`Unknown experience mode: ${mode}`);
    }

    updateProgress(100);
}

/**
 * Initialize VR Tabletop experience
 */
async function initializeVRExperience() {
    console.log('🥽 Initializing VR Tabletop experience...');

    window.DNDApp.vrTabletop = new VRTabletop(document.body, {
        enableVR: true,
        enableAR: false,
        enableHandTracking: true,
        enableVoiceChat: true,
        maxPlayers: 6,
        tabletopSize: { width: 8, height: 8 },
        targetFPS: 90
    });

    const success = await window.DNDApp.vrTabletop.initialize();
    if (!success) {
        throw new Error('Failed to initialize VR Tabletop');
    }

    // Start VR session
    await window.DNDApp.crossPlatform.startSession('immersive-vr');
}

/**
 * Initialize AR Character View experience
 */
async function initializeARExperience() {
    console.log('📱 Initializing AR Character View experience...');

    // Check if we're on the AR view page
    if (!document.getElementById('ar-canvas')) {
        // Redirect to AR view
        window.location.href = 'ar-view.html';
        return;
    }

    window.DNDApp.arCharacterView = new ARCharacterView(document.body, {
        enableMarkerTracking: false,
        enablePlaneDetection: true,
        enableLightEstimation: true,
        maxPlacedObjects: 20,
        placementDistance: 2.0
    });

    const success = await window.DNDApp.arCharacterView.initialize();
    if (!success) {
        throw new Error('Failed to initialize AR Character View');
    }

    // Start AR session
    await window.DNDApp.crossPlatform.startSession('immersive-ar');
}

/**
 * Initialize WebXR experience
 */
async function initializeWebXRExperience() {
    console.log('🌐 Initializing WebXR experience...');

    // Determine if VR or AR is available and preferred
    const capabilities = window.DNDApp.crossPlatform.getDeviceCapabilities();

    if (capabilities.isVR) {
        await initializeVRExperience();
    } else if (capabilities.isAR) {
        await initializeARExperience();
    } else {
        await initializeWebExperience();
    }
}

/**
 * Initialize web (non-VR/AR) experience
 */
async function initializeWebExperience() {
    console.log('💻 Initializing web experience...');

    // Create a basic 3D scene without VR/AR
    showLoading('Creating 3D scene...');

    // Initialize a basic 3D scene
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });

    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    document.body.appendChild(renderer.domElement);

    // Add basic lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 10, 7.5);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Add a simple ground plane
    const groundGeometry = new THREE.PlaneGeometry(20, 20);
    const groundMaterial = new THREE.MeshStandardMaterial({ color: 0x3a3a3a });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);

    // Position camera
    camera.position.set(0, 5, 10);
    camera.lookAt(0, 0, 0);

    // Add orbit controls
    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
    }

    animate();

    // Store reference for cleanup
    window.DNDApp.webScene = { scene, camera, renderer, controls };

    // Show fallback UI
    showWebFallbackUI();
}

/**
 * Setup global event handlers
 */
function setupEventHandlers() {
    // Handle window resize
    window.addEventListener('resize', handleWindowResize);

    // Handle visibility change
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Handle page unload
    window.addEventListener('beforeunload', handlePageUnload);

    // Handle keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);

    // Handle performance optimization events
    if (window.DNDApp.performanceOptimizer) {
        window.DNDApp.performanceOptimizer.on('qualityLevelChanged', handleQualityChange);
    }

    // Handle cross-platform events
    if (window.DNDApp.crossPlatform) {
        window.DNDApp.crossPlatform.on('sessionStarted', handleSessionStarted);
        window.DNDApp.crossPlatform.on('sessionEnded', handleSessionEnded);
    }
}

/**
 * Event handlers
 */
function handleWindowResize() {
    if (window.DNDApp.vrTabletop) {
        window.DNDApp.vrTabletop.handleResize();
    } else if (window.DNDApp.arCharacterView) {
        window.DNDApp.arCharacterView.handleResize();
    } else if (window.DNDApp.webScene) {
        const { camera, renderer } = window.DNDApp.webScene;
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }
}

function handleVisibilityChange() {
    if (document.hidden) {
        // Pause app when tab is not visible
        pauseApp();
    } else {
        // Resume app when tab becomes visible
        resumeApp();
    }
}

function handlePageUnload() {
    // Cleanup resources
    cleanupApp();
}

function handleKeyboardShortcuts(event) {
    // Global keyboard shortcuts
    switch (event.key) {
        case 'Escape':
            handleEscapeKey();
            break;
        case 'F11':
            toggleFullscreen();
            break;
        case 'F1':
            event.preventDefault();
            showHelp();
            break;
    }
}

function handleQualityChange(data) {
    console.log(`🎯 Quality level changed to: ${data.level}`);
    showNotification(`Quality: ${data.level}`, 3000);
}

function handleSessionStarted(data) {
    console.log('🚀 Session started:', data);
    showNotification('Session started successfully!', 3000);
}

function handleSessionEnded(data) {
    console.log('🛑 Session ended:', data);
    showNotification('Session ended', 3000);
}

function handleEscapeKey() {
    // Handle escape key based on current context
    if (window.DNDApp.vrTabletop) {
        // Try to end VR session
        window.DNDApp.crossPlatform.endSession();
    } else {
        // Close modals or panels
        closeAllPanels();
    }
}

/**
 * UI Helper functions
 */
function showLoading(text = 'Loading...') {
    if (loadingText) {
        loadingText.textContent = text;
    }
    if (loadingScreen && loadingScreen.classList.contains('hidden')) {
        loadingScreen.classList.remove('hidden');
        loadingScreen.style.opacity = '1';
    }
}

function updateProgress(percent) {
    if (progressBar) {
        progressBar.style.width = `${Math.min(100, percent)}%`;
    }
}

function hideLoadingScreen() {
    if (loadingScreen) {
        loadingScreen.style.opacity = '0';
        setTimeout(() => {
            loadingScreen.classList.add('hidden');
            loadingScreen.style.opacity = '1';
        }, 500);
    }
}

function showNotification(message, duration = 5000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(26, 26, 46, 0.9);
        color: #4ecdc4;
        padding: 15px 20px;
        border-radius: 8px;
        border: 1px solid rgba(78, 205, 196, 0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
        backdrop-filter: blur(10px);
    `;

    // Add to page
    document.body.appendChild(notification);

    // Remove after duration
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in forwards';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, duration);
}

function showWelcomeMessage(mode) {
    const modeNames = {
        'vr': 'Virtual Reality',
        'ar': 'Augmented Reality',
        'webxr': 'WebXR',
        'web': 'Web'
    };

    const message = `Welcome to D&D ${modeNames[mode]} Experience!`;
    showNotification(message, 5000);
}

function showError(error) {
    console.error('Application error:', error);

    const errorDiv = document.createElement('div');
    errorDiv.innerHTML = `
        <div style="
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(220, 53, 69, 0.9);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            z-index: 10001;
            max-width: 400px;
        ">
            <h3>Error</h3>
            <p>${error.message || 'An unknown error occurred'}</p>
            <button onclick="location.reload()" style="
                margin-top: 10px;
                padding: 8px 16px;
                background: white;
                color: #dc3545;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            ">Reload</button>
        </div>
    `;

    document.body.appendChild(errorDiv);
    hideLoadingScreen();
}

function showWebFallbackUI() {
    showNotification('VR/AR not available. Showing 3D web experience.', 5000);
}

function showHelp() {
    showNotification('Help: F11 - Fullscreen | ESC - Exit | F1 - This help', 5000);
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}

function closeAllPanels() {
    // Close any open panels or modals
    const panels = document.querySelectorAll('.ui-panel');
    panels.forEach(panel => {
        if (panel.style.display !== 'none') {
            panel.style.display = 'none';
        }
    });
}

/**
 * App state management
 */
function pauseApp() {
    console.log('⏸️ Pausing application...');
    if (window.DNDApp.vrTabletop) {
        window.DNDApp.vrTabletop.pause();
    } else if (window.DNDApp.arCharacterView) {
        window.DNDApp.arCharacterView.pause();
    }
}

function resumeApp() {
    console.log('▶️ Resuming application...');
    if (window.DNDApp.vrTabletop) {
        window.DNDApp.vrTabletop.resume();
    } else if (window.DNDApp.arCharacterView) {
        window.DNDApp.arCharacterView.resume();
    }
}

function cleanupApp() {
    console.log('🧹 Cleaning up application...');

    if (window.DNDApp.vrTabletop) {
        window.DNDApp.vrTabletop.dispose();
    }

    if (window.DNDApp.arCharacterView) {
        window.DNDApp.arCharacterView.dispose();
    }

    if (window.DNDApp.mixedReality) {
        window.DNDApp.mixedReality.dispose();
    }

    if (window.DNDApp.crossPlatform) {
        window.DNDApp.crossPlatform.dispose();
    }

    if (window.DNDApp.performanceOptimizer) {
        window.DNDApp.performanceOptimizer.dispose();
    }

    if (window.DNDApp.webScene) {
        const { renderer } = window.DNDApp.webScene;
        if (renderer) {
            renderer.dispose();
        }
    }
}

/**
 * Global API functions for use from HTML
 */
window.DNDAppGlobal = {
    rollDice: function(sides) {
        if (window.DNDApp.vrTabletop) {
            window.DNDApp.vrTabletop.rollDice(sides);
        } else if (window.DNDApp.arCharacterView) {
            window.DNDApp.arCharacterView.rollVirtualDice(sides, Math.floor(Math.random() * sides) + 1);
        } else {
            console.log(`Rolling d${sides}: ${Math.floor(Math.random() * sides) + 1}`);
        }
    },

    castSpell: function(spellId) {
        if (window.DNDApp.vrTabletop) {
            window.DNDApp.vrTabletop.castSpell(spellId, null);
        } else if (window.DNDApp.arCharacterView) {
            window.DNDApp.arCharacterView.castSpellInAR(spellId);
        } else {
            console.log(`Casting spell: ${spellId}`);
        }
    },

    togglePanel: function(panelId) {
        const panel = document.getElementById(panelId);
        if (panel) {
            if (panel.style.display === 'none') {
                panel.style.display = 'block';
            } else {
                panel.style.display = 'none';
            }
        }
    },

    resetView: function() {
        if (window.DNDApp.vrTabletop) {
            window.DNDApp.vrTabletop.resetView();
        } else if (window.DNDApp.arCharacterView) {
            window.DNDApp.arCharacterView.resetARView();
        }
    },

    getPerformanceReport: function() {
        if (window.DNDApp.performanceOptimizer) {
            return window.DNDApp.performanceOptimizer.getPerformanceReport();
        }
        return null;
    }
};

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .notification {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 14px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
`;
document.head.appendChild(style);

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}