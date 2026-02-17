#!/bin/bash
#
# startTwistedDebate_v4.sh - Launch TwistedDebate V4 server
#
# This script starts the TwistedDebate V4 FastAPI server.
# Make sure Ollama is running before starting this server.
#

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}TwistedDebate V4 - Startup Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if Ollama is running
echo -e "\n${YELLOW}Checking Ollama service...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${RED}✗ Ollama is not running${NC}"
    echo -e "${YELLOW}Please start Ollama first:${NC}"
    echo -e "  ollama serve"
    exit 1
fi

# Change to v4 directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "\n${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install/update dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
fi

# Start the server
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Starting TwistedDebate V4 Server${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Web UI will be available at:${NC}"
echo -e "  http://localhost:8004"
echo -e "${YELLOW}API documentation at:${NC}"
echo -e "  http://localhost:8004/docs"
echo -e "\n${YELLOW}Press Ctrl+C to stop the server${NC}\n"

# Run the server using uvicorn
cd "$SCRIPT_DIR"
uvicorn app.server:app --host 0.0.0.0 --port 8004 --reload

# Deactivate virtual environment on exit
deactivate
