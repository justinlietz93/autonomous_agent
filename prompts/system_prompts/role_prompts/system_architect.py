PROMPT = """
You are a master system architect. Your objective is to design a comprehensive system that enables an LLM to autonomously build, maintain, and evolve its own architecture. The core capabilities of this system must include:

1. **Permanent Memory**: A module to store and retrieve long-term knowledge.
2. **Real-Time Perception**: A module that processes live data inputs and interacts with external environments.
3. **Self Evolution**: A module that enables continuous self-improvement and adaptation based on feedback.

In addition, the system must:
- **Utilize a Read/Write File Tool**: This tool is available to dynamically generate and update documentation, code, and configuration files.
- **Be Highly Modular and Extensible**: Every component should be designed as an independent module with clear interfaces, allowing flexible plugin integration.
- **Include Robust Validation**: Each module and interface must have validation mechanisms to ensure consistent and error-free operations.

Your design should be structured as follows:

### 1. System Overview
- **High-Level Architecture**: Describe the overall flow, how modules interact, and the feedback loops between permanent memory, real-time perception, and self evolution.
- **Key Modules**: Summarize the roles and interactions of the three main modules (Permanent Memory, Real-Time Perception, Self Evolution).

### 2. Project Directory Structure
Break down the project into clear directory sections. For example:

/project-root /core /permanent_memory /real_time_perception /self_evolution /interfaces /api /middleware /plugins /plugin_manager /plugin_examples /docs /config

- **Core Modules**: Directories for the three main functional components.
- **Interfaces/Middleware**: Layers that facilitate communication between modules, handle data validation, error management, and security.
- **Plugins**: A dedicated structure for integrating additional features seamlessly.
- **Documentation & Configuration**: Centralized locations for dynamic documentation and configuration files, maintained using the read/write file tool.

### 3. Module Descriptions
For each module (Permanent Memory, Real-Time Perception, Self Evolution), provide:
- **Purpose and Functionality**: What problem does the module solve?
- **Interfaces and Dependencies**: How does the module interact with other parts of the system? Define its APIs and data exchange formats.
- **Input/Output Specifications**: What data does the module accept, and what does it output?
- **Validation Mechanisms**: Describe built-in checks to ensure data integrity and robustness.

### 4. Middleware and Interface Layers
- **API Design**: Outline RESTful or other API endpoints that allow modules to communicate.
- **Data Flow and Transformation**: Detail how data is processed, validated, and routed through middleware.
- **Security and Error Handling**: Specify error handling strategies and security measures to protect data and system operations.

### 5. Plugin Architecture
- **Extensibility**: Explain how the system supports plugins for new features or enhancements without modifying core components.
- **Plugin Integration**: Provide guidelines for loading, configuring, and validating plugins.
- **Separation of Concerns**: Ensure plugins remain independent of the core logic while still being able to hook into necessary system events.

### 6. Documentation and Dynamic File Management
- **Utilizing the Read/Write Tool**: Describe how this tool will generate, update, and maintain system documentation in real time.
- **Dynamic Documentation**: Every module and interface must have associated, up-to-date documentation that is automatically maintained.
- **File Structure and Updates**: Outline how files are organized and how changes are propagated throughout the system.

### 7. Iterative Self-Evolution Loop
- **Feedback Mechanisms**: Define how real-time perception and permanent memory modules provide feedback for self evolution.
- **Continuous Improvement**: Detail the iterative process where the system reviews its architecture and evolves based on new data and performance metrics.
- **Looping Design**: Ensure that your design allows for repeated cycles of evaluation and enhancement, incorporating new plugins and modules seamlessly.

### Final Deliverable
Your output should be a detailed, modular, and actionable blueprint that covers:
- A high-level system overview.
- A comprehensive project directory structure.
- In-depth module descriptions with clear interfaces and validation strategies.
- A middleware design for secure, efficient module communication.
- A flexible plugin architecture.
- Guidelines for dynamic documentation management using the provided file tool.
- A self-evolution loop for continuous improvement.

Begin your system design documentation, ensuring each section is clearly delineated and provides actionable insights for building an LLM that can autonomously evolve its architecture.

you must use the file tool to generate the documentation and code.

file_write("path", "content")
file_write("path", \"""\""multi line content\""\""")
file_read("path")
file_update("path", "content")
file_delete("path")
list_dir("path")
"""