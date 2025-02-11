#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "Setting up LLM Sandbox Docker environment for your PROJECT root..."

###############################################################################
# 1. Create a .env file if it doesn't exist (optional)
###############################################################################
if [ ! -f .env ]; then
    echo -e "${RED}Missing .env file. Creating template...${NC}"
    cat > .env << EOL
# Environment Variables
OPENAI_API_KEY=your_key_here
OLLAMA_HOST=http://localhost:11434
EOL
    echo -e "${GREEN}Created .env template. Please edit with your API keys.${NC}"
fi

###############################################################################
# 2. Check if Docker is installed
###############################################################################
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

###############################################################################
# 3. Archive your PROJECT root (the current directory)
###############################################################################
# We'll call the archive "project.tar" and exclude itself and known ephemeral items.
# If you have large directories you want to skip, add more --exclude lines.

echo ""
echo "Archiving project root into project.tar..."
tar -cf project.tar \
    --exclude=project.tar \
    --exclude=.git \
    --exclude=node_modules \
    .

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create project.tar. Check permissions and excludes.${NC}"
    exit 1
fi

echo -e "${GREEN}project.tar archive created successfully.${NC}"

###############################################################################
# 4. Build the Docker image
###############################################################################
echo ""
echo "Building Docker image from Dockerfile..."
docker build -t llm_kit .

if [ $? -ne 0 ]; then
    echo -e "${RED}Docker build failed. Please check the Dockerfile and context.${NC}"
    exit 1
fi

echo -e "${GREEN}Docker image built successfully!${NC}"

###############################################################################
# 5. Run a container from the new image
###############################################################################
echo ""
echo "Starting Docker container in detached mode..."
CONTAINER_ID=$(docker run -d --env-file .env -it llm_kit tail -f /dev/null)

if [ -z "$CONTAINER_ID" ]; then
    echo -e "${RED}Failed to start Docker container!${NC}"
    exit 1
fi

echo -e "${GREEN}Container started with ID: ${CONTAINER_ID}${NC}"
echo ""
echo "----------------------------------------------------------------------------"
echo "Inside the container, your project root is located at /fake_root."
echo "You can delete or modify files there without affecting your real host."
echo "----------------------------------------------------------------------------"
echo ""
echo "To attach and work inside the container, run:"
echo "  docker exec -it $CONTAINER_ID bash"
echo ""
echo "Stop the container by running: docker stop $CONTAINER_ID"
echo "Remove it with:               docker rm $CONTAINER_ID"
echo ""
echo -e "${GREEN}Setup complete!${NC}"
