#!/bin/bash

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
mkdir -p notes uploads

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please edit .env file with your settings (e.g., OPENAI_API_KEY)"
fi

# Build and start services
docker-compose up -d --build

# Wait for services to start
echo "Waiting for services to start..."
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "Services are running successfully!"
    echo "API is available at http://localhost:5000"
    echo ""
    echo "Next steps:"
    echo "1. Copy the plugin to your Obsidian vault:"
    echo "   cp -r dist/ \$OBSIDIAN_VAULT/.obsidian/plugins/disco-sui/"
    echo ""
    echo "2. Configure the plugin in Obsidian:"
    echo "   - Open Obsidian Settings"
    echo "   - Go to Community Plugins"
    echo "   - Enable DiscoSui"
    echo "   - Configure API URL as http://localhost:5000"
    echo ""
    echo "3. View logs with:"
    echo "   docker-compose logs -f"
else
    echo "Error: Services failed to start. Check logs with:"
    echo "docker-compose logs"
    exit 1
fi

# Create plugin directory if it doesn't exist
mkdir -p notes/.obsidian/plugins/discosui

# Copy manifest.json
cp manifest.json notes/.obsidian/plugins/discosui/

# Copy main.js
cp main.js notes/.obsidian/plugins/discosui/

# Copy styles.css if it exists
if [ -f styles.css ]; then
    cp styles.css notes/.obsidian/plugins/discosui/
fi

echo "Plugin files copied to notes/.obsidian/plugins/discosui/" 