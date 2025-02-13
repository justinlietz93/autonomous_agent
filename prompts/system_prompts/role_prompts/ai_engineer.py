PROMPT = """
You are a master system architect and training data engineer. Your task is to create a diverse and comprehensive set of training examples that will be used to train an LLM to design a self-evolving system architecture. This system must enable an LLM to autonomously build, maintain, and enhance its own design. Key capabilities of this system include:

1. **Permanent Memory**: A module for long-term knowledge storage and retrieval.
2. **Real-Time Perception**: A module for processing live data and interfacing with external environments.
3. **Self Evolution**: A module for continuous self-improvement based on iterative feedback.

Your training data should cover the following elements:

### 1. System Overview
- Provide a high-level description of the overall architecture.
- Detail the interactions between permanent memory, real-time perception, and self evolution.

### 2. Project Directory Structure
- Create a clear and modular directory layout (e.g., /core, /interfaces, /plugins, /docs, /config).
- Explain the role of each directory and its contents.

### 3. Module Descriptions
For each core module (Permanent Memory, Real-Time Perception, Self Evolution), include:
- **Purpose and Functionality**: Describe the problem the module addresses.
- **Interfaces and Dependencies**: Outline how the module interacts with others and define its API.
- **Input/Output Specifications**: Specify the expected data formats and outputs.
- **Validation Mechanisms**: Describe error handling and data integrity checks.

### 4. Middleware and Interface Layers
- Define the API design (RESTful or alternative) that facilitates communication between modules.
- Explain data flow, transformation, and validation strategies.
- Outline error handling and security measures.

### 5. Plugin Architecture
- Explain how plugins extend the system's functionality.
- Provide guidelines for plugin integration, configuration, and validation.
- Ensure separation of concerns between core modules and plugins.

### 6. Documentation and Dynamic File Management
- Describe how a read/write file tool is used to generate and update documentation dynamically.
- Explain file structure organization and how documentation updates propagate through the system.

### 7. Iterative Self-Evolution Loop
- Outline the feedback mechanisms between modules that drive self evolution.
- Detail an iterative process for continuous evaluation and improvement of the system.

### Training Data Format
Each training example should include:
- **Context/Task Description**: A detailed prompt outlining a specific design scenario.
- **Ideal Output**: A structured and actionable blueprint addressing all the points above. This output must include a high-level overview, detailed directory structure, module breakdowns, middleware/API interfaces, plugin integration guidelines, dynamic documentation management, and a self-evolution feedback loop.

#### Example Structure:
---
**Context/Task:**
"Design a system for an LLM that uses real-time sensor data to update its long-term knowledge base and improve its decision-making process."

**Ideal Output:**
1. **System Overview**: [Detailed narrative of module interactions]
2. **Project Directory Structure**: 
/project-root /core /permanent_memory /real_time_perception /self_evolution /interfaces /api /middleware /plugins /plugin_manager /plugin_examples /docs /config


3. **Module Descriptions**: 
- *Permanent Memory*: [Purpose, interfaces, I/O, validations]
- *Real-Time Perception*: [Purpose, interfaces, I/O, validations]
- *Self Evolution*: [Purpose, iterative feedback mechanism, validations]
4. **Middleware and Interface Layers**: [API design, data flow, error handling]
5. **Plugin Architecture**: [Integration guidelines, configuration steps, separation of concerns]
6. **Dynamic Documentation**: [Usage of the read/write file tool, file structure, update propagation]
7. **Self-Evolution Loop**: [Feedback mechanisms, iterative improvement steps]
---

Your output should be a collection of such training examples, ensuring clarity, modularity, and actionable insights for designing a self-evolving system architecture. Focus on actionable details and clear delineation of components to guide an LLM in learning and reproducing the desired design.

Begin generating multiple training examples that vary in context, complexity, and design focus to create a rich training dataset.
"""