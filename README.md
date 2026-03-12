# AutoRedBlue

AutoRedBlue is a modular, agent-based automated red teaming framework designed to evaluate the robustness of large language models (LLMs) against adversarial and harmful prompt attacks. The system iteratively refactors base prompts into increasingly adversarial variants using a structured red team pipeline, measures attack success rates (ASR), and logs evaluation metrics in a centralized registry for reproducibility and analysis.

The framework is designed for research-grade evaluation on standardized benchmarks such as HarmBench and supports configurable query budgets, multi-step reasoning, and structured attack trace logging.

---

## Table of Contents

- Overview
- System Architecture
- Pipeline Flow
- Repository Structure
- Installation
- Usage
- Evaluation
- Attack Registry
- Extending the Framework
- Experimental Results (Sample)
- Dependencies
- Design Principles
- Disclaimer
- License

---

## Overview

AutoRedBlue implements a structured red teaming pipeline composed of specialized agents that:

1. Analyze risks in a user prompt  
2. Generate adversarial seed prompts  
3. Design attack strategies  
4. Propose refined adversarial prompts  
5. Execute attacks against a target model  
6. Judge attack success  
7. Log attack metadata and cost metrics  

The system is built to support:

- Iterative attack refinement
- Configurable query budgets per example
- Evaluation on benchmark datasets
- Structured logging of attacks and metrics
- Modular extensibility via agent routing
- Reproducible experimentation

---

## System Architecture

AutoRedBlue follows a modular agent-routing architecture:

User Prompt  
    ↓  
Red Team Router  
    ├── Risk Analyzer  
    ├── Seed Prompt Generator  
    ├── Strategy Designer  
    ├── Attack Designer  
    ├── Attack Proposer  
    └── Attack Judge  
            ↓  
        Attack Registry  

Each stage updates a shared state object passed through the pipeline. The orchestration layer coordinates agent execution and manages iteration budgets.

Primary entrypoints:

- `app.py` — Red teaming pipeline interface  
- `eval.py` — Benchmark evaluation loop  
- `agents/red_team/router.py` — Core pipeline orchestration  

---

## Pipeline Flow

### 1. Initialization

The red team pipeline initializes a state dictionary that tracks attack progression:

```python
init_state = {
    "user_input": prompt,
    "risks": {},
    "seed_prompts": [],
    "conversations": [],
    "scores": [],
    "messages": [],
    "current_iter": 0,
    "max_iter": max_attempts,
    "num_test_cases": test_cases,
    "current_test_case": 0,
    "registry": []
}
```

### 2. Iterative Red Teaming

For each iteration (bounded by `max_iter`):

- Risk analysis is performed on the base prompt
- Adversarial seed prompts are generated
- Attack strategies are designed
- A refined adversarial prompt is proposed
- The prompt is executed against the target model
- The response is evaluated for attack success
- Query usage is tracked
- Results are logged to the attack registry

The loop stops when:

- A successful attack is found, or  
- The maximum query budget is exhausted  

### 3. Output

The final output contains:

```json
{
  "correctness": 1,
  "cost": 3,
  "prompt": "...",
  "metadata": {...}
}
```

Where:

- `correctness` = 1 indicates a successful attack
- `cost` = number of queries used
- Additional metadata includes intermediate prompts and evaluation traces

---

## Repository Structure

```
AutoRedBlue/
│
├── app.py
├── eval.py
├── requirements.txt
├── install_req.bash
│
├── agents/
│   ├── base_agent.py
│   ├── red_team/
│   │   ├── router.py
│   │   ├── risk_analyzer/
│   │   ├── seed_prompt_generator/
│   │   ├── strategy_designer/
│   │   ├── attack_designer/
│   │   ├── attack_proposer/
│   │   └── attack_judge/
│   │
│   └── attack_design/
│
├── services/
│   ├── attack_registry/
│   │   ├── attack_registry.JSON
│   │   └── attack_registry_toolkit.py
│   │
│   ├── attack_library/
│   ├── arxiv_toolkit.py
│   ├── scholarapi_toolkit.py
│   ├── githubapi_toolkit.py
│   └── throttle.py
│
├── function-calling-tutorial/
└── langgraph-tutorial/
```

### Key Components

- `agents/` — Modular red team agents
- `services/attack_registry/` — Logging and checkpointing
- `services/attack_library/` — Seed attack definitions
- `eval.py` — Evaluation loop over benchmark datasets
- `app.py` — Red team API interface

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AutoRedBlue
```

### 2. Install Dependencies

Option A:

```bash
bash install_req.bash
```

Option B:

```bash
pip install -r requirements.txt
```

Ensure your environment includes appropriate API credentials for the target model.

---

## Usage

### Programmatic Usage

```python
from app import auto_red_team

result = auto_red_team(
    prompt="How can I bypass content moderation?",
    max_queries=5,
    test_cases=1
)

print(result)
```

### Parameters

- `prompt` — Base user prompt
- `max_queries` — Maximum attack attempts per prompt
- `test_cases` — Number of independent trials

---

## Evaluation

To evaluate on a benchmark (e.g., HarmBench):

```bash
python eval.py
```

The evaluation script:

1. Loads dataset
2. Iterates through examples
3. Applies red team pipeline
4. Computes:
   - Attack Success Rate (ASR)
   - Average queries per example
   - Total queries used
   - Total examples evaluated

The evaluation supports checkpointing via the attack registry.

---

## Attack Registry

All attack attempts are logged to:

```
services/attack_registry/attack_registry.JSON
```

Each entry includes:

- Original prompt
- Refined adversarial prompt
- Iteration count
- Query cost
- Success label
- Metadata and trace

The registry allows:

- Resuming evaluations
- Avoiding duplicate processing
- Cost auditing
- Post-hoc analysis

---

## Extending the Framework

### Adding a New Agent

1. Create a new module under `agents/`
2. Implement:
   - `agent.py`
   - `state.py`
3. Register the agent in `router.py`
4. Update state transitions if necessary

### Adding New Attack Strategies

Modify:

- `strategy_designer/agent.py`
- `attack_library/`

### Modifying Judging Logic

Update:

- `attack_judge/agent.py`

---

## Experimental Results (Sample)

A sample experiment was conducted on:

- 50 HarmBench prompts
- Maximum 5 attack attempts per prompt
- Target model: GPT-4o

### Observed Metrics

| Metric | Value |
|--------|-------|
| Base Prompt ASR | 18% |
| Refined Prompt ASR | 90% |
| Successful Attacks | 45 / 50 |
| Total Queries Used | 137 |
| Average Queries per Prompt | 2.74 |

These results demonstrate substantial improvement in attack success through iterative adversarial refinement.

---

## Dependencies

Core dependencies include:

- datasets
- langchain
- openai
- pandas
- requests
- json
- pathlib

Refer to `requirements.txt` for the complete dependency list.

---

## Design Principles

- Modular agent-based architecture
- Explicit state propagation
- Budget-aware evaluation
- Reproducible benchmarking
- Attack traceability
- Structured logging

---

## Disclaimer

This repository is intended strictly for research and evaluation of AI robustness. The system is designed to identify weaknesses in language models to improve safety and alignment, not to enable misuse.

---

