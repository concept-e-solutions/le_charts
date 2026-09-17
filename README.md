# chart tool – Setup Guide

 
✅ **0. Requirements**
- Install Python 3.x
- Install Git
- Install Visual Studio Code (VS Code)

---

✅ **1. Create Repository**

- open the chart tools home page in GitHub.
- **Click “Use this template”**.
- Enter a new name and select the visibility and owner.
- Click “Create repository”
---

✅ **2. Clone the Repository (GitHub via HTTPS)**
- Open VS Code.
- Open the terminal in VS Code (Ctrl + ö or Ctrl + ~).
- Navigate to the folder where you want the project to be located:
  ```bash
  cd C:\Users\YOURNAME\Documents
  ```
- Clone the repository:
  ```bash
  git clone https://github.com/YOURUSER/REPO_NAME.git
  ```
- Open the project folder in VS Code:
  ```bash
  cd REPO_NAME
  ```

---

✅ **3. Create a Virtual Environment**
- Create a venv:
  ```bash
  python -m venv venv
  ```
- Activate the venv:
  - **Windows:**
    ```bash
    .\venv\Scripts\activate
    ```
  - **macOS/Linux:**
    ```bash
    source venv/bin/activate
    ```

---

✅ **4. Install Dependencies**
```bash
pip install -r requirements.txt
```

---

✅ **5. Prepare Input Files**
- Place the required Excel files in the folder:
  ```
  input/
    stromverbrauch.xlsx
    globalstrahlung.xlsx
  ```
- File names must match exactly, and the headers in the Excel files must be identical to those in the input examples!





---

✅ **6. Run the Script**

see **Anleitung.md** for a how to instruction.


In the VS Code terminal:
```bash
python main.py
```
Results will be saved in:
```
output/
  monthly_average_day_profiles.xlsx
  globalstrahlung_jahresprofil_stuendlich.html
  globlastrahlung_stuendlich.xlsx
  monatsprofil_01_Januar.html
  monatsprofil_02_Februar.html
  ...
```
Open the `.html` files in your browser → you can export the charts as PNG there.

Make sure you save the finished output files in your customer folder.

---

✅ **7. Upload Changes (optional)**
If you make changes:
```bash
git add .
git commit -m "Update script"
git push
```
