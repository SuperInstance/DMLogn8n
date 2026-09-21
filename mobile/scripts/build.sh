#!/bin/bash

# DMLogn8n Mobile Build Script
# This script handles the complete build process for both iOS and Android platforms

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="DMLogn8n"
BUILD_DIR="./build"
IOS_BUILD_DIR="$BUILD_DIR/ios"
ANDROID_BUILD_DIR="$BUILD_DIR/android"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

check_dependencies() {
    log "Checking dependencies..."

    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi

    # Check npm/yarn
    if ! command -v npm &> /dev/null && ! command -v yarn &> /dev/null; then
        log_error "Neither npm nor yarn is installed"
        exit 1
    fi

    # Check React Native CLI
    if ! command -v react-native &> /dev/null; then
        log_warning "React Native CLI not found globally. Using npx..."
    fi

    # Platform-specific checks
    case "$1" in
        "ios")
            check_ios_dependencies
            ;;
        "android")
            check_android_dependencies
            ;;
        "all")
            check_ios_dependencies
            check_android_dependencies
            ;;
    esac

    log_success "Dependencies check completed"
}

check_ios_dependencies() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_warning "iOS build requires macOS. Skipping iOS dependencies check."
        return
    fi

    # Check Xcode
    if ! command -v xcodebuild &> /dev/null; then
        log_error "Xcode is not installed"
        exit 1
    fi

    # Check CocoaPods
    if ! command -v pod &> /dev/null; then
        log_error "CocoaPods is not installed. Install with: sudo gem install cocoapods"
        exit 1
    fi

    log_success "iOS dependencies verified"
}

check_android_dependencies() {
    # Check Java
    if ! command -v java &> /dev/null; then
        log_error "Java is not installed"
        exit 1
    fi

    # Check Android SDK
    if [ -z "$ANDROID_HOME" ]; then
        log_error "ANDROID_HOME environment variable is not set"
        exit 1
    fi

    # Check Gradle
    if ! command -v gradle &> /dev/null && [ ! -f "./android/gradlew" ]; then
        log_error "Gradle is not available"
        exit 1
    fi

    log_success "Android dependencies verified"
}

clean_project() {
    log "Cleaning project..."

    # Clean React Native cache
    log "Cleaning React Native cache..."
    npx react-native clean --silent 2>/dev/null || true

    # Clean Metro cache
    log "Cleaning Metro cache..."
    npx react-native start --reset-cache --silent > /dev/null 2>&1 &
    sleep 2
    pkill -f "react-native start" || true

    # Clean node modules if requested
    if [ "$CLEAN_NODE_MODULES" = "true" ]; then
        log "Removing node_modules..."
        rm -rf node_modules
        log "Reinstalling dependencies..."
        npm install
    fi

    # Clean build directories
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"

    log_success "Project cleaned"
}

install_dependencies() {
    log "Installing dependencies..."

    # Install npm dependencies
    log "Installing npm packages..."
    npm install

    # Install iOS dependencies
    if [ "$1" = "ios" ] || [ "$1" = "all" ]; then
        log "Installing iOS dependencies..."
        cd ios && pod install && cd ..
    fi

    # Install Android dependencies
    if [ "$1" = "android" ] || [ "$1" = "all" ]; then
        log "Installing Android dependencies..."
        cd android && ./gradlew clean && cd ..
    fi

    log_success "Dependencies installed"
}

build_ios() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_warning "iOS build requires macOS. Skipping iOS build."
        return
    fi

    log "Building iOS app..."

    # Build configuration
    BUILD_TYPE=${BUILD_TYPE:-"Release"}
    SCHEME=${SCHEME:-"$PROJECT_NAME"}
    WORKSPACE="${WORKSPACE:-"ios/$PROJECT_NAME.xcworkspace"}"

    # Create build directory
    mkdir -p "$IOS_BUILD_DIR"

    # Build command
    log "Building iOS app with configuration: $BUILD_TYPE"

    if [ "$BUILD_TYPE" = "Release" ]; then
        xcodebuild -workspace "$WORKSPACE" \
            -scheme "$SCHEME" \
            -configuration Release \
            -destination generic/platform=iOS \
            -archivePath "$IOS_BUILD_DIR/$PROJECT_NAME.xcarchive" \
            archive

        # Export IPA if needed
        if [ "$EXPORT_IPA" = "true" ]; then
            log "Exporting IPA..."
            xcodebuild -exportArchive \
                -archivePath "$IOS_BUILD_DIR/$PROJECT_NAME.xcarchive" \
                -exportOptionsPlist "ios/exportOptions.plist" \
                -exportPath "$IOS_BUILD_DIR"
        fi
    else
        xcodebuild -workspace "$WORKSPACE" \
            -scheme "$SCHEME" \
            -configuration Debug \
            -destination 'platform=iOS Simulator,name=iPhone 14,OS=latest' \
            build
    fi

    log_success "iOS build completed"
}

build_android() {
    log "Building Android app..."

    # Build configuration
    BUILD_TYPE=${BUILD_TYPE:-"Release"}
    VARIANT=${VARIANT:-"$BUILD_TYPE"}

    # Create build directory
    mkdir -p "$ANDROID_BUILD_DIR"

    # Build command
    log "Building Android app with variant: $VARIANT"

    cd android

    if [ "$BUILD_TYPE" = "Release" ]; then
        # Check if signing configuration is available
        if [ -f "app/release.keystore" ]; then
            ./gradlew assembleRelease
        else
            log_warning "Release keystore not found. Using debug build instead."
            ./gradlew assembleDebug
        fi

        # Bundle for Play Store if requested
        if [ "$BUNDLE_AAB" = "true" ]; then
            log "Creating Android App Bundle..."
            ./gradlew bundleRelease
        fi
    else
        ./gradlew assembleDebug
    fi

    cd ..

    # Move artifacts to build directory
    cp android/app/build/outputs/apk/*/*.apk "$ANDROID_BUILD_DIR/" 2>/dev/null || true
    cp android/app/build/outputs/bundle/*/*.aab "$ANDROID_BUILD_DIR/" 2>/dev/null || true

    log_success "Android build completed"
}

run_tests() {
    log "Running tests..."

    # Jest tests
    log "Running Jest tests..."
    npm test

    # E2E tests if requested
    if [ "$RUN_E2E" = "true" ]; then
        log "Running E2E tests..."

        if [ "$1" = "ios" ] || [ "$1" = "all" ]; then
            log "Running iOS E2E tests..."
            npm run test:ios
        fi

        if [ "$1" = "android" ] || [ "$1" = "all" ]; then
            log "Running Android E2E tests..."
            npm run test:android
        fi
    fi

    log_success "Tests completed"
}

lint_and_type_check() {
    log "Running linting and type checking..."

    # ESLint
    log "Running ESLint..."
    npm run lint

    # TypeScript type checking
    log "Running TypeScript type checking..."
    npm run type-check

    log_success "Linting and type checking completed"
}

show_usage() {
    echo "Usage: $0 [OPTIONS] [PLATFORM]"
    echo ""
    echo "PLATFORM:"
    echo "  ios       Build iOS app"
    echo "  android   Build Android app"
    echo "  all       Build both iOS and Android apps (default)"
    echo ""
    echo "OPTIONS:"
    echo "  --clean               Clean project before building"
    echo "  --test                Run tests before building"
    echo "  --lint                Run linting and type checking"
    echo "  --install-deps        Install dependencies before building"
    echo "  --build-type TYPE     Build type: Debug or Release (default: Release)"
    echo "  --clean-node-modules  Remove and reinstall node_modules"
    echo "  --export-ipa          Export IPA for iOS builds"
    echo "  --bundle-aab          Create Android App Bundle"
    echo "  --run-e2e             Run E2E tests"
    echo "  --help, -h            Show this help message"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  BUILD_TYPE            Build type (Debug/Release)"
    echo "  CLEAN_NODE_MODULES    Set to 'true' to clean node_modules"
    echo "  RUN_E2E               Set to 'true' to run E2E tests"
    echo "  EXPORT_IPA            Set to 'true' to export iOS IPA"
    echo "  BUNDLE_AAB            Set to 'true' to create Android AAB"
}

main() {
    local platform="all"
    local clean=false
    local test=false
    local lint=false
    local install_deps=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean)
                clean=true
                shift
                ;;
            --test)
                test=true
                shift
                ;;
            --lint)
                lint=true
                shift
                ;;
            --install-deps)
                install_deps=true
                shift
                ;;
            --build-type)
                BUILD_TYPE="$2"
                shift 2
                ;;
            --clean-node-modules)
                CLEAN_NODE_MODULES=true
                shift
                ;;
            --export-ipa)
                EXPORT_IPA=true
                shift
                ;;
            --bundle-aab)
                BUNDLE_AAB=true
                shift
                ;;
            --run-e2e)
                RUN_E2E=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            ios|android|all)
                platform="$1"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    log "Starting DMLogn8n mobile build process..."
    log "Platform: $platform"
    log "Build Type: ${BUILD_TYPE:-"Release"}"

    # Check dependencies
    check_dependencies "$platform"

    # Clean project if requested
    if [ "$clean" = "true" ]; then
        clean_project
    fi

    # Install dependencies if requested
    if [ "$install_deps" = "true" ]; then
        install_dependencies "$platform"
    fi

    # Run tests if requested
    if [ "$test" = "true" ]; then
        run_tests "$platform"
    fi

    # Run linting and type checking if requested
    if [ "$lint" = "true" ]; then
        lint_and_type_check
    fi

    # Build the application
    case "$platform" in
        "ios")
            build_ios
            ;;
        "android")
            build_android
            ;;
        "all")
            build_ios
            build_android
            ;;
    esac

    log_success "Build process completed successfully!"

    # Show build artifacts
    if [ -d "$BUILD_DIR" ]; then
        log "Build artifacts:"
        find "$BUILD_DIR" -type f -name "*.apk" -o -name "*.aab" -o -name "*.ipa" | while read file; do
            log "  - $file"
        done
    fi
}

# Run main function with all arguments
main "$@"