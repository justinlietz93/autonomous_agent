# LLM_kit

A toolkit for working with local LLM providers through Ollama.

## Command Line Usage

The main script (main_autonomous.py) accepts the following command line arguments:

### 1. List Available Providers
```bash
python main_autonomous.py --list-providers
# or
python main_autonomous.py -l
```
This will show all available LLM providers in your system.

### 2. List Available Prompts
```bash
python main_autonomous.py --list-prompts
```
Shows all available prompts in the system.

### 3. Specify a Provider
```bash
python main_autonomous.py --provider deepseek-14b_ollama
# or
python main_autonomous.py -p phi4_ollama
```

### 4. Specify a Prompt
```bash
python main_autonomous.py --prompt SELF_OPTIMIZATION
```
You can combine this with provider selection:
```bash
python main_autonomous.py --provider deepseek_ollama --prompt DEBUG
```

### 5. Create New Provider
```bash
python main_autonomous.py --new-provider qwen2.5-coder
```
Creates a new provider configuration for an Ollama model.

This requires that you have the Ollama model on your local system. 

Example:
```bash
ollama run deepseek-r1:32b
```

### 6. Single Response Mode
```bash
python main_autonomous.py --single
# or
python main_autonomous.py -s
```
Runs in single response mode instead of autonomous loop. Useful for quick tests or one-off queries.

You can combine this with other flags:
```bash
python main_autonomous.py --provider deepseek-r1_api --prompt DEBUG --single
```

### 7. Default Usage
```bash
python main_autonomous.py
```
This will use the default provider (deepseek_ollama) and default prompt (SELF_OPTIMIZATION)

## Examples

1. List all providers:
   ```bash
   python main_autonomous.py -l
   ```

2. Use the 14b model:
   ```bash
   python main_autonomous.py -p deepseek-14b_ollama
   ```

3. Use Phi-4:
   ```bash
   python main_autonomous.py -p phi4_ollama
   ```

4. Quick test with single response:
   ```bash
   python main_autonomous.py -p deepseek-r1_api --single
   ```

## Currently Available Providers
- `deepseek_ollama` (32b model)
- `deepseek-14b_ollama` (14b model)
- `phi4_ollama`
- `deepseek-r1_api` (API provider)

## Testing Prompts

You can test and view prompts using the test script:
```bash
# From tests/prompts directory:
python test_prompt.py --prompt SELF_OPTIMIZATION --with-context
```

Options:
- `--prompt NAME`: Specify which prompt to display
- `--with-context` or `-c`: Include actual context as seen by the LLM
- `--lines N`: Number of context lines to include (default: 300)
- `--list` or `-l`: List available prompts

## Requirements

- Python 3.8+
- Ollama installed and running
- Required models pulled in Ollama:
  - `deepseek-r1:32b`
  - `deepseek-r1:14b`
  - `phi4:latest`

> **Note**: Make sure Ollama is running before starting the script:
> ```bash
> ollama serve
> ```

## Development Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd LLM_kit
   ```

2. Run the setup script:
   ```bash
   ./setup_env.sh
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

To deactivate the virtual environment:
```bash
deactivate
```
