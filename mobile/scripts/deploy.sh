#!/bin/bash

# DMLogn8n Mobile Deployment Script
# Handles deployment to various environments and app stores

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="DMLogn8n"
VERSION=$(node -p "require('./package.json').version")
BUILD_DIR="./build"
DEPLOY_DIR="./deploy"

# Environment configurations
declare -A ENVIRONMENTS=(
    ["development"]="Development build for testing"
    ["staging"]="Staging build for QA testing"
    ["production"]="Production build for app stores"
)

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

check_prerequisites() {
    log "Checking deployment prerequisites..."

    # Check if we're in the right directory
    if [ ! -f "package.json" ]; then
        log_error "package.json not found. Please run this script from the project root."
        exit 1
    fi

    # Check if the project is clean (no uncommitted changes)
    if [ "$SKIP_GIT_CHECK" != "true" ]; then
        if ! git diff-index --quiet HEAD --; then
            log_error "Working directory is not clean. Please commit or stash changes first."
            exit 1
        fi
    fi

    # Check if current branch is deployable
    if [ "$SKIP_BRANCH_CHECK" != "true" ]; then
        current_branch=$(git branch --show-current)
        if [ "$ENVIRONMENT" = "production" ] && [ "$current_branch" != "main" ]; then
            log_error "Production deployments must be from the main branch. Current branch: $current_branch"
            exit 1
        fi
    fi

    log_success "Prerequisites check passed"
}

prepare_environment() {
    local env="$1"
    log "Preparing $env environment..."

    # Create environment-specific configuration
    case "$env" in
        "development")
            export NODE_ENV="development"
            export BUILD_TYPE="Debug"
            export API_URL="http://dev-api.dmlogn8n.com"
            export WS_URL="ws://dev-api.dmlogn8n.com"
            ;;
        "staging")
            export NODE_ENV="production"
            export BUILD_TYPE="Release"
            export API_URL="https://staging-api.dmlogn8n.com"
            export WS_URL="wss://staging-api.dmlogn8n.com"
            ;;
        "production")
            export NODE_ENV="production"
            export BUILD_TYPE="Release"
            export API_URL="https://api.dmlogn8n.com"
            export WS_URL="wss://api.dmlogn8n.com"
            ;;
    esac

    # Create environment file
    cat > ".env.$env" << EOF
NODE_ENV=$NODE_ENV
BUILD_TYPE=$BUILD_TYPE
API_URL=$API_URL
WS_URL=$WS_URL
VERSION=$VERSION
ENVIRONMENT=$env
EOF

    log_success "Environment $env prepared"
}

build_application() {
    local platform="$1"
    log "Building $platform application for $ENVIRONMENT..."

    # Run build script
    ./scripts/build.sh --clean --install-deps --lint --build-type "$BUILD_TYPE" "$platform"

    log_success "$platform build completed"
}

create_deployment_package() {
    local platform="$1"
    log "Creating deployment package for $platform..."

    local package_dir="$DEPLOY_DIR/$ENVIRONMENT/$platform"
    mkdir -p "$package_dir"

    case "$platform" in
        "ios")
            # Copy iOS artifacts
            if [ -f "$BUILD_DIR/ios/$PROJECT_NAME.ipa" ]; then
                cp "$BUILD_DIR/ios/$PROJECT_NAME.ipa" "$package_dir/"
            fi

            if [ -f "$BUILD_DIR/ios/$PROJECT_NAME.xcarchive" ]; then
                cp -r "$BUILD_DIR/ios/$PROJECT_NAME.xcarchive" "$package_dir/"
            fi

            # Create Info.plist summary
            if [ -f "$BUILD_DIR/ios/$PROJECT_NAME.xcarchive/Info.plist" ]; then
                /usr/libexec/PlistBuddy -c "Print" "$BUILD_DIR/ios/$PROJECT_NAME.xcarchive/Info.plist" > "$package_dir/archive-info.txt"
            fi
            ;;
        "android")
            # Copy Android artifacts
            find "$BUILD_DIR/android" -name "*.apk" -exec cp {} "$package_dir/" \;
            find "$BUILD_DIR/android" -name "*.aab" -exec cp {} "$package_dir/" \;

            # Create build summary
            find "$BUILD_DIR/android" -name "*.apk" -o -name "*.aab" | while read file; do
                echo "$(basename "$file") - $(stat -f%z "$file") bytes" >> "$package_dir/build-summary.txt"
            done
            ;;
    esac

    # Copy deployment metadata
    cat > "$package_dir/deployment.json" << EOF
{
  "project": "$PROJECT_NAME",
  "version": "$VERSION",
  "environment": "$ENVIRONMENT",
  "platform": "$platform",
  "build_type": "$BUILD_TYPE",
  "api_url": "$API_URL",
  "ws_url": "$WS_URL",
  "built_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "git_commit": "$(git rev-parse HEAD)",
  "git_branch": "$(git branch --show-current)"
}
EOF

    # Create checksums
    cd "$package_dir"
    if command -v sha256sum &> /dev/null; then
        sha256sum * > checksums.txt
    elif command -v shasum &> /dev/null; then
        shasum -a 256 * > checksums.txt
    fi
    cd - > /dev/null

    log_success "Deployment package created for $platform"
}

upload_to_distribution() {
    local platform="$1"
    log "Uploading $platform distribution..."

    case "$platform" in
        "ios")
            upload_ios_distribution
            ;;
        "android")
            upload_android_distribution
            ;;
    esac
}

upload_ios_distribution() {
    local package_dir="$DEPLOY_DIR/$ENVIRONMENT/ios"
    local ipa_path="$package_dir/$PROJECT_NAME.ipa"

    if [ ! -f "$ipa_path" ]; then
        log_warning "IPA file not found. Skipping iOS distribution upload."
        return
    fi

    case "$ENVIRONMENT" in
        "development"|"staging")
            # Upload to TestFlight or alternative distribution service
            if command -v xcrun &> /dev/null && [ -f "$package_dir/$PROJECT_NAME.xcarchive" ]; then
                log "Uploading to TestFlight..."
                xcrun altool --upload-app \
                    --type ios \
                    --file "$ipa_path" \
                    --username "$APPLE_ID" \
                    --password "$APPLE_APP_PASSWORD" \
                    --asc-provider "$APPLE_TEAM_ID"
            else
                log_warning "xcrun not available or archive not found. Skipping TestFlight upload."
            fi
            ;;
        "production")
            log "Production iOS deployment requires manual App Store Connect submission."
            log "Please upload the IPA file to App Store Connect manually."
            ;;
    esac

    log_success "iOS distribution upload completed"
}

upload_android_distribution() {
    local package_dir="$DEPLOY_DIR/$ENVIRONMENT/android"
    local aab_path=$(find "$package_dir" -name "*.aab" | head -n 1)
    local apk_path=$(find "$package_dir" -name "*.apk" | head -n 1)

    case "$ENVIRONMENT" in
        "development"|"staging")
            # Upload to Firebase App Distribution or alternative service
            if [ -n "$aab_path" ]; then
                log "Uploading AAB to Firebase App Distribution..."
                if command -v firebase &> /dev/null; then
                    firebase appdistribution:distribute \
                        "$aab_path" \
                        --app "$FIREBASE_ANDROID_APP_ID" \
                        --release-notes "Version $VERSION - $ENVIRONMENT build" \
                        --groups "testers"
                else
                    log_warning "Firebase CLI not installed. Skipping Firebase App Distribution."
                fi
            fi

            # Alternative: Upload APK directly to testing service
            if [ -n "$apk_path" ]; then
                log "APK file available for direct distribution: $apk_path"
            fi
            ;;
        "production")
            if [ -n "$aab_path" ]; then
                log "Production Android AAB ready for Google Play Console upload."
                log "Please upload the AAB file to Google Play Console manually."
                log "AAB path: $aab_path"
            fi
            ;;
    esac

    log_success "Android distribution upload completed"
}

deploy_to_backend() {
    log "Deploying backend services..."

    # Deploy mobile backend services
    cd ../backend

    case "$ENVIRONMENT" in
        "development")
            log "Starting development backend services..."
            python mobile_api.py &
            python push_service.py &
            python offline_sync.py &
            python mobile_auth.py &
            ;;
        "staging")
            log "Deploying to staging environment..."
            # Add staging deployment logic here
            ;;
        "production")
            log "Deploying to production environment..."
            # Add production deployment logic here
            ;;
    esac

    cd - > /dev/null
    log_success "Backend deployment completed"
}

create_deployment_summary() {
    log "Creating deployment summary..."

    local summary_file="$DEPLOY_DIR/deployment-summary-$ENVIRONMENT-$VERSION.md"

    cat > "$summary_file" << EOF
# DMLogn8n Mobile Deployment Summary

## Environment: $ENVIRONMENT
## Version: $VERSION
## Deployed: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Build Information
- Build Type: $BUILD_TYPE
- Git Commit: $(git rev-parse HEAD)
- Git Branch: $(git branch --show-current)
- Node Version: $(node --version)
- React Native Version: $(npx react-native --version)

## API Configuration
- API URL: $API_URL
- WebSocket URL: $WS_URL

## Artifacts
EOF

    # List all artifacts
    find "$DEPLOY_DIR/$ENVIRONMENT" -type f -name "*.apk" -o -name "*.aab" -o -name "*.ipa" | while read file; do
        echo "- $(basename "$file") ($(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "unknown") bytes)" >> "$summary_file"
    done

    cat >> "$summary_file" << EOF

## Verification Checklist
- [ ] App builds successfully
- [ ] Basic functionality tests pass
- [ ] API connectivity verified
- [ ] Push notifications work
- [ ] Offline mode functions
- [ ] Biometric authentication works
- [ ] Performance meets requirements
- [ ] Security scan passed

## Next Steps
- Monitor deployment metrics
- Check for crash reports
- Review user feedback
- Plan next release
EOF

    log_success "Deployment summary created: $summary_file"
}

notify_team() {
    log "Sending deployment notifications..."

    # Slack notification (if webhook is configured)
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        local message="🚀 DMLogn8n Mobile v$VERSION deployed to $ENVIRONMENT"
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || log_warning "Failed to send Slack notification"
    fi

    # Email notification (if configured)
    if [ -n "$DEPLOYMENT_EMAIL" ]; then
        echo "DMLogn8n Mobile v$VERSION has been deployed to $ENVIRONMENT" | \
            mail -s "Deployment Notification: $PROJECT_NAME v$VERSION" "$DEPLOYMENT_EMAIL" 2>/dev/null || \
            log_warning "Failed to send email notification"
    fi

    log_success "Team notifications sent"
}

cleanup() {
    log "Cleaning up temporary files..."

    # Remove environment files
    rm -f ".env.$ENVIRONMENT"

    # Clean up build artifacts older than 7 days
    find "$BUILD_DIR" -type f -mtime +7 -delete 2>/dev/null || true

    log_success "Cleanup completed"
}

show_usage() {
    echo "Usage: $0 [OPTIONS] ENVIRONMENT [PLATFORM]"
    echo ""
    echo "ENVIRONMENT:"
    echo "  development   Deploy to development environment"
    echo "  staging       Deploy to staging environment"
    echo "  production    Deploy to production environment"
    echo ""
    echo "PLATFORM (optional):"
    echo "  ios           Deploy iOS only"
    echo "  android       Deploy Android only"
    echo "  all           Deploy both platforms (default)"
    echo ""
    echo "OPTIONS:"
    echo "  --skip-git-check      Skip git status check"
    echo "  --skip-branch-check  Skip branch validation"
    echo "  --skip-build         Skip application build"
    echo "  --skip-upload        Skip distribution upload"
    echo "  --skip-backend       Skip backend deployment"
    echo "  --skip-notify        Skip team notifications"
    echo "  --skip-cleanup       Skip cleanup"
    echo "  --help, -h           Show this help message"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  APPLE_ID              Apple ID for TestFlight uploads"
    echo "  APPLE_APP_PASSWORD    App-specific password for Apple ID"
    echo "  APPLE_TEAM_ID         Apple Developer Team ID"
    echo "  FIREBASE_ANDROID_APP_ID Firebase Android app ID"
    echo "  SLACK_WEBHOOK_URL     Slack webhook URL for notifications"
    echo "  DEPLOYMENT_EMAIL      Email address for notifications"
}

main() {
    local environment=""
    local platform="all"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-git-check)
                SKIP_GIT_CHECK=true
                shift
                ;;
            --skip-branch-check)
                SKIP_BRANCH_CHECK=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-upload)
                SKIP_UPLOAD=true
                shift
                ;;
            --skip-backend)
                SKIP_BACKEND=true
                shift
                ;;
            --skip-notify)
                SKIP_NOTIFY=true
                shift
                ;;
            --skip-cleanup)
                SKIP_CLEANUP=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            development|staging|production)
                environment="$1"
                shift
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

    # Validate environment
    if [ -z "$environment" ]; then
        log_error "Environment is required"
        show_usage
        exit 1
    fi

    if [ -z "${ENVIRONMENTS[$environment]}" ]; then
        log_error "Invalid environment: $environment"
        show_usage
        exit 1
    fi

    # Export environment variable
    export ENVIRONMENT="$environment"

    log "Starting DMLogn8n mobile deployment..."
    log "Environment: $environment"
    log "Platform: $platform"
    log "Version: $VERSION"

    # Deployment pipeline
    check_prerequisites
    prepare_environment "$environment"

    if [ "$SKIP_BUILD" != "true" ]; then
        case "$platform" in
            "ios")
                build_application "ios"
                ;;
            "android")
                build_application "android"
                ;;
            "all")
                build_application "ios"
                build_application "android"
                ;;
        esac
    fi

    # Create deployment packages
    case "$platform" in
        "ios")
            create_deployment_package "ios"
            ;;
        "android")
            create_deployment_package "android"
            ;;
        "all")
            create_deployment_package "ios"
            create_deployment_package "android"
            ;;
    esac

    if [ "$SKIP_UPLOAD" != "true" ]; then
        case "$platform" in
            "ios")
                upload_to_distribution "ios"
                ;;
            "android")
                upload_to_distribution "android"
                ;;
            "all")
                upload_to_distribution "ios"
                upload_to_distribution "android"
                ;;
        esac
    fi

    if [ "$SKIP_BACKEND" != "true" ]; then
        deploy_to_backend
    fi

    create_deployment_summary

    if [ "$SKIP_NOTIFY" != "true" ]; then
        notify_team
    fi

    if [ "$SKIP_CLEANUP" != "true" ]; then
        cleanup
    fi

    log_success "Deployment completed successfully!"
    log "Environment: $environment"
    log "Version: $VERSION"
    log "Platform: $platform"

    # Show deployment artifacts
    if [ -d "$DEPLOY_DIR/$environment" ]; then
        log "Deployment artifacts:"
        find "$DEPLOY_DIR/$environment" -type f -name "*.apk" -o -name "*.aab" -o -name "*.ipa" | while read file; do
            log "  - $file"
        done
    fi
}

# Run main function with all arguments
main "$@"