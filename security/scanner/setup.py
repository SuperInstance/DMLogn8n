#!/usr/bin/env python3
"""
DMLogn8n Security Scanner System - Setup Script
Installation and configuration for the comprehensive security scanning system
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

def print_step(step, description):
    """Print a step description"""
    print(f"\n{'='*60}")
    print(f"Step {step}: {description}")
    print('='*60)

def run_command(command, description=""):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check Python version compatibility"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def create_virtual_environment():
    """Create Python virtual environment"""
    venv_path = "/home/activeloguser/DMLogn8n/security-env"
    if os.path.exists(venv_path):
        print(f"✅ Virtual environment already exists at {venv_path}")
        return venv_path

    print(f"Creating virtual environment at {venv_path}")
    if run_command(f"python3 -m venv {venv_path}", "Creating virtual environment"):
        print(f"✅ Virtual environment created at {venv_path}")
        return venv_path
    else:
        print("❌ Failed to create virtual environment")
        return None

def install_dependencies():
    """Install Python dependencies"""
    requirements_path = "/home/activeloguser/DMLogn8n/security/requirements.txt"
    if not os.path.exists(requirements_path):
        print("❌ Requirements file not found")
        return False

    print("Installing Python dependencies...")
    if run_command(
        f"pip install -r {requirements_path}",
        "Installing dependencies from requirements.txt"
    ):
        print("✅ Dependencies installed successfully")
        return True
    else:
        print("❌ Failed to install dependencies")
        return False

def install_system_dependencies():
    """Install system-level dependencies"""
    print("Installing system dependencies...")

    commands = [
        ("apt update", "Updating package lists"),
        ("apt install -y python3-pip python3-venv sqlite3 nmap git curl wget", "Installing core packages"),
        ("apt install -y libffi-dev libssl-dev", "Installing cryptographic libraries"),
        ("apt install -y net-tools iproute2", "Installing network tools"),
    ]

    for cmd, desc in commands:
        if not run_command(cmd, desc):
            print(f"⚠️  Warning: {desc} failed. You may need to install manually.")

def create_directories():
    """Create necessary directory structure"""
    print("Creating directory structure...")

    directories = [
        "/home/activeloguser/DMLogn8n/security/config",
        "/home/activeloguser/DMLogn8n/security/logs",
        "/home/activeloguser/DMLogn8n/security/data",
        "/home/activeloguser/DMLogn8n/security/reports",
        "/home/activeloguser/DMLogn8n/security/templates",
        "/home/activeloguser/DMLogn8n/security/wordlists",
        "/home/activeloguser/DMLogn8n/security/backups",
        "/home/activeloguser/DMLogn8n/security/evidence",
        "/home/activeloguser/DMLogn8n/security/workspace"
    ]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create directory {directory}: {e}")

def setup_database():
    """Initialize SQLite databases"""
    print("Setting up databases...")

    # The databases will be created automatically when the modules are imported
    print("✅ Databases will be initialized on first run")

def create_wordlists():
    """Create basic wordlists for security testing"""
    wordlist_dir = "/home/activeloguser/DMLogn8n/security/wordlists"

    # Create basic usernames wordlist
    usernames_path = os.path.join(wordlist_dir, "usernames.txt")
    if not os.path.exists(usernames_path):
        with open(usernames_path, 'w') as f:
            f.write("admin\nadministrator\nroot\ntest\nguest\nuser\ndemo\napi\nservice\nbackup\noracle\npostgres\nmysql\nwww\nftp\nmail\nemail\nweb\nwww-data\nnobody\napache\nnginx\ntomcat\njboss\nweblogic\nspring\ndjango\n")

    # Create basic passwords wordlist
    passwords_path = os.path.join(wordlist_dir, "passwords.txt")
    if not os.path.exists(passwords_path):
        with open(passwords_path, 'w') as f:
            f.write("password\n123456\nadmin\nroot\ntest\nguest\nuser\npassword123\n12345678\nqwerty\nabc123\nPassword1\nadmin123\nroot123\ntest123\nguest123\nuser123\nchangeme\ndefault\nletmein\nwelcome\nmonkey\n")

    # Create basic subdomains wordlist
    subdomains_path = os.path.join(wordlist_dir, "subdomains.txt")
    if not os.path.exists(subdomains_path):
        with open(subdomains_path, 'w') as f:
            f.write("www\nmail\nftp\nadmin\ntest\ndev\nstaging\napi\nblog\nshop\nsupport\nhelp\ndocs\nvpn\nremote\nportal\nsecure\ninternal\nprivate\npublic\nassets\n")

    print("✅ Basic wordlists created")

def create_systemd_service():
    """Create systemd service for security monitoring"""
    service_content = """[Unit]
Description=DMLogn8n Security Monitor
After=network.target

[Service]
Type=simple
User=activeloguser
WorkingDirectory=/home/activeloguser/DMLogn8n
Environment=PATH=/home/activeloguser/DMLogn8n/security-env/bin
ExecStart=/home/activeloguser/DMLogn8n/security-env/bin/python /home/activeloguser/DMLogn8n/security/scanner/main.py --monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    service_path = "/etc/systemd/system/dmlogn8n-security.service"

    try:
        with open('dmlogn8n-security.service', 'w') as f:
            f.write(service_content)

        print("Creating systemd service...")
        if run_command("sudo mv dmlogn8n-security.service /etc/systemd/system/", "Moving service file"):
            run_command("sudo systemctl daemon-reload", "Reloading systemd")
            run_command("sudo systemctl enable dmlogn8n-security", "Enabling service")
            print("✅ Systemd service created and enabled")
            print("To start the service: sudo systemctl start dmlogn8n-security")
            print("To check status: sudo systemctl status dmlogn8n-security")
        else:
            print("⚠️  Service creation failed. Manual setup required.")
    except Exception as e:
        print(f"❌ Failed to create systemd service: {e}")

def setup_cron_jobs():
    """Setup cron jobs for automated scanning"""
    cron_content = """# DMLogn8n Security Scanner Automated Tasks
# Edit this file to customize scan schedules

# Daily vulnerability scan at 2 AM
0 2 * * * /home/activeloguser/DMLogn8n/security-env/bin/python /home/activeloguser/DMLogn8n/security/scanner/main.py --vulnerability-scan /home/activeloguser/DMLogn8n >> /home/activeloguser/DMLogn8n/security/logs/cron.log 2>&1

# Weekly dependency check on Sunday at 3 AM
0 3 * * 0 /home/activeloguser/DMLogn8n/security-env/bin/python /home/activeloguser/DMLogn8n/security/scanner/main.py --dependency-check /home/activeloguser/DMLogn8n >> /home/activeloguser/DMLogn8n/security/logs/cron.log 2>&1

# Monthly compliance assessment on 1st at 4 AM
0 4 1 * * /home/activeloguser/DMLogn8n/security-env/bin/python /home/activeloguser/DMLogn8n/security/scanner/main.py --compliance OWASP_TOP_10 >> /home/activeloguser/DMLogn8n/security/logs/cron.log 2>&1

# Cleanup old logs weekly (keep 30 days)
0 5 * * 0 find /home/activeloguser/DMLogn8n/security/logs -name "*.log" -mtime +30 -delete
"""

    try:
        with open('dmlogn8n-security.cron', 'w') as f:
            f.write(cron_content)

        print("Setting up cron jobs...")
        if run_command("crontab dmlogn8n-security.cron", "Installing cron jobs"):
            print("✅ Cron jobs installed successfully")
            print("To edit cron jobs: crontab -e")
            print("To view cron jobs: crontab -l")
        else:
            print("⚠️  Cron job installation failed. Manual setup required.")

        # Clean up temporary file
        os.remove('dmlogn8n-security.cron')
    except Exception as e:
        print(f"❌ Failed to setup cron jobs: {e}")

def create_desktop_shortcut():
    """Create desktop shortcut for easy access"""
    desktop_path = os.path.expanduser("~/Desktop")
    if os.path.exists(desktop_path):
        shortcut_content = """[Desktop Entry]
Version=1.0
Type=Application
Name=DMLogn8n Security Scanner
Comment=Advanced security vulnerability scanning system
Exec=python3 /home/activeloguser/DMLogn8n/security/scanner/main.py --full-assessment /home/activeloguser/DMLogn8n
Icon=security-high
Terminal=true
Categories=System;Security;
"""

        shortcut_file = os.path.join(desktop_path, "DMLogn8n-Security-Scanner.desktop")
        try:
            with open(shortcut_file, 'w') as f:
                f.write(shortcut_content)
            os.chmod(shortcut_file, 0o755)
            print(f"✅ Desktop shortcut created: {shortcut_file}")
        except Exception as e:
            print(f"⚠️  Could not create desktop shortcut: {e}")

def test_installation():
    """Test the installation"""
    print("Testing installation...")

    test_script = """
import sys
sys.path.insert(0, '/home/activeloguser/DMLogn8n/security/scanner')

try:
    from vulnerability_scanner import VulnerabilityScanner
    from dependency_checker import DependencyChecker
    from code_analyzer import CodeAnalyzer
    from network_scanner import NetworkScanner
    from patch_manager import PatchManager
    from security_monitor import SecurityMonitor
    from penetration_tester import PenetrationTester
    from compliance_checker import ComplianceChecker
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
"""

    with open('test_installation.py', 'w') as f:
        f.write(test_script)

    if run_command("python3 test_installation.py", "Testing module imports"):
        print("✅ Installation test passed")
    else:
        print("❌ Installation test failed")

    # Clean up test file
    if os.path.exists('test_installation.py'):
        os.remove('test_installation.py')

def main():
    """Main setup function"""
    print("🛡️  DMLogn8n Security Scanner System Setup")
    print("="*60)
    print("This script will install and configure the DMLogn8n Security Scanner System")
    print("="*60)

    # Check if running as root for system installations
    if os.geteuid() != 0:
        print("⚠️  Note: Some features require root privileges for system installation")
        print("   Consider running with 'sudo' for full functionality")

    try:
        # Check prerequisites
        print_step(1, "Checking prerequisites")
        if not check_python_version():
            return False

        # Install system dependencies
        print_step(2, "Installing system dependencies")
        if os.geteuid() == 0:
            install_system_dependencies()
        else:
            print("⚠️  Skipping system dependencies (requires root privileges)")

        # Create virtual environment
        print_step(3, "Setting up Python virtual environment")
        venv_path = create_virtual_environment()
        if not venv_path:
            return False

        # Install Python dependencies
        print_step(4, "Installing Python dependencies")
        if not install_dependencies():
            return False

        # Create directory structure
        print_step(5, "Creating directory structure")
        create_directories()

        # Create wordlists
        print_step(6, "Creating security wordlists")
        create_wordlists()

        # Setup database
        print_step(7, "Setting up databases")
        setup_database()

        # Create systemd service
        print_step(8, "Setting up system service")
        if os.geteuid() == 0:
            create_systemd_service()
        else:
            print("⚠️  Skipping systemd service (requires root privileges)")

        # Setup cron jobs
        print_step(9, "Setting up automated tasks")
        setup_cron_jobs()

        # Create desktop shortcut
        print_step(10, "Creating desktop shortcut")
        create_desktop_shortcut()

        # Test installation
        print_step(11, "Testing installation")
        test_installation()

        # Success message
        print("\n" + "="*60)
        print("🎉 DMLogn8n Security Scanner System Setup Complete!")
        print("="*60)
        print("\n📋 Quick Start:")
        print(f"1. Activate virtual environment: source {venv_path}/bin/activate")
        print("2. Run full assessment: python security/scanner/main.py --full-assessment /home/activeloguser/DMLogn8n")
        print("3. Start monitoring: python security/scanner/main.py --monitor")
        print("4. View reports: ls /home/activeloguser/DMLogn8n/security/reports/")
        print("\n📚 Documentation:")
        print("- README: /home/activeloguser/DMLogn8n/security/scanner/README.md")
        print("- Config: /home/activeloguser/DMLogn8n/security/config/security_config.json")
        print("- Logs: /home/activeloguser/DMLogn8n/security/logs/")
        print("\n⚙️  Configuration:")
        print("- Edit: /home/activeloguser/DMLogn8n/security/config/security_config.json")
        print("- Customize: scan schedules, notifications, and security policies")
        print("\n🚀 System Service:")
        print("- Start: sudo systemctl start dmlogn8n-security")
        print("- Enable: sudo systemctl enable dmlogn8n-security")
        print("- Status: sudo systemctl status dmlogn8n-security")
        print("\n" + "="*60)
        print("For help and support, check the README.md file or run:")
        print("python security/scanner/main.py --help")
        print("="*60)

        return True

    except KeyboardInterrupt:
        print("\n⚠️ Setup interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)