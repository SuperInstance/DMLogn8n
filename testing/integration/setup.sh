#!/bin/bash

# DMLogn8n Integration Testing Setup Script
# This script sets up the environment for integration testing

set -e

echo "🚀 Setting up DMLogn8n Integration Testing Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.8+ is installed
check_python() {
    print_status "Checking Python installation..."

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        REQUIRED_VERSION="3.8"

        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python $PYTHON_VERSION found (>= 3.8 required)"
            PYTHON_CMD="python3"
        else
            print_error "Python $PYTHON_VERSION found but >= 3.8 is required"
            exit 1
        fi
    else
        print_error "Python 3 is not installed"
        exit 1
    fi
}

# Check if pip is installed
check_pip() {
    print_status "Checking pip installation..."

    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
        print_success "pip $PIP_VERSION found"
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        PIP_VERSION=$(pip --version | cut -d' ' -f2)
        print_success "pip $PIP_VERSION found"
        PIP_CMD="pip"
    else
        print_error "pip is not installed"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."

    VENV_PATH="./venv"

    if [ -d "$VENV_PATH" ]; then
        print_warning "Virtual environment already exists at $VENV_PATH"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_PATH"
            print_status "Recreating virtual environment..."
        else
            print_status "Using existing virtual environment"
            return
        fi
    fi

    $PYTHON_CMD -m venv "$VENV_PATH"
    print_success "Virtual environment created at $VENV_PATH"
}

# Activate virtual environment and install dependencies
install_dependencies() {
    print_status "Activating virtual environment and installing dependencies..."

    # Activate virtual environment
    source "$VENV_PATH/bin/activate"

    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip

    # Install requirements
    print_status "Installing test dependencies..."
    pip install -r requirements.txt

    print_success "Dependencies installed successfully"
}

# Install Chrome/Chromium for browser tests
install_browser() {
    print_status "Checking browser installation..."

    if command -v google-chrome &> /dev/null; then
        CHROME_VERSION=$(google-chrome --version | cut -d' ' -f3)
        print_success "Google Chrome $CHROME_VERSION found"
    elif command -v chromium-browser &> /dev/null; then
        CHROMIUM_VERSION=$(chromium-browser --version | cut -d' ' -f2)
        print_success "Chromium Browser $CHROMIUM_VERSION found"
    elif command -v chromium &> /dev/null; then
        CHROMIUM_VERSION=$(chromium --version | cut -d' ' -f2)
        print_success "Chromium $CHROMIUM_VERSION found"
    else
        print_warning "No browser found. Installing Chromium..."

        # Detect OS and install accordingly
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y chromium-browser
            elif command -v yum &> /dev/null; then
                sudo yum install -y chromium
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y chromium
            else
                print_warning "Could not automatically install browser. Please install Chrome or Chromium manually."
            fi
        else
            print_warning "Automatic browser installation not supported on this OS. Please install Chrome or Chromium manually."
        fi
    fi

    # Install ChromeDriver
    print_status "Installing ChromeDriver..."
    pip install webdriver-manager
    print_success "ChromeDriver manager installed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."

    directories=(
        "logs"
        "reports"
        "screenshots"
        "debug/logs"
        "debug/snapshots"
        "debug/reports"
        "debug/traces"
        "test_data"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        fi
    done

    print_success "All necessary directories created"
}

# Set up configuration
setup_config() {
    print_status "Setting up configuration..."

    # Create environment file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
# DMLogn8n Integration Testing Environment Variables
# Override these values as needed for your environment

# Application URLs
BASE_URL=http://localhost:8000
AI_SERVICE_URL=http://localhost:8080
N8N_URL=http://localhost:5678
WEBSOCKET_URL=ws://localhost:8001

# Database URLs
DATABASE_URL=postgresql://dmlog:password@localhost:5432/dmlog_test
REDIS_URL=redis://localhost:6379/1
MONGO_URL=mongodb://localhost:27017

# Test Environment
TEST_ENVIRONMENT=development

# Browser Configuration
HEADLESS_BROWSER=true

# Debug Options
DEBUG_TESTS=false
VERBOSE_LOGGING=false

# Notifications (optional)
# SLACK_WEBHOOK_URL=your_webhook_url_here
# EMAIL_RECIPIENTS=admin@example.com
EOF
        print_success ".env file created"
    else
        print_status ".env file already exists"
    fi

    # Make setup script executable
    chmod +x setup.sh

    print_success "Configuration setup completed"
}

# Check service dependencies
check_dependencies() {
    print_status "Checking service dependencies..."

    services=(
        "PostgreSQL:5432"
        "Redis:6379"
        "MongoDB:27017"
        "Application:8000"
        "AI Service:8080"
    )

    for service in "${services[@]}"; do
        service_name=$(echo $service | cut -d':' -f1)
        port=$(echo $service | cut -d':' -f2)

        if nc -z localhost "$port" 2>/dev/null; then
            print_success "$service_name is running on port $port"
        else
            print_warning "$service_name is not running on port $port"
            print_status "  Note: Tests may fail if this service is required"
        fi
    done
}

# Run initial tests to verify setup
run_verification() {
    print_status "Running verification tests..."

    # Activate virtual environment
    source "$VENV_PATH/bin/activate"

    # Run a simple import test
    print_status "Testing Python imports..."
    python3 -c "
import sys
modules = ['pytest', 'aiohttp', 'selenium', 'psutil', 'redis', 'psycopg2', 'websockets']
failed = []
for module in modules:
    try:
        __import__(module)
        print(f'✓ {module}')
    except ImportError as e:
        failed.append(module)
        print(f'✗ {module}: {e}')

if failed:
    print(f'\\nFailed imports: {failed}')
    sys.exit(1)
else:
    print('\\nAll modules imported successfully!')
"

    if [ $? -eq 0 ]; then
        print_success "Verification tests passed"
    else
        print_error "Verification tests failed"
        exit 1
    fi
}

# Create run scripts
create_run_scripts() {
    print_status "Creating run scripts..."

    # Create main test runner
    cat > run_tests.sh << 'EOF'
#!/bin/bash

# DMLogn8n Integration Test Runner
source venv/bin/activate

# Default to running all tests
SUITE=${1:-"all"}

echo "🧪 Running DMLogn8n Integration Tests..."
echo "Suite: $SUITE"
echo "Time: $(date)"
echo "=================================="

# Run the tests
if [ "$SUITE" = "all" ]; then
    python3 integration_test_suite.py --parallel
elif [ "$SUITE" = "smoke" ]; then
    python3 integration_test_suite.py --suite smoke
elif [ "$SUITE" = "integration" ]; then
    python3 integration_test_suite.py --suite integration
elif [ "$SUITE" = "performance" ]; then
    python3 integration_test_suite.py --suite performance
elif [ "$SUITE" = "regression" ]; then
    python3 integration_test_suite.py --suite regression
elif [ "$SUITE" = "debug" ]; then
    python3 debug_tools.py
else
    echo "Unknown suite: $SUITE"
    echo "Available suites: all, smoke, integration, performance, regression, debug"
    exit 1
fi

echo "=================================="
echo "Tests completed at $(date)"
EOF

    # Create debug script
    cat > run_debug.sh << 'EOF'
#!/bin/bash

# DMLogn8n Debug Tool Runner
source venv/bin/activate

echo "🔍 Running DMLogn8n Debug Tools..."
echo "Time: $(date)"
echo "=================================="

python3 debug_tools.py

echo "=================================="
echo "Debug analysis completed at $(date)"
EOF

    # Make scripts executable
    chmod +x run_tests.sh run_debug.sh

    print_success "Run scripts created"
}

# Print final instructions
print_instructions() {
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Activate the virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Configure your environment variables in .env file"
    echo "3. Make sure all required services are running"
    echo ""
    echo "🧪 To run tests:"
    echo "   ./run_tests.sh                    # Run all tests"
    echo "   ./run_tests.sh smoke              # Run smoke tests only"
    echo "   ./run_tests.sh integration        # Run integration tests"
    echo "   ./run_tests.sh performance        # Run performance tests"
    echo "   ./run_tests.sh regression         # Run regression tests"
    echo ""
    echo "🔍 To run debug analysis:"
    echo "   ./run_debug.sh"
    echo ""
    echo "📊 Test reports will be saved in the 'reports' directory"
    echo "🐛 Debug reports will be saved in the 'debug' directory"
    echo ""
    echo "📖 For more information, see the README.md file"
    echo ""
}

# Main execution flow
main() {
    echo "DMLogn8n Integration Testing Setup"
    echo "=================================="

    check_python
    check_pip
    create_venv
    install_dependencies
    install_browser
    create_directories
    setup_config
    check_dependencies
    run_verification
    create_run_scripts
    print_instructions
}

# Run the main function
main "$@"