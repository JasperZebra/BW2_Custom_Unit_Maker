import customtkinter as ctk
from tkinter import filedialog
import os
import shutil
import sys
import re
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Dict, Optional
from PIL import Image, ImageTk



ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

@dataclass
class UnitReference:
    file_path: str
    offset: int
    original_name: str
    max_length: int
    xml_element: Optional[ET.Element] = None

class CustomDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, message, dialog_type="info", yes_no=False):
        super().__init__(parent)
        
        self.title(title)
        self.geometry("800x600")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (200 // 2)
        self.geometry(f"800x600+{x}+{y}")
        
        self.result = None
        
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Icon and message
        message_label = ctk.CTkLabel(
            main_frame,
            text=message,
            font=ctk.CTkFont(size=13),
            wraplength=450,
            justify="left"
        )
        message_label.pack(pady=20)
        
        # Button frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(side="bottom", pady=10)
        
        if yes_no:
            # Yes/No buttons
            yes_btn = ctk.CTkButton(
                button_frame,
                text="Yes",
                command=self.on_yes,
                width=100,
                fg_color="#2E7D32",
                hover_color="#1B5E20"
            )
            yes_btn.pack(side="left", padx=5)
            
            no_btn = ctk.CTkButton(
                button_frame,
                text="No",
                command=self.on_no,
                width=100,
                fg_color="#D32F2F",
                hover_color="#B71C1C"
            )
            no_btn.pack(side="left", padx=5)
        else:
            # OK button
            ok_btn = ctk.CTkButton(
                button_frame,
                text="OK",
                command=self.on_ok,
                width=100
            )
            ok_btn.pack()
        
        # Set colors based on dialog type
        if dialog_type == "error":
            message_label.configure(text_color="#FF6B6B")
        elif dialog_type == "warning":
            message_label.configure(text_color="#FFA500")
        elif dialog_type == "success":
            message_label.configure(text_color="#90EE90")
    
    def on_yes(self):
        self.result = True
        self.destroy()
    
    def on_no(self):
        self.result = False
        self.destroy()
    
    def on_ok(self):
        self.result = True
        self.destroy()
    
    def get_result(self):
        self.wait_window()
        return self.result


# Helper functions to replace messagebox
def show_info(parent, title, message):
    dialog = CustomDialog(parent, title, message, dialog_type="info")
    return dialog.get_result()

def show_error(parent, title, message):
    dialog = CustomDialog(parent, title, message, dialog_type="error")
    return dialog.get_result()

def show_warning(parent, title, message):
    dialog = CustomDialog(parent, title, message, dialog_type="warning")
    return dialog.get_result()

def ask_yes_no(parent, title, message):
    dialog = CustomDialog(parent, title, message, dialog_type="info", yes_no=True)
    return dialog.get_result()

class UnitEditorApp(ctk.CTk):
    # Shared/generic files that should never be renamed
    EXCLUDE_TEXTURES = {
        'SFX_white_glow', 'SFX_scorch_mark', 'SFX_smoke3', 'SFX_smoke', 
        'SFX_jetclouds', 'SFX_leaves', 'SFX_smoke4', 'SFX_fireball',
        'SFX_white_blob', 'SFX_waterplume', 'SFX_spot', 'SFX_hl_flare',
        'SFX_smoke2', 'SFX_watersplash', 'SFX_snow', 'SFX_DISPfisheye',
        'SFX_dmg_char', 'SFX_SmokePlume', 'SFX_muzz_shotgun', 'SFX_shock',
        'SFX_watersplash2', 'SFX_Debris', 'SFX_clods', 'SFX_black_spot',
        'SFX_dirt', 'SFX_ground_bits', 'SFX_trails', 'SFX_fireblobanim',
        'SFX_muzz_mg', 'SFX_mist', 'SFX_radial_glows', 'SFX_spawn_tank',
        'SFX_spot_grey', 'SFX_solar_beam', 'SFX_digits_black_on_white',
        'SFX_bigfireadd', 'rotorblur1', 'WF_rocket',
        'GEN_VRPickup'
    }
    
    SKIP_FILES = {
        'GEN_HealthPickup.modl', 'GEN_VRPickup.modl',
        'WF_BOXLOD.modl', 'S_BOXLOD.modl', 'T_BOXLOD.modl', 'X_BOXLOD.modl',
        'AI_BOXLOD.modl', 'U_BOXLOD.modl', 'A_BOXLOD.modl',
        'WF_grenade.modl', 'WF_shell.modl', 'WF_bomb.modl', 'WF_rocket.modl', 'WF_TORPEDO.modl',
        'S_grenade.modl', 'S_shell.modl', 'S_bomb.modl', 'S_rocket.modl', 'S_TORPEDO.modl',
        'T_grenade.modl', 'T_shell.modl', 'T_bomb.modl', 'T_rocket.modl', 'T_TORPEDO.modl',
        'X_grenade.modl','X_shell.modl', 'X_bomb.modl', 'X_rocket.modl', 'X_TORPEDO.modl',
        'AI_grenade.modl', 'AI_shell.modl', 'AI_bomb.modl', 'AI_rocket.modl', 'AI_TORPEDO.modl',
        'U_grenade.modl', 'U_shell.modl', 'U_bomb.modl', 'U_rocket.modl', 'U_TORPEDO.modl',
        'N_TORPEDO.modl'
    }

    def __init__(self):
        super().__init__()

        import os
        script_dir = get_base_dir()

        self.title("Battalion Wars: Custom Unit Editor | Made By: Jasper_Zebra | Version 2.0")
        self.geometry("1200x800")

        icon_path = os.path.join(script_dir, "app_icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.unit_folder = None
        self.selected_template = None
        self.template_data = None
        self.found_files = {"models": {}, "textures": {}, "icon": None}
        self.references: List[UnitReference] = []

        # Load all faction JSON files into unit_templates
        self.unit_templates = self.load_templates()
        if not self.unit_templates:
            return

        self.icon_images = {}

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        import os
        from PIL import Image, ImageTk

        # Script directory
        script_dir = get_base_dir()
        print(f"[DEBUG] script_dir: {script_dir}")

        # Keep references to images so they are not garbage-collected
        self.icon_images = {}

        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Battalion Wars 2: Custom Unit Editor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="ew")

        # LEFT COLUMN - Template Selection
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=1, column=0, padx=(0, 5), pady=5, sticky="nsew")

        ctk.CTkLabel(
            left_frame,
            text="Step 1: Select Unit Type",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Search bar
        search_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=5)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search units...")
        self.search_entry.pack(fill="x", padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_units)

        # Scrollable unit list
        self.unit_list_frame = ctk.CTkScrollableFrame(left_frame)
        self.unit_list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Faction colors
        self.faction_colors = {
            "WF": ("#adada5", "#efefe7", "#b5d684", "black"),
            "T": ("#942910", "#bd2918", "#000000", "white"),
            "S": ("#52525a", "#9c9cad", "#dedede", "white"),
            "AI": ("#efce29", "#ffff6b", "#522100", "black"),
            "IL": ("#9cf794", "#bdffad", "#8c08e7", "black"),
            "X": ("#315263", "#426373", "#ffcd22", "white"),
        }

        # Create template buttons
        self.template_names = [v["display_name"] for v in self.unit_templates.values()]
        self.unit_buttons = []

        # O(1) lookup instead of O(n) search per button
        name_to_template = {v["display_name"]: v for v in self.unit_templates.values()}

        # Pre-load unique icons once (many units share the same icon file)
        icon_cache = {}
        for tmpl in self.unit_templates.values():
            iname = tmpl.get("icon")
            if iname:
                ipath = os.path.join(script_dir, "assets", "icons", iname.split(".")[0] + ".png")
                if ipath not in icon_cache and os.path.exists(ipath):
                    icon_cache[ipath] = ctk.CTkImage(Image.open(ipath), size=(32, 32))
        self.icon_images.update(icon_cache)  # keep references alive

        sorted_names = sorted(self.template_names)

        # Build buttons in batches so the window appears immediately
        def _build_buttons(idx=0, batch=20):
            for template_name in sorted_names[idx:idx + batch]:
                template = name_to_template.get(template_name)
                if not template:
                    continue

                faction = template.get("faction")
                icon_name = template.get("icon")
                colors = self.faction_colors.get(faction, ("#1F6AA5", "#3A8AC9", "#144870", "white"))
                normal_color, hover_color, border_color, text_color = colors

                icon_photo = None
                if icon_name:
                    ipath = os.path.join(script_dir, "assets", "icons", icon_name.split(".")[0] + ".png")
                    icon_photo = icon_cache.get(ipath)

                unit_frame = ctk.CTkFrame(self.unit_list_frame, fg_color="transparent")
                unit_frame.pack(fill="x", padx=2, pady=3)

                btn = ctk.CTkButton(
                    unit_frame,
                    text=template_name,
                    command=lambda name=template_name: self.on_template_selected(name),
                    height=40,
                    anchor="w",
                    fg_color=normal_color,
                    hover_color=hover_color,
                    border_color=border_color,
                    border_width=2,
                    text_color=text_color,
                    font=ctk.CTkFont(size=16, weight="normal"),
                    image=icon_photo,
                    compound="right"
                )
                btn.pack(fill="x", expand=True)
                self.unit_buttons.append((unit_frame, template_name))

            if idx + batch < len(sorted_names):
                self.after(1, lambda: _build_buttons(idx + batch))

        self.after(0, _build_buttons)

        # Unit info display
        self.unit_info_label = ctk.CTkLabel(
            left_frame,
            text="No unit selected",
            font=ctk.CTkFont(size=11),
            wraplength=350,
            width=400,
            anchor="w"
        )
        self.unit_info_label.pack(fill="x", padx=10, pady=5)

        # RIGHT COLUMN - Folder Selection & Validation
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=1, column=1, padx=(5, 0), pady=5, sticky="nsew")

        ctk.CTkLabel(
            right_frame,
            text="Step 2: Select Folder",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        folder_btn_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        folder_btn_frame.pack(fill="x", padx=10, pady=5)

        self.folder_btn = ctk.CTkButton(
            folder_btn_frame,
            text="Browse",
            command=self.select_folder,
            state="disabled",
            width=100
        )
        self.folder_btn.pack(side="left", padx=5)

        self.folder_label = ctk.CTkLabel(
            folder_btn_frame,
            text="No folder selected",
            font=ctk.CTkFont(size=11),
            width=400,
            anchor="w"
        )
        self.folder_label.pack(side="left", padx=5, fill="x", expand=True)

        # File validation
        ctk.CTkLabel(
            right_frame,
            text="File Validation",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.validation_scroll = ctk.CTkScrollableFrame(right_frame)
        self.validation_scroll.pack(fill="both", expand=True, padx=10, pady=5)

        # BOTTOM ROW - Rename Section
        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.grid(row=2, column=0, columnspan=2, pady=(5, 0), sticky="ew")

        ctk.CTkLabel(
            bottom_frame,
            text="Step 3: Enter New Name",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        name_input_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        name_input_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            name_input_frame,
            text="New Name:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=5)

        self.name_entry = ctk.CTkEntry(
            name_input_frame,
            width=250,
            placeholder_text="Enter 3-character code (e.g. TTS)..."
        )
        self.name_entry.pack(side="left", padx=5)
        self.name_entry.bind("<KeyRelease>", lambda e: (self.limit_name_length(), self.validate_name()))

        self.char_counter_label = ctk.CTkLabel(
            name_input_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.char_counter_label.pack(side="left", padx=(0, 5))

        self.name_validation_label = ctk.CTkLabel(
            name_input_frame,
            text="",
            font=ctk.CTkFont(size=10)
        )
        self.name_validation_label.pack(side="left", padx=10)

        self.apply_btn = ctk.CTkButton(
            name_input_frame,
            text="Create Custom Unit",
            command=self.apply_changes,
            state="disabled",
            height=35,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.apply_btn.pack(side="right", padx=10)

        self.status_label = ctk.CTkLabel(
            bottom_frame,
            text="Ready",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(pady=(5, 10))

    def limit_name_length(self, event=None):
        """Limit name entry to 3 characters maximum"""
        if not self.template_data:
            return

        # Always enforce 3-character maximum
        max_len = 3

        # Get current text
        current_text = self.name_entry.get()

        # If text exceeds max length, truncate it
        if len(current_text) > max_len:
            self.name_entry.delete(max_len, "end")
            current_text = self.name_entry.get()

        self.char_counter_label.configure(text=f"{len(current_text)}/{max_len}")

    def filter_units(self, event=None):
        """Debounce search input before filtering"""
        if hasattr(self, '_filter_job'):
            self.after_cancel(self._filter_job)
        self._filter_job = self.after(150, self._apply_filter)

    def _apply_filter(self):
        """Filter unit list based on search input"""
        search_term = self.search_entry.get().lower()

        # Unpack all first to preserve order when re-packing
        for unit_frame, template_name in self.unit_buttons:
            unit_frame.pack_forget()

        for unit_frame, template_name in self.unit_buttons:
            if not search_term or search_term in template_name.lower():
                unit_frame.pack(fill="x", padx=2, pady=3)

    def on_template_selected(self, choice):
        """Handle template selection"""
        # Find the template key from display name
        for key, template in self.unit_templates.items():
            if template["display_name"] == choice:
                self.selected_template = key
                self.template_data = template
                break
        
        if self.template_data:
            unit_type = "Infantry" if self.template_data["type"] == "infantry" else "Vehicle"
            faction = self.template_data["faction"]
            
            if self.template_data["type"] == "infantry":
                prefix = self.template_data["base_prefix"]
                info_text = f"Type: {unit_type} | Faction: {faction} | Prefix: {prefix}"
            else:
                base_name = self.template_data["base_name"]
                info_text = f"Type: {unit_type} | Faction: {faction} | Base: {base_name}"
            
            self.unit_info_label.configure(text=info_text)
            self.folder_btn.configure(state="normal")
            self.status_label.configure(text=f"Selected: {choice}")
            self.char_counter_label.configure(text="0/3")
            self.name_entry.delete(0, "end")
    
    def validate_folder(self):
        """Validate that the folder contains expected files"""
        if not self.unit_folder or not self.template_data:
            return
        
        folder_name = os.path.basename(self.unit_folder)
        self.folder_label.configure(text=f"Selected: {folder_name}")
        self.status_label.configure(text="Validating files...")

        # Clear previous validation
        for widget in self.validation_scroll.winfo_children():
            widget.destroy()

        self.found_files = {"models": {}, "textures": {}, "icon": None}

        models_path = os.path.join(self.unit_folder, "Models")
        textures_path = os.path.join(self.unit_folder, "Textures")

        # Shared fonts — created once, reused for every label
        font_small = ctk.CTkFont(size=11)
        font_heading = ctk.CTkFont(size=14, weight="bold")

        # Check Models
        ctk.CTkLabel(
            self.validation_scroll,
            text="📦 Models:",
            font=font_heading
        ).pack(anchor="w", pady=(10, 5))

        if os.path.exists(models_path):
            for model_key, model_file in self.template_data["models"].items():
                if model_file:
                    model_path = os.path.join(models_path, model_file)
                    if os.path.exists(model_path):
                        self.found_files["models"][model_key] = model_path
                        ctk.CTkLabel(
                            self.validation_scroll,
                            text=f"  ✓ {model_key}: {model_file}",
                            text_color="lightgreen",
                            font=font_small
                        ).pack(anchor="w", padx=20)
                    else:
                        ctk.CTkLabel(
                            self.validation_scroll,
                            text=f"  ✗ {model_key}: {model_file} (NOT FOUND)",
                            text_color="red",
                            font=font_small
                        ).pack(anchor="w", padx=20)

        # Check Textures
        ctk.CTkLabel(
            self.validation_scroll,
            text="🎨 Textures:",
            font=font_heading
        ).pack(anchor="w", pady=(10, 5))

        if os.path.exists(textures_path):
            for texture_key, texture_file in self.template_data["textures"].items():
                if texture_file:
                    texture_path = os.path.join(textures_path, texture_file)
                    if os.path.exists(texture_path):
                        self.found_files["textures"][texture_key] = texture_path
                        ctk.CTkLabel(
                            self.validation_scroll,
                            text=f"  ✓ {texture_key}: {texture_file}",
                            text_color="lightgreen",
                            font=font_small
                        ).pack(anchor="w", padx=20)
                    else:
                        ctk.CTkLabel(
                            self.validation_scroll,
                            text=f"  ✗ {texture_key}: {texture_file} (NOT FOUND)",
                            text_color="orange",
                            font=font_small
                        ).pack(anchor="w", padx=20)

        # Check Icon
        ctk.CTkLabel(
            self.validation_scroll,
            text="🎨 Icon:",
            font=font_heading
        ).pack(anchor="w", pady=(10, 5))

        if "icon" in self.template_data:
            icon_file = self.template_data["icon"]
            icon_path = os.path.join(textures_path, icon_file)
            if os.path.exists(icon_path):
                self.found_files["icon"] = icon_path
                ctk.CTkLabel(
                    self.validation_scroll,
                    text=f"  ✓ {icon_file}",
                    text_color="lightgreen",
                    font=font_small
                ).pack(anchor="w", padx=20)
            else:
                ctk.CTkLabel(
                    self.validation_scroll,
                    text=f"  ✗ {icon_file} (NOT FOUND)",
                    text_color="orange",
                    font=font_small
                ).pack(anchor="w", padx=20)

        # Check bundle.xml
        ctk.CTkLabel(
            self.validation_scroll,
            text="📄 Configuration:",
            font=font_heading
        ).pack(anchor="w", pady=(10, 5))

        bundle_path = os.path.join(self.unit_folder, "bundle.xml")
        if os.path.exists(bundle_path):
            ctk.CTkLabel(
                self.validation_scroll,
                text=f"  ✓ bundle.xml",
                text_color="lightgreen",
                font=font_small
            ).pack(anchor="w", padx=20)
        else:
            ctk.CTkLabel(
                self.validation_scroll,
                text=f"  ✗ bundle.xml (NOT FOUND)",
                text_color="red",
                font=font_small
            ).pack(anchor="w", padx=20)
        
        # Enable name entry if we have at least some files
        if self.found_files["models"] or self.found_files["textures"]:
            self.name_entry.configure(state="normal")
            self.status_label.configure(text="✓ Files validated - Enter new name")
        else:
            self.status_label.configure(text="✗ No valid files found")
    
    def validate_name(self):
        """Validate the entered name"""
        new_name = self.name_entry.get().strip()
        
        if not new_name:
            self.name_validation_label.configure(text="", text_color="white")
            self.apply_btn.configure(state="disabled")
            return
        
        # Check if name is alphanumeric
        if not new_name.isalnum():
            self.name_validation_label.configure(
                text="✗ Name must be alphanumeric only",
                text_color="red"
            )
            self.apply_btn.configure(state="disabled")
            return
        
        # Check length based on unit type
        if self.template_data["type"] == "infantry":
            # Infantry uses 2-char prefix
            if len(new_name) < 2:
                self.name_validation_label.configure(
                    text="✗ Name too short (min 2 characters for infantry)",
                    text_color="red"
                )
                self.apply_btn.configure(state="disabled")
                return
            
            max_len = len(self.template_data["base_prefix"])
            if len(new_name) > max_len:
                self.name_validation_label.configure(
                    text=f"✗ Name too long (max {max_len} characters)",
                    text_color="red"
                )
                self.apply_btn.configure(state="disabled")
                return
        else:
            # Vehicle
            max_len = len(self.template_data["base_name"])
            if len(new_name) > max_len:
                self.name_validation_label.configure(
                    text=f"✗ Name too long (max {max_len} characters)",
                    text_color="red"
                )
                self.apply_btn.configure(state="disabled")
                return
        
        self.name_validation_label.configure(
            text="✓ Valid name",
            text_color="lightgreen"
        )
        self.apply_btn.configure(state="normal")
        
    def apply_positional_replacement(self, old_filename: str, new_base: str) -> str:
        """
        Apply positional character replacement to a filename.
        Replaces the first N characters where N = length of new_base.
        Preserves numeric suffixes that appear right before underscores or at specific positions.
        
        Args:
            old_filename: Original filename (without extension)
            new_base: New base name to use
        
        Returns:
            New filename with positional replacement applied
        """
        import re
        
        replacement_length = len(new_base)
        
        # Check if there's a numeric suffix in the old filename that should be preserved
        # Pattern: looks for digits that appear right after the base name portion
        if len(old_filename) >= replacement_length:
            base_portion = old_filename[:replacement_length]
            suffix_portion = old_filename[replacement_length:]
            
            # Check if suffix starts with a digit (like "0_SPEC", "1_main", etc)
            if suffix_portion and suffix_portion[0].isdigit():
                # Extract the number at the start of suffix
                match = re.match(r'^(\d+)', suffix_portion)
                if match:
                    number = match.group(1)
                    remaining = suffix_portion[len(number):]
                    new_filename = new_base + number + remaining
                else:
                    new_filename = new_base + suffix_portion
            else:
                new_filename = new_base + suffix_portion
        else:
            # If original is shorter, just use new_base (truncated if needed)
            new_filename = new_base[:len(old_filename)]
        
        return new_filename
        

    def replace_case_insensitive(self, data: bytearray, old_bytes: bytes, new_bytes: bytes) -> bytearray:
        """Replace all occurrences of old_bytes with new_bytes (case-insensitive for ASCII)"""
        if len(old_bytes) != len(new_bytes):
            # Safety check - lengths must match for binary files
            return data

        result = bytearray(data)
        pattern = re.escape(old_bytes)
        # re.finditer on a bytes snapshot — C-speed scan instead of a Python byte loop
        for m in re.finditer(pattern, bytes(result), re.IGNORECASE):
            start = m.start()
            for j in range(len(new_bytes)):
                orig = result[start + j]
                nb = new_bytes[j]
                # Preserve the case of the original byte
                if 65 <= orig <= 90:    # Uppercase original
                    result[start + j] = nb if 65 <= nb <= 90 else (nb - 32)
                elif 97 <= orig <= 122:  # Lowercase original
                    result[start + j] = nb if 97 <= nb <= 122 else (nb + 32)
                else:
                    result[start + j] = nb

        return result
    
    def replace_all_cases(self, data: bytearray, old_str: str, new_str: str) -> bytearray:
        """Replace string in all case variations (original, UPPER, lower) maintaining field length"""
        if len(old_str) != len(new_str):
            return data  # Safety check
        
        # Replace original case
        old_bytes = old_str.encode('ascii')
        new_bytes = new_str.encode('ascii')
        data = data.replace(old_bytes, new_bytes)
        
        # Replace uppercase
        old_upper = old_str.upper().encode('ascii')
        new_upper = new_str.upper().encode('ascii')
        data = data.replace(old_upper, new_upper)
        
        # Replace lowercase  
        old_lower = old_str.lower().encode('ascii')
        new_lower = new_str.lower().encode('ascii')
        data = data.replace(old_lower, new_lower)
        
        return data

    def load_templates(self):
        """Load unit templates from multiple JSON files"""
        script_dir = get_base_dir()
        
        # List of all faction JSON files
        json_files = [
            "anglo_units.json",
            "iron_legion_units.json", 
            "solar_units.json",
            "tundran_units.json",
            "wf_units.json",
            "xylvania_units.json"
        ]
        
        all_templates = {}
        
        for json_file in json_files:
            json_path = os.path.join(script_dir, "units", "bw2", json_file)
            
            try:
                with open(json_path, 'r') as f:
                    faction_data = json.load(f)
                    all_templates.update(faction_data)
            except FileNotFoundError:
                show_warning(
                    self, 
                    "Warning", 
                    f"{json_file} not found in units/bw2/. Skipping this faction."
                )
                continue
            except json.JSONDecodeError as e:
                show_error(
                    self, 
                    "Error", 
                    f"Error reading {json_file}:\n{str(e)}"
                )
                continue
        
        if not all_templates:
            show_error(
                self,
                "Error",
                "No valid unit template files found!\n\nPlease ensure the JSON files exist in units/bw2/."
            )
            self.destroy()
        
        return all_templates

    def select_folder(self):
        """Select unit folder"""
        if not self.selected_template:
            show_error(self, "Error", "Please select a unit type first!")
            return
        
        folder = filedialog.askdirectory(title="Select Unit Folder")
        if folder:
            self.unit_folder = folder
            self.validate_folder()

    def apply_changes(self):
        """Apply renaming changes to create custom unit"""
        new_name = self.name_entry.get().strip().upper()
        
        if not new_name:
            show_error(self, "Error", "Please enter a new name")
            return
        
        # Prepare confirmation message
        model_count = len(self.found_files["models"])
        texture_count = len(self.found_files["textures"])
        has_icon = 1 if self.found_files["icon"] else 0
        
        self.status_label.configure(text="Creating custom unit...")
        self.update()
        
        try:
            if self.template_data["type"] == "infantry":
                self.create_infantry_unit(new_name)
            else:
                self.create_vehicle_unit(new_name)
            
            self.status_label.configure(text="✓ Custom unit created successfully!")
                    
        except Exception as e:
            self.status_label.configure(text="✗ Error creating unit")
            show_error(self, "Error", f"Failed to create unit:\n{str(e)}")

    def create_vehicle_unit(self, new_name: str):
        """Create custom vehicle unit"""
        # Enforce 3-character limit
        if len(new_name) > 3:
            show_error(self, "Invalid Name Length", 
                      f"New unit name must be exactly 3 characters or less.\n\n"
                      f"You entered: '{new_name}' ({len(new_name)} characters)\n"
                      f"Please use a 3-character code (e.g., 'TTS' for Tundran Territories Strato)")
            return
        
        old_base = self.template_data["base_name"]
        new_base = new_name.upper()
        
        # Create output directory
        script_dir = get_base_dir()
        output_base = os.path.join(script_dir, "bw2", "newly_made_units")
        output_folder = os.path.join(output_base, f"{new_base}H")
        
        os.makedirs(output_folder, exist_ok=True)
        
        # Copy entire folder
        for item in os.listdir(self.unit_folder):
            source = os.path.join(self.unit_folder, item)
            destination = os.path.join(output_folder, item)
            
            if os.path.isdir(source):
                if os.path.exists(destination):
                    shutil.rmtree(destination)
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
        
        renamed_files = []
        
        # Collect all texture names that need to be replaced in model files
        texture_replacements = {}
        
        # Process all textures from template
        textures_path = os.path.join(output_folder, "Textures")
        for texture_key, texture_filename in self.template_data["textures"].items():
            if not texture_filename:
                continue
                
            old_texture_path = os.path.join(textures_path, texture_filename)
            if not os.path.exists(old_texture_path):
                continue
            
            # Get filename without extension
            old_filename_without_ext = texture_filename[:-8]  # Remove .texture
            
            # Skip excluded textures
            if old_filename_without_ext in self.EXCLUDE_TEXTURES:
                continue
            
            # Apply positional replacement
            new_filename_without_ext = self.apply_positional_replacement(old_filename_without_ext, new_base)
            new_texture_filename = new_filename_without_ext + ".texture"
            
            # Store for model file replacement
            texture_replacements[old_filename_without_ext] = new_filename_without_ext
            
            # Update internal name in texture file
            with open(old_texture_path, 'rb') as f:
                data = bytearray(f.read())
            
            old_name_bytes = old_filename_without_ext.encode('ascii')
            new_name_bytes = new_filename_without_ext.encode('ascii')
            
            old_byte_len = len(old_name_bytes)
            new_byte_len = len(new_name_bytes)
            replacement = new_name_bytes + b'\x00' * (old_byte_len - new_byte_len)
            
            data = data.replace(old_name_bytes, replacement)
            
            with open(old_texture_path, 'wb') as f:
                f.write(data)
            
            # Rename file
            new_texture_path = os.path.join(textures_path, new_texture_filename)
            if old_texture_path != new_texture_path:
                # Check if destination already exists
                if os.path.exists(new_texture_path):
                    print(f"Warning: {new_texture_path} already exists, skipping rename")
                else:
                    os.rename(old_texture_path, new_texture_path)
                renamed_files.append(f"{texture_filename} → {new_texture_filename}")
        
        # Rename icon
        if self.found_files["icon"]:
            old_icon_path = self.found_files["icon"]
            old_icon_filename = os.path.basename(old_icon_path)
            
            # Apply positional replacement to icon
            old_icon_name = old_icon_filename[:-8]
            new_icon_name = self.apply_positional_replacement(old_icon_name, new_base)
            new_icon_filename = new_icon_name + ".texture"
            
            old_path = os.path.join(textures_path, old_icon_filename)
            new_path = os.path.join(textures_path, new_icon_filename)
            
            if os.path.exists(old_path):
                # Update internal name
                with open(old_path, 'rb') as f:
                    data = bytearray(f.read())
                
                old_name_bytes = old_icon_name.encode('ascii')
                new_name_bytes = new_icon_name.encode('ascii')
                
                old_byte_len = len(old_name_bytes)
                new_byte_len = len(new_name_bytes)
                replacement = new_name_bytes + b'\x00' * (old_byte_len - new_byte_len)
                
                data = data.replace(old_name_bytes, replacement)
                
                with open(old_path, 'wb') as f:
                    f.write(data)
                
                if old_path != new_path:
                    os.rename(old_path, new_path)
                    renamed_files.append(f"{old_icon_filename} → {new_icon_filename} (icon)")
        
        # Rename model files and update internal references
        models_path = os.path.join(output_folder, "Models")
        for model_key, model_path in self.found_files["models"].items():
            old_filename = os.path.basename(model_path)
            
            # Apply positional replacement to model filename (without .modl)
            old_model_name = old_filename[:-5]  # Remove .modl
            new_model_name = self.apply_positional_replacement(old_model_name, new_base)
            new_filename = new_model_name + ".modl"
            
            old_path = os.path.join(models_path, old_filename)
            new_path = os.path.join(models_path, new_filename)
            
            if os.path.exists(old_path):
                # Update internal references in model file
                with open(old_path, 'rb') as f:
                    data = bytearray(f.read())
                
                # Replace old base with new base (using positional replacement to maintain length)
                # Search for all case variations
                old_base_replaced = self.apply_positional_replacement(old_base, new_base)
                if len(old_base) == len(old_base_replaced):
                    data = self.replace_all_cases(data, old_base, old_base_replaced)
                
                # Replace BGF name (all case variations)
                old_bgf = self.template_data["bgf_name"]
                new_bgf = self.apply_positional_replacement(old_bgf, new_base)
                data = self.replace_all_cases(data, old_bgf, new_bgf)
                
                # Replace all model references from template (all case variations)
                if "models" in self.template_data:
                    for model_key, model_filename in self.template_data["models"].items():
                        if not model_filename:
                            continue
                        
                        old_model_ref = model_filename[:-5]  # Remove .modl
                        new_model_ref = self.apply_positional_replacement(old_model_ref, new_base)
                        data = self.replace_all_cases(data, old_model_ref, new_model_ref)
                
                # Replace all texture references from template
                for old_tex_name, new_tex_name in texture_replacements.items():
                    old_tex_bytes = old_tex_name.encode('ascii')
                    new_tex_bytes = new_tex_name.encode('ascii')
                    data = data.replace(old_tex_bytes, new_tex_bytes)
                
                with open(old_path, 'wb') as f:
                    f.write(data)
                
                # Rename file
                if old_path != new_path:
                    os.rename(old_path, new_path)
                    renamed_files.append(f"{old_filename} → {new_filename}")
        
        # Update bundle.xml
        bundle_path = os.path.join(output_folder, "bundle.xml")
        if os.path.exists(bundle_path):
            self.process_bundle_xml_vehicle(bundle_path, old_base, new_base)
        
        # Show results
        success_msg = (f"Vehicle unit created successfully!\n\n"
                    f"Base: {old_base} → {new_base}\n"
                    f"Output: {output_folder}\n\n"
                    f"Renamed {len(renamed_files)} files")
        
        if renamed_files:
            success_msg += ":\n" + "\n".join(f"• {r}" for r in renamed_files[:10])
            if len(renamed_files) > 10:
                success_msg += f"\n• ... and {len(renamed_files) - 10} more"
        
        if ask_yes_no(self, "Success", success_msg + "\n\nOpen the output folder?"):
            if os.name == 'nt':
                os.startfile(output_folder)
            elif os.name == 'posix':
                os.system(f'open "{output_folder}"' if sys.platform == 'darwin' else f'xdg-open "{output_folder}"')

    def create_infantry_unit(self, new_name: str):
        """Create custom infantry unit"""
        # Enforce 3-character limit
        if len(new_name) > 3:
            show_error(self, "Invalid Name Length", 
                      f"New unit name must be exactly 3 characters or less.\n\n"
                      f"You entered: '{new_name}' ({len(new_name)} characters)\n"
                      f"Please use a 3-character code (e.g., 'TTG' for Tundran Territories Grunt)")
            return
        
        old_prefix = self.template_data["base_prefix"]
        new_prefix = new_name.upper()
        
        # Create output directory
        script_dir = get_base_dir()
        output_base = os.path.join(script_dir, "bw2", "newly_made_units")
        output_folder = os.path.join(output_base, f"{new_prefix}_CUSTOM")
        
        os.makedirs(output_folder, exist_ok=True)
        
        # Copy entire folder
        for item in os.listdir(self.unit_folder):
            source = os.path.join(self.unit_folder, item)
            destination = os.path.join(output_folder, item)
            
            if os.path.isdir(source):
                if os.path.exists(destination):
                    shutil.rmtree(destination)
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
        
        renamed_files = []
        
        # Collect all texture names that need to be replaced in model files
        texture_replacements = {}
        
        # Process all textures from template
        textures_path = os.path.join(output_folder, "Textures")
        for texture_key, texture_filename in self.template_data["textures"].items():
            if not texture_filename:
                continue
                
            old_texture_path = os.path.join(textures_path, texture_filename)
            if not os.path.exists(old_texture_path):
                continue
            
            # Get filename without extension
            old_filename_without_ext = texture_filename[:-8]  # Remove .texture
            
            # Skip excluded textures
            if old_filename_without_ext in self.EXCLUDE_TEXTURES:
                continue
            
            # Apply positional replacement
            new_filename_without_ext = self.apply_positional_replacement(old_filename_without_ext, new_prefix)
            new_texture_filename = new_filename_without_ext + ".texture"
            
            # Store for model file replacement
            texture_replacements[old_filename_without_ext] = new_filename_without_ext
            
            # Update internal name in texture file
            with open(old_texture_path, 'rb') as f:
                data = bytearray(f.read())
            
            old_name_bytes = old_filename_without_ext.encode('ascii')
            new_name_bytes = new_filename_without_ext.encode('ascii')
            
            old_byte_len = len(old_name_bytes)
            new_byte_len = len(new_name_bytes)
            replacement = new_name_bytes + b'\x00' * (old_byte_len - new_byte_len)
            
            data = data.replace(old_name_bytes, replacement)
            
            with open(old_texture_path, 'wb') as f:
                f.write(data)
            
            # Rename file
            new_texture_path = os.path.join(textures_path, new_texture_filename)
            if old_texture_path != new_texture_path:
                # Check if destination already exists
                if os.path.exists(new_texture_path):
                    print(f"Warning: {new_texture_path} already exists, skipping rename")
                else:
                    os.rename(old_texture_path, new_texture_path)
                renamed_files.append(f"{texture_filename} → {new_texture_filename}")
        
        # Rename icon
        if self.found_files["icon"]:
            old_icon_path = self.found_files["icon"]
            old_icon_filename = os.path.basename(old_icon_path)
            
            # Apply positional replacement to icon
            old_icon_name = old_icon_filename[:-8]
            new_icon_name = self.apply_positional_replacement(old_icon_name, new_prefix)
            new_icon_filename = new_icon_name + ".texture"
            
            old_path = os.path.join(textures_path, old_icon_filename)
            new_path = os.path.join(textures_path, new_icon_filename)
            
            if os.path.exists(old_path):
                # Update internal name
                with open(old_path, 'rb') as f:
                    data = bytearray(f.read())
                
                old_name_bytes = old_icon_name.encode('ascii')
                new_name_bytes = new_icon_name.encode('ascii')
                
                old_byte_len = len(old_name_bytes)
                new_byte_len = len(new_name_bytes)
                replacement = new_name_bytes + b'\x00' * (old_byte_len - new_byte_len)
                
                data = data.replace(old_name_bytes, replacement)
                
                with open(old_path, 'wb') as f:
                    f.write(data)
                
                if old_path != new_path:
                    os.rename(old_path, new_path)
                    renamed_files.append(f"{old_icon_filename} → {new_icon_filename} (icon)")
        
        # Rename model files and update internal references
        models_path = os.path.join(output_folder, "Models")
        for model_key, model_path in self.found_files["models"].items():
            old_filename = os.path.basename(model_path)
            
            # Apply positional replacement to model filename (without .modl)
            old_model_name = old_filename[:-5]  # Remove .modl
            new_model_name = self.apply_positional_replacement(old_model_name, new_prefix)
            new_filename = new_model_name + ".modl"
            
            old_path = os.path.join(models_path, old_filename)
            new_path = os.path.join(models_path, new_filename)
            
            if os.path.exists(old_path):
                # Update internal references in model file
                with open(old_path, 'rb') as f:
                    data = bytearray(f.read())
                
                # Replace old prefix with new prefix
                old_bytes = old_prefix.encode('ascii')
                new_bytes = new_prefix.encode('ascii')
                data = data.replace(old_bytes, new_bytes)
                
                # Replace BGF name if present (all case variations)
                if "bgf_name" in self.template_data:
                    old_bgf = self.template_data["bgf_name"]
                    new_bgf = self.apply_positional_replacement(old_bgf, new_prefix)
                    data = self.replace_all_cases(data, old_bgf, new_bgf)
                
                # Replace all model references from template (all case variations)
                if "models" in self.template_data:
                    for model_key, model_filename in self.template_data["models"].items():
                        if not model_filename:
                            continue
                        
                        old_model_ref = model_filename[:-5]  # Remove .modl
                        new_model_ref = self.apply_positional_replacement(old_model_ref, new_prefix)
                        data = self.replace_all_cases(data, old_model_ref, new_model_ref)
                
                # Replace all texture references from template
                for old_tex_name, new_tex_name in texture_replacements.items():
                    old_tex_bytes = old_tex_name.encode('ascii')
                    new_tex_bytes = new_tex_name.encode('ascii')
                    data = data.replace(old_tex_bytes, new_tex_bytes)
                
                with open(old_path, 'wb') as f:
                    f.write(data)
                
                # Rename file
                if old_path != new_path:
                    os.rename(old_path, new_path)
                    renamed_files.append(f"{old_filename} → {new_filename}")
        
        # Update bundle.xml
        bundle_path = os.path.join(output_folder, "bundle.xml")
        if os.path.exists(bundle_path):
            self.process_bundle_xml_infantry(bundle_path, old_prefix, new_prefix)
        
        # Show results
        success_msg = (f"Infantry unit created successfully!\n\n"
                    f"Prefix: {old_prefix} → {new_prefix}\n"
                    f"Output: {output_folder}\n\n"
                    f"Renamed {len(renamed_files)} files")
        
        if renamed_files:
            success_msg += ":\n" + "\n".join(f"• {r}" for r in renamed_files[:10])
            if len(renamed_files) > 10:
                success_msg += f"\n• ... and {len(renamed_files) - 10} more"
        
        if ask_yes_no(self, "Success", success_msg + "\n\nOpen the output folder?"):
            if os.name == 'nt':
                os.startfile(output_folder)
            elif os.name == 'posix':
                os.system(f'open "{output_folder}"' if sys.platform == 'darwin' else f'xdg-open "{output_folder}"')

    def process_bundle_xml_infantry(self, file_path: str, old_prefix: str, new_prefix: str):
        """Process bundle.xml for infantry units"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Collect all existing IDs to avoid conflicts
            existing_ids = set()
            for obj in root.findall('.//Object'):
                obj_id = obj.get('id')
                if obj_id:
                    existing_ids.add(obj_id)
            for item in root.findall('.//Item'):
                if item.text and item.text.isdigit():
                    existing_ids.add(item.text)
            
            # Map old IDs to new IDs
            id_mapping = {}
            new_ids = set()

            def generate_unique_id():
                """Generate a unique random ID"""
                import random
                while True:
                    new_id = str(random.randint(9000000000, 9999999999))
                    if new_id not in existing_ids and new_id not in new_ids:
                        existing_ids.add(new_id)
                        new_ids.add(new_id)
                        return new_id

            # Pre-fetch node lists once instead of once per model/texture
            model_nodes   = root.findall('.//Object[@type="cNodeHierarchyResource"]')
            texture_nodes = root.findall('.//Object[@type="cTextureResource"]')

            # Update cNodeHierarchyResource objects (models)
            if "models" in self.template_data:
                for model_key, model_filename in self.template_data["models"].items():
                    if not model_filename:
                        continue

                    old_model_name = model_filename[:-5]  # Remove .modl
                    new_model_name = self.apply_positional_replacement(old_model_name, new_prefix)

                    for obj in model_nodes:
                        name_elem = obj.find('.//Attribute[@name="mName"]/Item')
                        if name_elem is not None and name_elem.text:
                            if name_elem.text.strip() == old_model_name:
                                name_elem.text = new_model_name

                                # Update ID
                                old_id = obj.get('id')
                                if old_id:
                                    new_id = generate_unique_id()
                                    id_mapping[old_id] = new_id
                                    obj.set('id', new_id)

            # Update cTextureResource objects (textures)
            if "textures" in self.template_data:
                for texture_key, texture_filename in self.template_data["textures"].items():
                    if not texture_filename:
                        continue

                    old_texture_name = texture_filename[:-8]  # Remove .texture

                    # Skip excluded textures
                    if old_texture_name in self.EXCLUDE_TEXTURES:
                        continue

                    new_texture_name = self.apply_positional_replacement(old_texture_name, new_prefix)

                    for obj in texture_nodes:
                        name_elem = obj.find('.//Attribute[@name="mName"]/Item')
                        if name_elem is not None and name_elem.text:
                            if name_elem.text.strip() == old_texture_name:
                                name_elem.text = new_texture_name

                                # Update ID
                                old_id = obj.get('id')
                                if old_id:
                                    new_id = generate_unique_id()
                                    id_mapping[old_id] = new_id
                                    obj.set('id', new_id)

            # Update icon in cTextureResource
            if "icon" in self.template_data and self.template_data["icon"]:
                old_icon_name = self.template_data["icon"][:-8]  # Remove .texture
                new_icon_name = self.apply_positional_replacement(old_icon_name, new_prefix)

                for obj in texture_nodes:
                    name_elem = obj.find('.//Attribute[@name="mName"]/Item')
                    if name_elem is not None and name_elem.text:
                        if name_elem.text.strip() == old_icon_name:
                            name_elem.text = new_icon_name

                            # Update ID
                            old_id = obj.get('id')
                            if old_id:
                                new_id = generate_unique_id()
                                id_mapping[old_id] = new_id
                                obj.set('id', new_id)

            # Update sprite-related IDs
            for obj in root.findall('.//Object[@type="sSpriteBasetype"]'):
                texture_item = obj.find('.//Resource[@name="texture"]/Item')
                if texture_item is not None and texture_item.text in id_mapping:
                    old_id = obj.get('id')
                    if old_id:
                        new_id = generate_unique_id()
                        id_mapping[old_id] = new_id
                        obj.set('id', new_id)
            
            for obj in root.findall('.//Object[@type="cSprite"]'):
                base_item = obj.find('.//Pointer[@name="mBase"]/Item')
                if base_item is not None and base_item.text in id_mapping:
                    old_id = obj.get('id')
                    if old_id:
                        new_id = generate_unique_id()
                        id_mapping[old_id] = new_id
                        obj.set('id', new_id)
            
            # Update all references to old IDs with new IDs
            for elem in root.iter():
                if elem.text and elem.text.strip() in id_mapping:
                    elem.text = id_mapping[elem.text.strip()]
            
            # Write back the modified XML with proper indentation
            ET.indent(tree, space='\t', level=0)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            
            return True
        
        except Exception as e:
            print(f"Error processing bundle.xml: {e}")
            return False
    
    def process_bundle_xml_vehicle(self, file_path: str, old_base: str, new_base: str):
        """Process bundle.xml for vehicle units"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Collect all existing IDs to avoid conflicts
            existing_ids = set()
            for obj in root.findall('.//Object'):
                obj_id = obj.get('id')
                if obj_id:
                    existing_ids.add(obj_id)
            for item in root.findall('.//Item'):
                if item.text and item.text.isdigit():
                    existing_ids.add(item.text)
            
            # Map old IDs to new IDs
            id_mapping = {}
            new_ids = set()

            def generate_unique_id():
                """Generate a unique random ID"""
                import random
                while True:
                    new_id = str(random.randint(9000000000, 9999999999))
                    if new_id not in existing_ids and new_id not in new_ids:
                        existing_ids.add(new_id)
                        new_ids.add(new_id)
                        return new_id

            # Pre-fetch node lists once instead of once per model/texture
            model_nodes   = root.findall('.//Object[@type="cNodeHierarchyResource"]')
            texture_nodes = root.findall('.//Object[@type="cTextureResource"]')

            # Update cNodeHierarchyResource objects (models)
            if "models" in self.template_data:
                for model_key, model_filename in self.template_data["models"].items():
                    if not model_filename:
                        continue

                    old_model_name = model_filename[:-5]  # Remove .modl
                    new_model_name = self.apply_positional_replacement(old_model_name, new_base)

                    for obj in model_nodes:
                        name_elem = obj.find('.//Attribute[@name="mName"]/Item')
                        if name_elem is not None and name_elem.text:
                            if name_elem.text.strip() == old_model_name:
                                name_elem.text = new_model_name

                                # Update ID
                                old_id = obj.get('id')
                                if old_id:
                                    new_id = generate_unique_id()
                                    id_mapping[old_id] = new_id
                                    obj.set('id', new_id)

            # Also check for bgf_name
            if "bgf_name" in self.template_data:
                old_bgf = self.template_data["bgf_name"]
                new_bgf = self.apply_positional_replacement(old_bgf, new_base)

                for obj in model_nodes:
                    name_elem = obj.find('.//Attribute[@name="mName"]/Item')
                    if name_elem is not None and name_elem.text:
                        if name_elem.text.strip() == old_bgf:
                            name_elem.text = new_bgf

                            # Update ID
                            old_id = obj.get('id')
                            if old_id:
                                new_id = generate_unique_id()
                                id_mapping[old_id] = new_id
                                obj.set('id', new_id)

            # Update cTextureResource objects (textures)
            if "textures" in self.template_data:
                for texture_key, texture_filename in self.template_data["textures"].items():
                    if not texture_filename:
                        continue

                    old_texture_name = texture_filename[:-8]  # Remove .texture

                    # Skip excluded textures
                    if old_texture_name in self.EXCLUDE_TEXTURES:
                        continue

                    new_texture_name = self.apply_positional_replacement(old_texture_name, new_base)

                    for obj in texture_nodes:
                        name_elem = obj.find('.//Attribute[@name="mName"]/Item')
                        if name_elem is not None and name_elem.text:
                            if name_elem.text.strip() == old_texture_name:
                                name_elem.text = new_texture_name

                                # Update ID
                                old_id = obj.get('id')
                                if old_id:
                                    new_id = generate_unique_id()
                                    id_mapping[old_id] = new_id
                                    obj.set('id', new_id)

            # Update icon in cTextureResource
            if "icon" in self.template_data and self.template_data["icon"]:
                old_icon_name = self.template_data["icon"][:-8]  # Remove .texture
                new_icon_name = self.apply_positional_replacement(old_icon_name, new_base)

                for obj in texture_nodes:
                    name_elem = obj.find('.//Attribute[@name="mName"]/Item')
                    if name_elem is not None and name_elem.text:
                        if name_elem.text.strip() == old_icon_name:
                            name_elem.text = new_icon_name
                            
                            # Update ID
                            old_id = obj.get('id')
                            if old_id:
                                new_id = generate_unique_id()
                                id_mapping[old_id] = new_id
                                obj.set('id', new_id)
            
            # Update sprite-related IDs
            for obj in root.findall('.//Object[@type="sSpriteBasetype"]'):
                texture_item = obj.find('.//Resource[@name="texture"]/Item')
                if texture_item is not None and texture_item.text in id_mapping:
                    old_id = obj.get('id')
                    if old_id:
                        new_id = generate_unique_id()
                        id_mapping[old_id] = new_id
                        obj.set('id', new_id)
            
            for obj in root.findall('.//Object[@type="cSprite"]'):
                base_item = obj.find('.//Pointer[@name="mBase"]/Item')
                if base_item is not None and base_item.text in id_mapping:
                    old_id = obj.get('id')
                    if old_id:
                        new_id = generate_unique_id()
                        id_mapping[old_id] = new_id
                        obj.set('id', new_id)
            
            # Update all references to old IDs with new IDs
            for elem in root.iter():
                if elem.text and elem.text.strip() in id_mapping:
                    elem.text = id_mapping[elem.text.strip()]
            
            # Write back the modified XML with proper indentation
            ET.indent(tree, space='\t', level=0)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            
            return True
        
        except Exception as e:
            print(f"Error processing bundle.xml: {e}")
            return False


if __name__ == "__main__":
    app = UnitEditorApp()
    app.mainloop()