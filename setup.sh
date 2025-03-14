#!/bin/bash

# Function to check dependencies
check_dependencies() {
    echo "Checking dependencies..."
    
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
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 is not installed. Please install Python 3 first."
        exit 1
    fi
    
    echo "All dependencies are satisfied."
}

# Function to setup environment
setup_environment() {
    echo "Setting up environment..."
    
    # Create necessary directories
    mkdir -p notes uploads
    
    # Copy environment file if it doesn't exist
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "Please edit .env file with your settings (e.g., OPENAI_API_KEY)"
    fi
    
    # Load environment variables
    if [ -f .env ]; then
        export $(cat .env | xargs)
    fi
    
    # Set default vault path if not set
    if [ -z "$VAULT_PATH" ]; then
        export VAULT_PATH="./notes"
    fi
    
    echo "Environment setup complete."
}

# Function to setup plugin
setup_plugin() {
    echo "Setting up Obsidian plugin..."
    
    # Create plugin directory
    mkdir -p notes/.obsidian/plugins/discosui
    
    # Copy plugin files
    cp manifest.json notes/.obsidian/plugins/discosui/
    cp main.js notes/.obsidian/plugins/discosui/
    if [ -f styles.css ]; then
        cp styles.css notes/.obsidian/plugins/discosui/
    fi
    
    echo "Plugin files copied to notes/.obsidian/plugins/discosui/"
}

# Function to start services
start_services() {
    echo "Starting services..."
    
    # Build and start Docker services
    docker-compose up -d --build
    
    # Wait for services to start
    echo "Waiting for services to start..."
    sleep 5
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        echo "Services are running successfully!"
        echo "API is available at http://localhost:5000"
    else
        echo "Error: Services failed to start. Check logs with: docker-compose logs"
        exit 1
    fi
}

# Function to setup development environment
setup_dev() {
    echo "Setting up development environment..."
    
    # Create Python virtual environment
    python3 -m venv .venv
    source .venv/bin/activate
    
    # Install dependencies
    pip install -e .
    pip install -r requirements.txt
    
    # Install frontend dependencies
    npm install
    
    echo "Development environment setup complete."
}

# Function to display help
show_help() {
    echo "Usage: ./setup.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Full setup (default)"
    echo "  dev       - Setup development environment"
    echo "  start     - Start services"
    echo "  stop      - Stop services"
    echo "  restart   - Restart services"
    echo "  logs      - View service logs"
    echo "  help      - Show this help message"
}

# Main script execution
case "$1" in
    "dev")
        check_dependencies
        setup_environment
        setup_dev
        ;;
    "start")
        start_services
        ;;
    "stop")
        docker-compose down
        ;;
    "restart")
        docker-compose restart
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "help")
        show_help
        ;;
    *)
        check_dependencies
        setup_environment
        setup_plugin
        start_services
        echo ""
        echo "Next steps:"
        echo "1. Configure the plugin in Obsidian:"
        echo "   - Open Obsidian Settings"
        echo "   - Go to Community Plugins"
        echo "   - Enable DiscoSui"
        echo "   - Configure API URL as http://localhost:5000"
        echo ""
        echo "2. View logs with: ./setup.sh logs"
        ;;
esac 