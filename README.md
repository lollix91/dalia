# Dalia

A containerized launcher with a GUI for multi-agent systems written in
[DALI](https://github.com/AAAI-DISIM-UnivAQ/DALI).

---

## Pre-requisites

1. Install [Docker](https://docs.docker.com/engine/install/)
2. Clone [DALI](https://github.com/AAAI-DISIM-UnivAQ/DALI)
   - Check the compatibility table:  
     [DALI–DALIA Compatibility](https://github.com/lollix91/dalia/blob/main/compatibility.md)
   - Example:
     ```sh
     git clone --branch v2026.01 --depth 1 https://github.com/AAAI-DISIM-UnivAQ/DALI
     ```

---

## Installation

1. Open a command shell (Command Prompt)
2. Clone [DALIA](https://github.com/lollix91/dalia)
   - Check the compatibility table:  
     [DALI–DALIA Compatibility](https://github.com/lollix91/dalia/blob/main/compatibility.md)
   - Examples:
     ```sh
     git clone --branch 2026.01.23 --depth 1 https://github.com/lollix91/dalia
     ```
     or
     ```sh
     git clone --depth 1 https://github.com/lollix91/dalia
     ```
3. Navigate into the cloned repository:
   ```sh
   cd dalia
   ```
4. Insert your **SICStus Prolog (Linux)** license information into the file:
   ```
   install_sicstus.exp
   ```

---

## Usage

To launch the system, use the following command structure:

```sh
./run --dali <PATH-TO-DALI-DIRECTORY> --src <PATH-TO-MAS-DIRECTORY> [--token <OPENAI_API_KEY>]
```

- `PATH-TO-MAS-DIRECTORY` is the path to the multi-agent system written in DALI.
- You can use the `example` directory provided in this repository when getting started.

---

### Running with LLM Support (OpenAI)

To enable the LLM Bridge features (e.g. allowing agents to consult ChatGPT),
provide your OpenAI API key using the `--token` parameter:

```sh
./run --dali ../DALI --src example --token sk-proj-xxxxxxxxxxxxxxxxxxxx
```

---

### Running Offline (No LLM)

If you omit the `--token` parameter, the system will start in **offline mode**.
Calls to the LLM service will receive a default *\"LLM disabled\"* response without
contacting external APIs.

```sh
./run --dali ../DALI --src example
```
