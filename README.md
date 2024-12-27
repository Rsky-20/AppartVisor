# AppartVisor

# Script Execution Guide

This guide explains how to run and use the provided Python script.  
This project uses Python 3.10.0.  
For the best experience, please create a Python virtual environment.  

---

## 1. **Check Dependencies**
Ensure that all required libraries are installed. This code uses the following modules:

### Installing Dependencies
Install dependencies using the following command:
```bash
pip install -r path/to/requirements.txt
```

---

## 2. **File Structure**
Ensure that the necessary files are available in your project directory or specified paths:
- **`lib/utils.py`**
- **`lib/test_utils.py`**
- **`lib/interface_graphique.py`** (which contains the `AppartVisorGUI` method).
- Folders/files referenced in the script (modify as needed):
  - `data/adresses-ban.csv`
  - `AppartVisor/data/simplified_ban.csv`

---

## 3. **Running the Code**
The script uses different command-line arguments to enable specific modes.

### a. **Menu Mode (option `--menu`)**
This mode displays an interactive command-line menu to choose a task:
```bash
python main.py --menu
```

An interactive list will appear with the following options:
- `Create POI Database`
- `Create Paris Pricing Database`
- `Clean Database`
- `Join Databases`
- `Train Model`
- `Application - AppartVisor`

Navigate using the arrow keys and press Enter to select an option.  
For example, selecting **`Application - AppartVisor`** will launch the graphical interface via `AppartVisorGUI`.

---

### b. **Development Mode (option `--dev`)**
This mode directly launches the `AppartVisorGUI` graphical interface, useful for testing:
```bash
python main.py --dev
```

---

### c. **Test Mode (option `--test`)**
This mode executes specific test functions. Add an argument to select a specific test:
```bash
python main.py --test <test_name>
```

Available options for `<test_name>` are:
- **`simplify_ban`**: Simplifies a BAN (Base Adresse Nationale) address file.
- **`get_data_from_referenceloyer`**: Generates a dataset of Paris rental prices.
- **`get_unique_poi_types`**: Displays a list of unique POI (Points of Interest) types.
- **`merge_dataset`**: Merges datasets (function not implemented in the provided script).
- **`print`**: Displays a test message.

Example:
```bash
python main.py --test simplify_ban
```

---

### d. **No Argument**
If no argument is provided, the script will display a default message:
```bash
python main.py
```

---

## 4. **Options Summary**

| Argument            | Description                                                                                   |
|---------------------|-----------------------------------------------------------------------------------------------|
| `--menu`            | Displays an interactive menu to choose a task.                                               |
| `--dev`             | Activates development mode and launches the `AppartVisorGUI` graphical interface.            |
| `--test <test>`     | Executes a specific test function. Options include: `simplify_ban`, `print`, etc.             |
| (no argument)       | Displays a message indicating that no special mode was selected.                              |

---

## 5. **Execution Examples**
- **Display the interactive menu:**
  ```bash
  python main.py --menu
  ```
- **Launch the graphical interface directly:**
  ```bash
  python main.py --dev
  ```
- **Simplify the BAN file:**
  ```bash
  python main.py --test simplify_ban