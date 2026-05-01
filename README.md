# 🚀 Backyard Space Program

A rocket design and flight simulation tool that combines the UI of **OpenRocket** with the customization of **RocketPy**.

---

## Features

- **Career Mode** — Complete progressively challenging missions to unlock new rocket parts
- **Sandbox Mode** — Design fully custom rockets and run detailed flight analysis with your own parts

---

## Installation

### 1. Install Required Python Libraries

```bash
pip install rocketpy matplotlib numpy tkinter
```

> **Note:** `tkinter` is included with most Python installations.

### 2. Extract Project Files

Extract all project files into a new directory. The folder structure should look like:

```
BackyardSpaceProgram/
│   main.py               # Main menu launcher
│   rocket_tk_ui.py       # Rocket editing UI
│   config.py             # Game state (user level, game mode)
│   finbuilder.py         # Fin part editor
│   noseconebuilder.py    # Nosecone part editor
│   tailbuilder.py        # Tail part editor
│
└───data
    ├───airfoils           # Airfoil .csv files
    ├───dragcurves         # Drag curve .csv files
    ├───thrustcurves       # Thrust curve .csv files
    ├───fins               # Fin .txt files
    ├───motors             # Motor .txt files
    ├───nosecones          # Nosecone .txt files
    ├───parachutes         # Parachute .txt files
    └───tails              # Tail .txt files
```

### 3. Internet Connection

An active internet connection is required to download atmospheric sounding data.

### 4. Run the Program

```bash
python main.py
```

---

## Usage

### Career Mode *(Recommended for First-Timers)*

1. Click **"Career Mode"** from the main menu
2. Click **"Yes"** on the tutorial prompt to learn the interface
3. Click **"HELP"** at any time to revisit the tutorial
4. Read the mission objectives in the pop-up message
5. Select parts from the dropdown menus (only unlocked parts are shown)
6. Adjust part positions and parameters using the entry boxes on the left
7. ⚠️ Click **"Update Rocket"** after every change to refresh your design
8. View rocket info and mission goals in the right panel — stay within budget!
9. Ensure the **static margin is positive (green)** before launching
10. Click **"Launch"** to simulate the flight and view the trajectory plot
11. Complete the mission to advance and unlock new parts!

### Sandbox Mode *(For Intermediate Users)*

1. Click **"Sandbox Mode"** from the main menu
2. Read the tutorial message or click **"HELP"** at any time
3. Select parts from the dropdown menus
4. Adjust part positions and parameters using the entry boxes on the left
5. ⚠️ Click **"Update Rocket"** after every change to refresh your design
6. View basic info on the right panel, or click **"More Info"** for detailed specs

#### Custom Part Editors

1. Click any **"Create"** button to open a part editor
2. Adjust parameters using the entry boxes
3. Click **"Update"** to preview your part
4. Set a name in the **"File Name"** box and click **"Save and Export"**
5. Return to the Rocket UI and click **"Update Rocket"** to reload dropdowns
6. Your custom part will now appear in the selection menus
7. Ensure the **static margin is positive (green)** before launching
8. Click **"Launch"** to simulate and view the trajectory plot
9. View detailed post-flight results under **"Flight Results"**
10. Click **"Export KML"** to save the trajectory and open it in Google Earth

---

## Design Tips

- Keep the **static margin between 1.0–3.0 calibers** — unstable or overstable rockets tend to crash the simulation
- Place **fins at the rear** of the rocket
- Use **longer, wider rockets** for larger solid motors
- **Reduce cost** by shortening the rocket body (tube costs $100/kg)
- **Match the Nosecone and Tail top radii exactly** for part compatibility
- Always click **"Update Rocket"** after every change
- Use the toolbar at the bottom of the UI to zoom and pan the rocket view

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Simulation crashes without a stability warning | Re-launch and adjust fins to bring static margin into range |
| "Invalid Fin Position" warning | Ensure the fin position (measured at the top) falls between the tail and nosecone |
| Custom parts don't appear in dropdowns | Click "Update Rocket" after saving to refresh the dropdown lists |
| Slow simulations | Larger, more powerful rockets take longer — be patient |

---

## Advanced Features

### Custom Motor Creation
- Add motor `.txt` files to `data/motors/` following the existing format
- Include corresponding thrust curve `.csv` files in `data/thrustcurves/`

### Custom Airfoils & Drag Curves
- Upload files to the corresponding `data/` folders
- Update the file path references in `rocket_tk_ui.py`

### Custom Weather Data
- Change the weather sounding data URL in `rocket_tk_ui.py`

### Custom Career Missions
- Edit the `get_mission_data()` function in `rocket_editor.py` to add new missions
- Edit individual part `.txt` files to assign `Cost` and `Level` variables

### Detailed Analysis
- Click **"YES"** in the "More Info" and "Flight Info" dialogs to access RocketPy's full analysis, viewable in the terminal

---

## References & Credits

Click **"About"** in the Main Menu for additional references.

Built on top of [RocketPy](https://github.com/RocketPy-Team/RocketPy) — an advanced rocket flight simulator.
