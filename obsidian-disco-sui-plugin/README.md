# DiscoSui Plugin for Obsidian

This plugin integrates DiscoSui's AI-powered note management capabilities with Obsidian.

## Features

- Process notes with DiscoSui's AI capabilities directly from Obsidian
- Access DiscoSui Assistant through a modal interface
- Context menu integration for quick note processing
- Real-time streaming responses from the AI
- Configurable API endpoint and settings

## Installation

### Manual Installation

1. Download the latest release from the releases page
2. Extract the plugin folder into your vault's plugins folder: `<vault>/.obsidian/plugins/`
3. Reload Obsidian
4. Enable the plugin in the Obsidian settings

### From Obsidian

1. Open Settings in Obsidian
2. Go to Community Plugins and disable Safe Mode
3. Click Browse and search for "DiscoSui"
4. Install the plugin
5. Enable the plugin in the list of installed plugins

## Configuration

1. Open Settings in Obsidian
2. Go to the DiscoSui settings tab
3. Configure the following settings:
   - API Endpoint: The URL where your DiscoSui server is running (default: http://localhost:3000)
   - Vault Path: The path to your Obsidian vault
   - HuggingFace Token (Optional): Your HuggingFace API token if required

## Usage

### Using the Command Palette

1. Open the command palette (Cmd/Ctrl + P)
2. Search for "DiscoSui"
3. Select "Process Current Note with DiscoSui"

### Using the Ribbon Icon

1. Click the brain icon in the left ribbon
2. Enter your request in the modal that appears
3. Click "Process" to send the request to DiscoSui

### Using the Context Menu

1. Right-click on a note in the file explorer
2. Select "Process with DiscoSui"

## Development

1. Clone this repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Build the plugin:
   ```bash
   npm run dev
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 