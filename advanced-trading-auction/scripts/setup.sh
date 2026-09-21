#!/bin/bash

# DMlogn8n Advanced Trading & Auction House System Setup Script
# This script sets up the entire development environment

set -e  # Exit on any error

echo "🚀 Setting up DMlogn8n Advanced Trading System..."

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

# Check if Node.js is installed
check_nodejs() {
    print_status "Checking Node.js installation..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js is installed: $NODE_VERSION"

        # Check if version is 16 or higher
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')
        if [ "$NODE_MAJOR" -lt 16 ]; then
            print_error "Node.js version 16 or higher is required. Current version: $NODE_VERSION"
            exit 1
        fi
    else
        print_error "Node.js is not installed. Please install Node.js 16 or higher."
        exit 1
    fi
}

# Check if PostgreSQL is installed
check_postgresql() {
    print_status "Checking PostgreSQL installation..."
    if command -v psql &> /dev/null; then
        POSTGRES_VERSION=$(psql --version)
        print_success "PostgreSQL is installed: $POSTGRES_VERSION"
    else
        print_warning "PostgreSQL is not installed. Installing PostgreSQL..."

        # Detect OS and install PostgreSQL
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y postgresql postgresql-contrib
            elif command -v yum &> /dev/null; then
                sudo yum install -y postgresql-server postgresql-contrib
                sudo postgresql-setup initdb
                sudo systemctl start postgresql
                sudo systemctl enable postgresql
            else
                print_error "Unable to install PostgreSQL automatically. Please install it manually."
                exit 1
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command -v brew &> /dev/null; then
                brew install postgresql
                brew services start postgresql
            else
                print_error "Homebrew is not installed. Please install PostgreSQL manually."
                exit 1
            fi
        else
            print_error "Unsupported operating system. Please install PostgreSQL manually."
            exit 1
        fi
    fi
}

# Check if Redis is installed
check_redis() {
    print_status "Checking Redis installation..."
    if command -v redis-server &> /dev/null; then
        REDIS_VERSION=$(redis-server --version)
        print_success "Redis is installed: $REDIS_VERSION"
    else
        print_warning "Redis is not installed. Installing Redis..."

        # Detect OS and install Redis
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            if command -v apt-get &> /dev/null; then
                sudo apt-get install -y redis-server
                sudo systemctl start redis-server
                sudo systemctl enable redis-server
            elif command -v yum &> /dev/null; then
                sudo yum install -y redis
                sudo systemctl start redis
                sudo systemctl enable redis
            else
                print_error "Unable to install Redis automatically. Please install it manually."
                exit 1
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command -v brew &> /dev/null; then
                brew install redis
                brew services start redis
            else
                print_error "Homebrew is not installed. Please install Redis manually."
                exit 1
            fi
        else
            print_error "Unsupported operating system. Please install Redis manually."
            exit 1
        fi
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."

    mkdir -p logs
    mkdir -p uploads
    mkdir -p temp
    mkdir -p backups

    print_success "Directories created successfully"
}

# Install Node.js dependencies
install_dependencies() {
    print_status "Installing Node.js dependencies..."

    # Install main dependencies
    npm install

    # Install frontend dependencies
    if [ -d "frontend" ]; then
        print_status "Installing frontend dependencies..."
        cd frontend
        npm install
        cd ..
    fi

    print_success "Dependencies installed successfully"
}

# Setup environment variables
setup_environment() {
    print_status "Setting up environment variables..."

    if [ ! -f .env ]; then
        cp .env.example .env
        print_warning ".env file created from .env.example. Please review and update the configuration."

        # Generate a random JWT secret
        JWT_SECRET=$(openssl rand -base64 32)
        sed -i "s/your-super-secret-jwt-key-here/$JWT_SECRET/" .env

        print_success "Generated random JWT secret"
    else
        print_status ".env file already exists. Skipping environment setup."
    fi
}

# Setup PostgreSQL database
setup_database() {
    print_status "Setting up PostgreSQL database..."

    # Check if database exists
    DB_NAME=$(grep DB_NAME .env | cut -d'=' -f2)
    DB_USER=$(grep DB_USER .env | cut -d'=' -f2)

    if psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
        print_warning "Database '$DB_NAME' already exists. Skipping database creation."
    else
        print_status "Creating database '$DB_NAME'..."

        # Create database
        createdb -U $DB_USER $DB_NAME || {
            print_error "Failed to create database. Please check your PostgreSQL configuration."
            print_status "You may need to create the database manually:"
            print_status "  sudo -u postgres createdb $DB_NAME"
            print_status "  sudo -u postgres createuser $DB_USER"
            exit 1
        }

        print_success "Database created successfully"
    fi

    # Run migrations
    print_status "Running database migrations..."
    npm run migrate

    # Seed the database
    print_status "Seeding the database..."
    npm run seed

    print_success "Database setup completed"
}

# Setup n8n workflows
setup_n8n() {
    print_status "Setting up n8n workflows..."

    # Check if n8n is installed
    if command -v n8n &> /dev/null; then
        print_success "n8n is installed"
    else
        print_warning "n8n is not installed. Installing n8n..."
        npm install -g n8n
    fi

    print_status "n8n workflows are available in the n8n-workflows directory"
    print_status "Import them manually from the n8n interface at http://localhost:5678"
}

# Build frontend
build_frontend() {
    if [ -d "frontend" ]; then
        print_status "Building frontend..."
        cd frontend
        npm run build
        cd ..
        print_success "Frontend built successfully"
    else
        print_warning "Frontend directory not found. Skipping frontend build."
    fi
}

# Create systemd service files (Linux only)
create_systemd_services() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_status "Creating systemd service files..."

        # Create main application service
        cat > /tmp/dmlogn8n-trading.service << EOF
[Unit]
Description=DMlogn8n Trading System
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=NODE_ENV=production
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        print_status "Systemd service file created at /tmp/dmlogn8n-trading.service"
        print_status "To install the service, run:"
        print_status "  sudo cp /tmp/dmlogn8n-trading.service /etc/systemd/system/"
        print_status "  sudo systemctl daemon-reload"
        print_status "  sudo systemctl enable dmlogn8n-trading"
        print_status "  sudo systemctl start dmlogn8n-trading"
    fi
}

# Run tests
run_tests() {
    print_status "Running tests..."

    if npm run test; then
        print_success "All tests passed"
    else
        print_warning "Some tests failed. Please check the output above."
    fi
}

# Final setup summary
setup_summary() {
    print_success "🎉 DMlogn8n Advanced Trading System setup completed!"

    echo ""
    echo "📋 Next Steps:"
    echo "1. Review and update the .env file with your configuration"
    echo "2. Start Redis: redis-server"
    echo "3. Start PostgreSQL: sudo systemctl start postgresql (Linux) or brew services start postgresql (macOS)"
    echo "4. Start the application: npm run dev"
    echo "5. Import n8n workflows from the n8n-workflows directory"
    echo ""
    echo "🌐 Access Points:"
    echo "- API: http://localhost:3001/api"
    echo "- Frontend: http://localhost:3000 (if built)"
    echo "- n8n: http://localhost:5678"
    echo ""
    echo "📚 Documentation:"
    echo "- README.md: Main documentation"
    echo "- docs/API.md: API documentation"
    echo "- docs/DATABASE.md: Database schema"
    echo ""
    echo "🔧 Development Commands:"
    echo "- npm run dev: Start development server"
    echo "- npm test: Run tests"
    echo "- npm run migrate: Run database migrations"
    echo "- npm run seed: Seed database with sample data"
}

# Main setup function
main() {
    echo "🎯 DMlogn8n Advanced Trading & Auction House System Setup"
    echo "=========================================================="
    echo ""

    # Check prerequisites
    check_nodejs
    check_postgresql
    check_redis

    # Setup
    create_directories
    install_dependencies
    setup_environment
    setup_database
    setup_n8n
    build_frontend
    create_systemd_services

    # Optional: Run tests
    read -p "Do you want to run tests? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_tests
    fi

    # Show summary
    setup_summary
}

# Check if running with sudo (not recommended)
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script with sudo. Run it as a regular user."
    exit 1
fi

# Run main function
main "$@"