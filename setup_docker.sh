#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "Setting up LLM Kit Docker environment..."

# Check for required files
echo "Checking required files..."

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${RED}Missing .env file. Creating template...${NC}"
    cat > .env << EOL
# Environment Variables
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
OLLAMA_HOST=http://localhost:11434
EOL
    echo -e "${GREEN}Created .env template. Please edit with your API keys.${NC}"
fi

# Create necessary directories
echo "Creating directory structure..."
mkdir -p memory/context_logs

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Build the Docker image
echo "Building Docker image..."
docker build -t llm_kit .

echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "To run the system:"
echo "1. Make sure you've added your API keys to .env"
echo "2. Start Ollama server if using local models"
echo "3. Run: docker run --env-file .env -it llm_kit"
echo ""
echo "For development:"
echo "- Source code is in /app inside the container"
echo "- Logs will be in memory/context_logs"
echo "- Use 'docker exec -it <container_id> bash' to access the container" 