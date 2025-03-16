import ttkbootstrap as ttk
from tkinter import filedialog
import pandas as pd
import os
import re
import shutil
import time
from pathlib import Path
from typing import List, Tuple


class FileSorterApp:
    def __init__(self):
        self.app = ttk.Window(themename="litera")
        self.app.geometry("500x370")
        self.app.title("File Filter")

        # Initialize variables
        self.path_entry = None
        self.error_label = None
        self.dataframe = None  # Placeholder for DataFrame
        self.title_label = None

        # Filtering options
        self.data_type_var = None
        self.size_var = None
        self.create_date_var = None
        self.create_time_var = None
        self.access_date_var = None

        # Ranges for filtering
        self.creation_range = None
        self.creation_time_range = None
        self.modification_range = None
        self.access_range = None
        self.min_size, self.max_size = None, None
        self.data_types = None

        self.first_screen()  # Start with first screen

    def first_screen(self):
        """Initial screen for selecting folder path."""
        self.clear_screen()

        ttk.Label(self.app, text="Path Configuration", font=("Arial", 20, "bold")).pack(pady=20)

        path_frame = ttk.Frame(self.app)
        path_frame.pack(pady=10, padx=20, fill="x")

        ttk.Label(path_frame, text="Choose or insert the path of the folder to continue.", font=("Arial", 12, "bold")).pack()

        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        browse_button = ttk.Button(path_frame, text="Browse", command=self.browse_folder)
        browse_button.pack(side="right")

        self.error_label = ttk.Label(self.app, text="Invalid path! Please check the path and try again.",
                                     foreground="red", font=("Arial", 12, "bold"), bootstyle="danger")

        self.path_entry.bind('<KeyRelease>', lambda e: self.validate_path())

        submit_button = ttk.Button(self.app, text="Submit", command=self.on_submit, bootstyle="success")
        submit_button.pack(pady=20)

        self.app.mainloop()

    def browse_folder(self):
        """Opens a file dialog for folder selection."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder_selected)

    def validate_path(self):
        """Validates the path entry."""
        path = self.path_entry.get()
        if path and os.path.exists(path):
            self.path_entry.configure(bootstyle="success")
            self.error_label.pack_forget()
            return True
        else:
            self.path_entry.configure(bootstyle="default")
            self.error_label.pack(pady=(0, 10))
            return False

    def create_dataset(self, path: str) -> pd.DataFrame:
        """
        Gets all files in the selected folder and their metadata.
        Returns a DataFrame containing:
            - Path
            - File Name
            - Creation Time
            - Last Modified Time
            - Last Accessed Time
            - Size (MB)
            - File Type
        """
        files_data: List[Tuple[str, str, str, str, float, str]] = []

        def get_file_info(file_path: str) -> Tuple[str, str, str, float, str]:
            file = Path(file_path)
            file_size = round(file.stat().st_size / (1024 * 1024), 2)  # Convert bytes to MB
            creation_date = time.ctime(file.stat().st_ctime)
            modification_time = time.ctime(file.stat().st_mtime)
            access_time = time.ctime(file.stat().st_atime)
            file_type = file.suffix if file.suffix else "Unknown"
            return creation_date, modification_time, access_time, file_size, file_type

        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                creation_time, modification_time, access_time, file_size, file_type = get_file_info(file_path)
                files_data.append((file_path, file, creation_time, modification_time, access_time, file_size, file_type))

        df = pd.DataFrame(files_data, columns=["Path", "File Name", "Creation Date", "Last Modified Time", "Last Accessed Time", "Size (MB)", "File Type"])

        # Convert time strings to datetime
        for col in ["Creation Date", "Last Modified Time", "Last Accessed Time"]:
            df[col] = pd.to_datetime(df[col], format="%a %b %d %H:%M:%S %Y", errors="coerce")

        # Add "Creation Time" column
        df["Creation Time"] = df["Creation Date"].dt.time

        # Fill NaN values with "Unknown"
        df = df.fillna("Unknown")

        return df

    def on_submit(self):
        """Handles submit action - validates path, processes files, and transitions to the second screen."""
        path = self.path_entry.get()
        if self.validate_path():
            self.dataframe = self.create_dataset(path)  # Create DataFrame

            def range_date(column: str):
                date_range = sorted(self.dataframe[column].unique())
                return [date.strftime('%Y-%m-%d') for date in date_range]

            def range_time(column: str):
                time_range = sorted(self.dataframe[column].unique())
                return [date.strftime('%H:%M:%S') for date in time_range]

            self.creation_range = range_date("Creation Date")
            self.creation_time_range = range_time("Creation Time")
            self.modification_range = range_date("Last Modified Time")
            self.access_range = range_date("Last Accessed Time")
            self.min_size, self.max_size = self.dataframe["Size (MB)"].min(), self.dataframe["Size (MB)"].max()
            self.data_types = self.dataframe["File Type"].unique().tolist()
            self.data_types.insert(0, ".all")

            self.second_screen()  # Move to second screen
        else:
            self.error_label.pack(pady=(0, 10))

    def filter_files(self):
        """Filters files based on selected options and changes the user's screen."""
        def filter_int(text):
            match = re.search(r'\d+', text)
            return int(match.group()) if match else None

        # -------------- ERRORS -------------- #
        def reset_label():
            self.title_label.config(text="File Filter", foreground="black", font=("Arial", 16, "bold"))

        if not any([self.data_type_var.get(), self.size_var.get(), self.create_date_var.get(), self.create_time_var.get(), self.access_date_var.get()]):
            self.title_label.config(text="No options selected", foreground="red", font=("Arial", 16, "bold"))
            self.title_label.after(2000, reset_label)
        else:
            self.filtered_df = self.dataframe.copy()

            # ------- Filter by Data Type ------- #
            if self.data_type_var.get():
                selected_type = self.data_type_combobox.get()
                if selected_type != ".all":
                    self.filtered_df = self.filtered_df[self.filtered_df["File Type"] == selected_type]

            # ------- Filter by Size ------- #
            if self.size_var.get():
                size_min = filter_int(self.size_min.get())
                size_max = filter_int(self.size_max.get())
                if size_min is not None and size_max is not None:
                    self.filtered_df = self.filtered_df[
                        (self.filtered_df["Size (MB)"] >= size_min) & (self.filtered_df["Size (MB)"] <= size_max)
                    ]

            # ------- Filter by Creation Date ------- #
            if self.create_date_var.get():
                creation_min = pd.to_datetime(self.create_frame.min_box.get())
                creation_max = pd.to_datetime(self.create_frame.max_box.get())
                if creation_min and creation_max:
                    self.filtered_df = self.filtered_df[
                        (self.filtered_df["Creation Date"] >= creation_min) & (self.filtered_df["Creation Date"] <= creation_max)
                    ]

            # ------- Filter by Creation Time ------- #
            if self.create_time_var.get():
                time_min = pd.to_datetime(self.time_frame.min_box.get(), format="%H:%M:%S").time()
                time_max = pd.to_datetime(self.time_frame.max_box.get(), format="%H:%M:%S").time()
                if time_min and time_max:
                    self.filtered_df = self.filtered_df[
                        (self.filtered_df["Creation Time"] >= time_min) & (self.filtered_df["Creation Time"] <= time_max)
                    ]

            # ------- Filter by Access Date ------- #
            if self.access_date_var.get():
                access_min = pd.to_datetime(self.access_frame.min_box.get())
                access_max = pd.to_datetime(self.access_frame.max_box.get())
                if access_min and access_max:
                    self.filtered_df = self.filtered_df[
                        (self.filtered_df["Last Accessed Time"] >= access_min) & (self.filtered_df["Last Accessed Time"] <= access_max)
                    ]

            self.filtered_df = self.filtered_df.reset_index(drop=True)

            self.third_screen()

    def second_screen(self):
        """Second screen to display processed file data."""
        self.clear_screen()

        # -------------------- INITIAL INTERFACE --------------------
        self.title_label = ttk.Label(self.app, text="File Filter", font=("Arial", 16, "bold"))
        self.title_label.pack(pady=10)

        header_frame = ttk.Frame(self.app)
        header_frame.pack(fill="x", padx=20, pady=5)

        instruction_label = ttk.Label(header_frame, text="Choose categories to enable filtering:", font=("Arial", 12, "bold"))
        instruction_label.pack(side="left")

        options_frame = ttk.Frame(self.app)
        options_frame.pack(anchor="w", padx=20)

        # ---------------- DATA TYPE SORTING OPTIONS -----------------
        self.data_type_var = ttk.BooleanVar()
        data_frame_check = ttk.Checkbutton(options_frame, text="Filter by Data Type", variable=self.data_type_var, command=lambda: self.toggle_datatype_inputs(self.data_type_var, self.data_type_frame))
        data_frame_check.grid(row=0, column=0, sticky="w", pady=2)

        self.data_type_frame = ttk.Frame(self.app)
        self.data_type_combobox = ttk.Combobox(self.data_type_frame, values=self.data_types, width=15) 
        self.data_type_combobox.insert(0, ".all")  
        self.data_type_combobox.grid(row=0, column=1, pady=2)

        # ---------------- SIZE SORTING OPTIONS -----------------
        self.size_var = ttk.BooleanVar()
        size_check = ttk.Checkbutton(options_frame, text="Filter by Size", variable=self.size_var, command=self.toggle_size_inputs)
        size_check.grid(row=1, column=0, sticky="w", pady=2)

        self.size_frame = ttk.Frame(self.app)
        self.size_min = ttk.Entry(self.size_frame, width=10)
        self.size_max = ttk.Entry(self.size_frame, width=10)
        self.size_min.insert(0, f"Min: {self.min_size} MB")
        self.size_max.insert(0, f"Max: {self.max_size} MB")
        size_dash = ttk.Label(self.size_frame, text=" - ")

        # ---------------- DATE SORTING OPTIONS -----------------
        self.create_date_var = ttk.BooleanVar()
        create_check = ttk.Checkbutton(options_frame, text="Filter by Creation Date", variable=self.create_date_var, command=lambda: self.toggle_date_inputs(self.create_date_var, self.create_frame, self.creation_range))
        create_check.grid(row=2, column=0, sticky="w", pady=2)

        self.create_frame = ttk.Frame(self.app)
        self.creation_min = ttk.Combobox(self.create_frame, values=self.creation_range, width=15)
        self.creation_max = ttk.Combobox(self.create_frame, values=self.creation_range, width=15)
        create_dash = ttk.Label(self.create_frame, text=" - ")

        # ---------------- TIME SORTING OPTIONS -----------------
        self.create_time_var = ttk.BooleanVar()
        time_check = ttk.Checkbutton(options_frame, text="Filter by Creation Time", variable=self.create_time_var, command=lambda: self.toggle_date_inputs(self.create_time_var, self.time_frame, self.creation_time_range))
        time_check.grid(row=3, column=0, sticky="w", pady=2)

        self.time_frame = ttk.Frame(self.app)
        self.time_min = ttk.Combobox(self.time_frame, values=self.creation_time_range, width=15)
        self.time_max = ttk.Combobox(self.time_frame, values=self.creation_time_range, width=15)
        create_dash = ttk.Label(self.create_frame, text=" - ")

        # ---------------- ACCESS DATE SORTING OPTIONS -----------------
        self.access_date_var = ttk.BooleanVar()
        access_check = ttk.Checkbutton(options_frame, text="Filter by Access Date", variable=self.access_date_var, command=lambda: self.toggle_date_inputs(self.access_date_var, self.access_frame, self.access_range))
        access_check.grid(row=4, column=0, sticky="w", pady=2)

        self.access_frame = ttk.Frame(self.app)
        self.access_min = ttk.Combobox(self.access_frame, values=self.access_range, width=15)
        self.access_max = ttk.Combobox(self.access_frame, values=self.access_range, width=15)
        access_dash = ttk.Label(self.access_frame, text=" - ")

        # Submit Button
        submit_button = ttk.Button(header_frame, text="Submit", command=self.filter_files, bootstyle="success")
        submit_button.pack(side="right")

    def toggle_datatype_inputs(self, var, frame):
        """Show/hide data type input fields when checkbox is clicked."""
        if var.get():
            frame.pack(anchor="w", padx=40, pady=2)
        else:
            frame.pack_forget()
        frame.update_idletasks()

    def toggle_size_inputs(self):
        """Show/hide size input fields when checkbox is clicked."""
        if self.size_var.get():
            self.size_frame.pack(anchor="w", padx=40, pady=2)
            self.size_min.pack(side="left")
            self.size_max.pack(side="right")
            if not hasattr(self, "size_label"):
                self.size_label = ttk.Label(self.size_frame, text=" - ")
                self.size_label.pack(side="left")
        else:
            self.size_frame.pack_forget()
        self.size_frame.update_idletasks()

    def toggle_date_inputs(self, var, frame, date_range):
        """Show/hide date input fields when checkbox is clicked."""
        if var.get():
            frame.pack(anchor="w", padx=40, pady=2)
            if not hasattr(frame, "min_box"):
                frame.min_box = ttk.Combobox(frame, values=date_range, width=15)
                frame.max_box = ttk.Combobox(frame, values=date_range, width=15)
                frame.min_box.current(0)  # Set to first date
                frame.max_box.current(len(date_range) - 1)  # Set to last date
                frame.label = ttk.Label(frame, text=" - ")
                frame.min_box.pack(side="left")
                frame.label.pack(side="left")
                frame.max_box.pack(side="right")
        else:
            frame.pack_forget()
        frame.update_idletasks()

    def save_files(self, filtered_dataset, save_path):
        """Saves filtered dataset to specified path."""
        if self.validate_path():
            for index, row in filtered_dataset.iterrows():
                try: 
                  source_path = row["Path"]
                  destination_path = os.path.join(save_path, os.path.basename(source_path))
                  shutil.copy2(source_path, destination_path)
                except shutil.SameFileError:
                  pass
            self.app.destroy()

    def third_screen(self):
        """Third screen to display filtered file data."""
        self.clear_screen()

        ttk.Label(self.app, text="Save Path Configuration", font=("Arial", 20, "bold")).pack(pady=20)

        path_frame = ttk.Frame(self.app)
        path_frame.pack(pady=10, padx=20, fill="x")

        ttk.Label(path_frame, text="Choose the path to save your filtered files.", font=("Arial", 12, "bold")).pack()

        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        browse_button = ttk.Button(path_frame, text="Browse", command=self.browse_folder)
        browse_button.pack(side="right")

        total_filtered = len(self.filtered_df)
        self.file_count_label = ttk.Label(self.app, text=f"Number of files to save: {total_filtered}", font=("Arial", 12, "bold"))
        self.file_count_label.pack(pady=10)

        self.error_label = ttk.Label(self.app, text="Invalid path",
                                     foreground="red", font=("Arial", 12, "bold"), bootstyle="danger")

        self.path_entry.bind('<KeyRelease>', lambda e: self.validate_path())

        submit_button = ttk.Button(self.app, text="Submit", command=lambda: self.save_files(self.filtered_df, self.path_entry.get()), bootstyle="success")
        submit_button.pack(pady=20)

        close_button = ttk.Button(self.app, text="Close", command=self.app.destroy, bootstyle="danger")
        close_button.pack(pady=10)

        self.app.mainloop()

    def clear_screen(self):
        """Clears all widgets from the screen."""
        for widget in self.app.winfo_children():
            widget.destroy()


if __name__ == "__main__": 
    FileSorterApp()