

# BW2 Custom Unit Maker

# How to Use
## Step 1 — Pick a Unit Template
On the left panel, browse or search the full unit list. Units are grouped by faction and color-coded:

| Color | Faction |
|-------|---------|
| Grey / Green | Western Frontier |
| Dark Red | Tundran Territories |
| Dark Grey | Solar Empire |
| Yellow / Brown | Anglo Isles |
| Light Green / Purple | Iron Legion |
| Dark Teal / Gold | Xylvania |

Click a unit button to select it as your base template.

## Step 2 — Select the Unit's Source Folder

Click **Browse** in the right panel and navigate to the folder containing the unit's extracted game files. It must include a `Models/` subfolder, a `Textures/` subfolder, and a `bundle.xml`. The tool will validate each expected file and show a ✓ or ✗ next to each one — all must pass before you can proceed.

## Step 3 — Enter a Custom Name

In the bottom bar, type your custom unit code:
- **Vehicles:** up to **3 alphanumeric characters** (e.g. `ABC`)
- **Infantry:** **2–3 alphanumeric characters** (e.g. `MG`)

Only letters and numbers are accepted.

## Step 4 — Create the Unit

Click **Create Custom Unit**. The tool will copy the source folder, rename all model and texture files to your new prefix, patch internal binary references inside `.modl` and `.texture` files, and update `bundle.xml` with new resource names and regenerated object IDs.

Your original source files are **never modified**. Output goes to:
- Infantry → `bw2/newly_made_units/{YOUR_PREFIX}_CUSTOM/`
- Vehicle → `bw2/newly_made_units/{YOUR_NAME}H/`

> **Tip:** If you see a ✗ during validation, make sure the folder you selected actually matches the unit you picked in Step 1.
