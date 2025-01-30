import os
import shutil
import json
import logging
from tkinter import Tk, Button, Label, filedialog, messagebox, ttk, Checkbutton, BooleanVar, Entry, StringVar, Frame, Listbox, MULTIPLE
from ttkbootstrap import Style
from tkinter import scrolledtext
from collections import defaultdict
from datetime import datetime, timedelta
from PIL import Image, ImageTk

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="file_organizer.log",
)

# Load configuration from JSON file
CONFIG_FILE = "config.json"

def load_config():
    """Load file types and folders from the config file."""
    if not os.path.exists(CONFIG_FILE):
        # Default configuration
        default_config = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
            "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".csv"],
            "Videos": [".mp4", ".mkv", ".mov", ".avi", ".flv"],
            "Music": [".mp3", ".wav", ".aac", ".flac"],
            "Archives": [".zip", ".rar", ".tar", ".gz"],
            "Code": [".py", ".js", ".html", ".css", ".java", ".cpp"],
            "Executables": [".exe", ".msi", ".dmg"],
            "Others": [],
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config
    else:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)

# Track file movements for undo functionality
file_movements = []


def organize_files(directories, progress_bar, log_text, file_count_label, handle_duplicates, custom_rules, rename_pattern, search_query , compress_files):
    """Organize files in the specified directories."""
    global file_movements
    file_movements.clear()  # Reset undo history
    file_types = load_config()
    total_files = sum(len([f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)) and (not search_query.get() or search_query.get().lower() in f.lower())]) for d in directories)
    organized_files = 0

    for directory in directories:
        # Create folders for each file type
        for folder_name in file_types.keys():
            folder_path = os.path.join(directory, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

        # Organize files
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            # Skip directories and files that don't match the search query
            if os.path.isdir(file_path) or (search_query.get() and search_query.get().lower() not in filename.lower()):
                continue

            # Get the file extension
            _, file_extension = os.path.splitext(filename)
            file_extension = file_extension.lower()

            # Apply custom rules
            if custom_rules.get():
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_age > timedelta(days=30):
                    destination_folder = os.path.join(directory, "Archive")
                    if not os.path.exists(destination_folder):
                        os.makedirs(destination_folder)
                    destination_path = os.path.join(destination_folder, filename)
                    shutil.move(file_path, destination_path)
                    file_movements.append((destination_path, file_path))  # Track for undo
                    log_text.insert("end", f"Moved (Custom Rule): {filename} -> Archive\n")
                    logging.info(f"Moved (Custom Rule): {filename} -> Archive")
                    organized_files += 1
                    continue

            # Find the appropriate folder for the file
            moved = False
            for folder_name, extensions in file_types.items():
                if file_extension in extensions:
                    destination_folder = os.path.join(directory, folder_name)
                    destination_path = os.path.join(destination_folder, filename)

                    # Handle duplicate files
                    if os.path.exists(destination_path):
                        if handle_duplicates.get():
                            base, ext = os.path.splitext(filename)
                            counter = 1
                            while os.path.exists(destination_path):
                                new_filename = f"{base} ({counter}){ext}"
                                destination_path = os.path.join(destination_folder, new_filename)
                                counter += 1
                            filename = new_filename

                    # Apply bulk renaming
                    if rename_pattern.get():
                        base, ext = os.path.splitext(filename)
                        new_filename = f"{rename_pattern.get()}_{organized_files + 1}{ext}"
                        destination_path = os.path.join(destination_folder, new_filename)

                    shutil.move(file_path, destination_path)
                    file_movements.append((destination_path, file_path))  # Track for undo
                    log_text.insert("end", f"Moved: {filename} -> {folder_name}\n")
                    logging.info(f"Moved: {filename} -> {folder_name}")
                    organized_files += 1
                    moved = True
                    break

            # If the file type is not recognized, move it to the "Others" folder
            if not moved:
                destination_folder = os.path.join(directory, "Others")
                destination_path = os.path.join(destination_folder, filename)

                # Handle duplicate files
                if os.path.exists(destination_path):
                    if handle_duplicates.get():
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(destination_path):
                            new_filename = f"{base} ({counter}){ext}"
                            destination_path = os.path.join(destination_folder, new_filename)
                            counter += 1
                        filename = new_filename

                shutil.move(file_path, destination_path)
                file_movements.append((destination_path, file_path))  # Track for undo
                log_text.insert("end", f"Moved: {filename} -> Others\n")
                logging.info(f"Moved: {filename} -> Others")
                organized_files += 1

            # Update progress bar
            progress_bar["value"] = (organized_files / total_files) * 100
            progress_bar.update()

    # Update file count label
    file_count_label.config(text=f"Files Organized: {organized_files}/{total_files}")
    logging.info("File organization complete!")
    messagebox.showinfo("Success", "Files organized successfully!")

def undo_last_action(directories, log_text, file_count_label):
    """Undo the last file organization action."""
    global file_movements
    if not file_movements:
        messagebox.showinfo("Info", "No actions to undo.")
        return

    for destination, source in reversed(file_movements):
        shutil.move(destination, source)
        log_text.insert("end", f"Undo: Moved back {os.path.basename(destination)} -> {os.path.dirname(source)}\n")
        logging.info(f"Undo: Moved back {os.path.basename(destination)} -> {os.path.dirname(source)}")

    file_movements.clear()
    file_count_label.config(text="Files Organized: 0/0")
    messagebox.showinfo("Success", "Undo completed!")

def add_directory(directory_listbox):
    directory = filedialog.askdirectory()
    if directory:  # Ensure a directory was selected
        directory_listbox.insert("end", directory)




def remove_directory(directory_listbox):
    selected_indices = directory_listbox.curselection()
    for index in reversed(selected_indices):  # Reverse to avoid shifting issues
        directory_listbox.delete(index)


def select_directories(directory_listbox, progress_bar, log_text, file_count_label, handle_duplicates, custom_rules, rename_pattern, search_query, compress_files):
    directories = [directory_listbox.get(i) for i in range(directory_listbox.size())]
    if not directories:
        messagebox.showwarning("No Directories Selected", "Please add at least one directory to organize.")
        return

    # Call the file organization function
    organize_files(directories, progress_bar, log_text, file_count_label, handle_duplicates, custom_rules, rename_pattern, search_query, compress_files)


# GUI Setup
def create_gui():
    """Create an enhanced GUI for the file organizer."""
    style = Style(theme="cosmo")  # Use a modern theme
    root = style.master
    root.title("File Organizer")
    root.geometry("800x600")

    # Dark mode toggle
    dark_mode = BooleanVar()
    def toggle_dark_mode():
        style.theme_use("darkly" if dark_mode.get() else "cosmo")

    Checkbutton(root, text="Dark Mode", variable=dark_mode, command=toggle_dark_mode).pack(pady=5)

    # Handle duplicates toggle
    handle_duplicates = BooleanVar()
    Checkbutton(root, text="Handle Duplicates", variable=handle_duplicates).pack(pady=5)

    # Custom rules toggle
    custom_rules = BooleanVar()
    Checkbutton(root, text="Apply Custom Rules (Move files older than 30 days to Archive)", variable=custom_rules).pack(pady=5)

    # Bulk renaming
    rename_pattern = StringVar()
    Label(root, text="Bulk Rename Pattern:").pack(pady=5)
    Entry(root, textvariable=rename_pattern).pack(pady=5)

    # File search
    search_query = StringVar()
    Label(root, text="Search Files:").pack(pady=5)
    Entry(root, textvariable=search_query).pack(pady=5)

    # Directory selection
    directory_frame = Frame(root)
    directory_frame.pack(pady=10)

    directory_listbox = Listbox(directory_frame, selectmode=MULTIPLE, width=50, height=5)
    directory_listbox.pack(side="left", fill="y")

    scrollbar = ttk.Scrollbar(directory_frame, orient="vertical", command=directory_listbox.yview)
    scrollbar.pack(side="right", fill="y")
    directory_listbox.config(yscrollcommand=scrollbar.set)

    Button(root, text="Add Directory", command=lambda: add_directory(directory_listbox)).pack(pady=5)
    Button(root, text="Remove Directory", command=lambda: remove_directory(directory_listbox)).pack(pady=5)

    # Header
    Label(root, text="File Organizer", font=("Helvetica", 16)).pack(pady=10)

    # Organize Button
    Button(root, text="Organize Files", command=lambda: select_directories(
        directory_listbox, progress_bar, log_text, file_count_label,
        handle_duplicates, custom_rules, rename_pattern, search_query, BooleanVar()
    )).pack(pady=10)

    # Undo Button
    Button(root, text="Undo Last Action", command=lambda: undo_last_action(directory_listbox.get(0, "end"), log_text, file_count_label)).pack(pady=10)

    # Progress Bar
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
    progress_bar.pack(pady=10)

    # File Count Label
    file_count_label = Label(root, text="Files Organized: 0/0", font=("Helvetica", 12))
    file_count_label.pack(pady=5)

    # Log Display
    log_text = scrolledtext.ScrolledText(root, width=80, height=15, wrap="word")
    log_text.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
