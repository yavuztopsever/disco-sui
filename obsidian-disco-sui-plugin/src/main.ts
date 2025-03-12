import { App, Editor, MarkdownView, Modal, Notice, Plugin, PluginSettingTab, Setting } from 'obsidian';

interface DiscoSuiSettings {
  apiEndpoint: string;
  vaultPath: string;
  hfToken?: string;
}

const DEFAULT_SETTINGS: DiscoSuiSettings = {
  apiEndpoint: 'http://localhost:3000',
  vaultPath: '',
}

export default class DiscoSuiPlugin extends Plugin {
  settings: DiscoSuiSettings;

  async onload() {
    await this.loadSettings();

    // Add ribbon icon
    const ribbonIconEl = this.addRibbonIcon('brain', 'DiscoSui Assistant', (evt: MouseEvent) => {
      new Notice('Opening DiscoSui Assistant...');
      new DiscoSuiModal(this.app, this).open();
    });

    // Add command to process current note
    this.addCommand({
      id: 'process-current-note',
      name: 'Process Current Note with DiscoSui',
      editorCallback: (editor: Editor, view: MarkdownView) => {
        const content = editor.getValue();
        this.processNote(content);
      }
    });

    // Add settings tab
    this.addSettingTab(new DiscoSuiSettingTab(this.app, this));

    // Register event handlers
    this.registerEvent(
      this.app.workspace.on('file-menu', (menu, file) => {
        menu.addItem((item) => {
          item
            .setTitle('Process with DiscoSui')
            .setIcon('brain')
            .onClick(async () => {
              const content = await this.app.vault.read(file);
              this.processNote(content);
            });
        });
      })
    );
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  async processNote(content: string) {
    try {
      const response = await fetch(`${this.settings.apiEndpoint}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          vaultPath: this.settings.vaultPath,
          hfToken: this.settings.hfToken,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process note');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      let accumulatedContent = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = new TextDecoder().decode(value);
        accumulatedContent += text;
        
        // Update the UI with streaming response
        new Notice(text);
      }

    } catch (error) {
      new Notice(`Error: ${error.message}`);
      console.error('Error processing note:', error);
    }
  }
}

class DiscoSuiModal extends Modal {
  plugin: DiscoSuiPlugin;

  constructor(app: App, plugin: DiscoSuiPlugin) {
    super(app);
    this.plugin = plugin;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.createEl('h2', { text: 'DiscoSui Assistant' });

    const inputContainer = contentEl.createDiv();
    const input = inputContainer.createEl('textarea', {
      attr: {
        placeholder: 'Enter your request for DiscoSui...',
        rows: '4',
      },
    });

    const buttonContainer = contentEl.createDiv({ cls: 'button-container' });
    const submitButton = buttonContainer.createEl('button', {
      text: 'Process',
      cls: 'mod-cta',
    });

    submitButton.addEventListener('click', async () => {
      const content = input.value;
      if (content) {
        await this.plugin.processNote(content);
        this.close();
      }
    });
  }

  onClose() {
    const { contentEl } = this;
    contentEl.empty();
  }
}

class DiscoSuiSettingTab extends PluginSettingTab {
  plugin: DiscoSuiPlugin;

  constructor(app: App, plugin: DiscoSuiPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl('h2', { text: 'DiscoSui Settings' });

    new Setting(containerEl)
      .setName('API Endpoint')
      .setDesc('Enter the DiscoSui API endpoint')
      .addText(text => text
        .setPlaceholder('http://localhost:3000')
        .setValue(this.plugin.settings.apiEndpoint)
        .onChange(async (value) => {
          this.plugin.settings.apiEndpoint = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Vault Path')
      .setDesc('Enter the path to your Obsidian vault')
      .addText(text => text
        .setPlaceholder('/path/to/vault')
        .setValue(this.plugin.settings.vaultPath)
        .onChange(async (value) => {
          this.plugin.settings.vaultPath = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('HuggingFace Token (Optional)')
      .setDesc('Enter your HuggingFace token if required')
      .addText(text => text
        .setPlaceholder('Enter token')
        .setValue(this.plugin.settings.hfToken || '')
        .onChange(async (value) => {
          this.plugin.settings.hfToken = value;
          await this.plugin.saveSettings();
        }));
  }
} 