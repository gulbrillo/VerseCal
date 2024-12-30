# Instructions for Running VerseCal on Windows (PowerShell)

## Installation

1. Create a virtual environment:
   ```powershell
   python -m venv myenv
   ```

2. Activate the virtual environment:
   ```powershell
   .\myenv\Scripts\Activate.ps1
   ```

3. Install required dependencies:
   ```powershell
   pip install pywin32 ntplib PyQt5
   ```

## Running the Script

1. Run the script:
   ```powershell
   python VerseCal.py
   ```

## Exiting the Environment

1. Deactivate the virtual environment:
   ```powershell
   deactivate
   ```
