#!/bin/bash
# FRIDAY AI - BlackArch Linux Deployment Script
# Implements: AI Suggests → Human Approves → Tool Executes → AI Analyzes

set -e

echo "========================================="
echo "FRIDAY AI - BlackArch Deployment"
echo "========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on BlackArch
if [ ! -f /etc/os-release ]; then
    echo -e "${RED}Error: Cannot detect OS${NC}"
    exit 1
fi

# Install Python dependencies
echo -e "${GREEN}[1/5] Installing Python dependencies...${NC}"
sudo pacman -Sy --needed python python-pip python-virtualenv --noconfirm

# Create virtual environment
echo -e "${GREEN}[2/5] Creating virtual environment...${NC}"
cd python_backend
python -m venv venv
source venv/bin/activate

# Install requirements
echo -e "${GREEN}[3/5] Installing Python packages...${NC}"
pip install -r requirements.txt

# Additional pentesting integrations
pip install pymetasploit3 scapy python-nmap

# Verify BlackArch tools
echo -e "${GREEN}[4/5] Verifying BlackArch tools...${NC}"
REQUIRED_TOOLS=("nmap" "metasploit" "sqlmap" "nikto" "aircrack-ng")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v $tool &> /dev/null; then
        MISSING_TOOLS+=($tool)
    fi
done

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo -e "${YELLOW}Missing tools: ${MISSING_TOOLS[*]}${NC}"
    echo -e "${YELLOW}Install with: sudo pacman -S ${MISSING_TOOLS[*]}${NC}"
else
    echo -e "${GREEN}All core tools verified ✓${NC}"
fi

# Create configuration
echo -e "${GREEN}[5/5] Creating configuration...${NC}"
cat > config_blackarch.json << EOF
{
    "mode": "pentest",
    "approval_required": true,
    "log_all_commands": true,
    "tools_path": "/usr/bin",
    "reports_dir": "./pentest_reports"
}
EOF

mkdir -p pentest_reports

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "To start FRIDAY AI Pentest Mode:"
echo "  1. cd python_backend"
echo "  2. source venv/bin/activate"
echo "  3. python automation/pentest_cli.py"
echo ""
echo "Workflow: AI Suggests → You Approve → Tool Executes → AI Analyzes"
echo ""
