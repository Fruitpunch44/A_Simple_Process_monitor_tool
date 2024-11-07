
# Simple Process Monitor Tool

## Overview

The **Simple Process Monitor Tool** is a Python-based utility that enables users to monitor system processes in real-time. With this tool, you can list running processes, monitor specific processes, and retrieve detailed process information. It is designed to be lightweight, easy to use, and extendable for various use cases, making it a helpful tool for anyone looking to manage and analyze system processes.

This tool uses the `psutil` library for interacting with system processes, providing essential functionality for process management.

## Features

- **List Active Processes**: Display all the processes currently running on your machine.
- **Monitor Processes**: Track specific processes and receive real-time information about their status.
- **Process Information**: Retrieve detailed details about any active process, including PID, memory usage, and CPU usage.
- **Real Time CPU/Memory usage graphs**:Provide a functional graph to view CPU an Memory usage in real time
  
## Installation

### Prerequisites

To use the **Simple Process Monitor Tool**, you need to have Python 3.x installed. Additionally, the tool requires the `psutil` library for accessing and managing system processes.

You can install the required dependencies by running:

```bash
pip install psutil
```

### Cloning the Repository

1. Clone the repository to your local machine using the following command:

   ```bash
   git clone https://github.com/Fruitpunch44/A_Simple_Process_monitor_tool.git
   ```

2. Navigate into the cloned directory:

   ```bash
   cd A_Simple_Process_monitor_tool
   ```

3. Optionally, create a virtual environment to isolate your dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

4. Install additional dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### Setting Up

After ensuring the prerequisites are installed, the tool is ready to use. There's no additional setup required.

## Usage

### Starting the Tool

To start the tool, simply run the `Process.py` script:

```bash
python Process.py
```

The script will provide a menu that has options the user can pick from ranging from listing all processes,terminating process etc.


### Bug Reports and Feature Requests

Please report any bugs or feature requests by opening an issue in the **Issues** section of the repository. .

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


