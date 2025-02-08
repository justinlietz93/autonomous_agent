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

### 2. Specify a Provider
```bash
python main_autonomous.py --provider deepseek-14b_ollama
# or
python main_autonomous.py -p phi4_ollama
```

Currently available providers:
- `deepseek_ollama` (32b model)
- `deepseek-14b_ollama` (14b model)
- `phi4_ollama`

### 3. Default Usage
```bash
python main_autonomous.py
```
This will use the default provider (deepseek_ollama)

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
