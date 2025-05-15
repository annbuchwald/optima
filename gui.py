import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import os
import optima_backend  # import the backend

class OptimaConfigurator(tk.Tk):
    def __init__(self, test_mode=False):
        super().__init__()

        if test_mode:
            self.withdraw()
        self.title("Optima - Complexity Analyzer Configuration")
        self.geometry("700x600")

        self.analysis_scope = tk.StringVar(value="file")
        self.target_path = tk.StringVar()
        self.max_complexity = tk.StringVar(value="10")
        self.file_extensions = tk.StringVar()
        self.include_lines = tk.BooleanVar()
        self.selected_lines = (None, None)  # new: for selected line range

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        target_frame = ttk.LabelFrame(main_frame, text="Analysis Scope", padding="10")
        target_frame.pack(fill=tk.X, pady=5)

        ttk.Radiobutton(target_frame, text="Single File", variable=self.analysis_scope, value="file", command=self._update_browse_button).grid(row=0, column=0, padx=5, sticky="w")
        ttk.Radiobutton(target_frame, text="Directory", variable=self.analysis_scope, value="directory", command=self._update_browse_button).grid(row=0, column=1, padx=5, sticky="w")

        ttk.Label(target_frame, text="Path:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.path_entry = ttk.Entry(target_frame, textvariable=self.target_path, width=50)
        self.path_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.browse_button = ttk.Button(target_frame, text="Browse File...", command=self._browse)
        self.browse_button.grid(row=1, column=2, padx=5, pady=5)

        self.view_button = ttk.Button(target_frame, text="View File", command=self._view_file)
        self.view_button.grid(row=1, column=3, padx=5, pady=5)

        self.line_select_button = ttk.Button(target_frame, text="Select Lines", command=self._select_lines_window)
        self.line_select_button.grid(row=1, column=4, padx=5, pady=5)

        target_frame.columnconfigure(1, weight=1)

        params_frame = ttk.LabelFrame(main_frame, text="Analysis Parameters", padding="10")
        params_frame.pack(fill=tk.X, pady=5)

        ttk.Label(params_frame, text="Maximum Cyclomatic Complexity:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        vcmd = (self.register(self._validate_complexity), "%P")
        self.complexity_spinbox = ttk.Spinbox(params_frame, from_=1, to=1000, textvariable=self.max_complexity, width=5, validate="key", validatecommand=vcmd)
        self.complexity_spinbox.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(params_frame, text="Function Name Regex Patterns (one per line):").grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.regex_text = scrolledtext.ScrolledText(params_frame, height=5, width=60)
        self.regex_text.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.regex_text.insert(tk.END, ".*")

        ttk.Label(params_frame, text="File Extensions (comma-separated, e.g., .py,.java):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(params_frame, textvariable=self.file_extensions, width=40).grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        ttk.Checkbutton(params_frame, text="Include function line numbers in output", variable=self.include_lines).grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        params_frame.columnconfigure(1, weight=1)

        action_frame = ttk.Frame(main_frame, padding="10")
        action_frame.pack(fill=tk.X, pady=10)

        self.run_button = ttk.Button(action_frame, text="Run Analysis", command=self._run_analysis)
        self.run_button.pack(side=tk.RIGHT, padx=5)

        ttk.Button(action_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT)

        output_frame = ttk.LabelFrame(main_frame, text="Output/Status", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.output_text = scrolledtext.ScrolledText(output_frame, height=10, state=tk.DISABLED, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        self.test_output = []

    def _validate_complexity(self, P):
        return P.isdigit() and 1 <= int(P) <= 1000 or P == ""

    def _update_browse_button(self):
        if self.analysis_scope.get() == "file":
            self.browse_button.config(text="Browse File...")
            self.view_button.config(state="normal")
            self.line_select_button.config(state="normal")
        else:
            self.browse_button.config(text="Browse Dir...")
            self.view_button.config(state="disabled")
            self.line_select_button.config(state="disabled")

    def _browse(self):
        if self.analysis_scope.get() == "file":
            filepath = filedialog.askopenfilename()
            if filepath:
                self.target_path.set(filepath)
        else:
            dirpath = filedialog.askdirectory()
            if dirpath:
                self.target_path.set(dirpath)

        self._update_browse_button()

    def _view_file(self):
        filepath = self.target_path.get()
        if not filepath or not os.path.isfile(filepath):
            messagebox.showerror("Error", "Please select a valid file first.")
            return

        try:
            with open(filepath, "r") as f:
                contents = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")
            return

        win = tk.Toplevel(self)
        win.title("View File Contents")
        win.geometry("800x600")

        text = scrolledtext.ScrolledText(win, wrap=tk.NONE)
        text.insert(tk.END, contents)
        text.config(state=tk.DISABLED)
        text.pack(fill=tk.BOTH, expand=True)

    def _select_lines_window(self):
        filepath = self.target_path.get()
        if not filepath or not os.path.isfile(filepath):
            messagebox.showerror("Error", "Please select a valid file first.")
            return

        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")
            return

        window = tk.Toplevel(self)
        window.title("Select Lines")
        window.geometry("700x500")

        ttk.Label(window, text="Use your mouse to select the lines of interest.").pack(pady=5)

        text = tk.Text(window, wrap=tk.NONE)
        text.pack(fill=tk.BOTH, expand=True)
        for i, line in enumerate(lines, 1):
            text.insert(tk.END, f"{i:4d}: {line}")

        def set_lines():
            try:
                index_start = text.index(tk.SEL_FIRST)
                index_end = text.index(tk.SEL_LAST)
                start_line = int(index_start.split(".")[0])
                end_line = int(index_end.split(".")[0])
                self.selected_lines = (start_line, end_line)
                messagebox.showinfo("Selection Saved", f"Lines {start_line} to {end_line} selected.")
                window.destroy()
            except tk.TclError:
                messagebox.showerror("Error", "Please select some lines first.")

        ttk.Button(window, text="Save Selection", command=set_lines).pack(pady=5)

    def _display_output(self, message):
        self.test_output.append(message)
        if hasattr(self, 'output_text') and self.output_text.winfo_exists():
            self.output_text.config(state=tk.NORMAL)
            self.output_text.insert(tk.END, message + "\n")
            self.output_text.see(tk.END)
            self.output_text.config(state=tk.DISABLED)
            self.update_idletasks()

    def _run_analysis(self, test_params=None):
        if test_params:
            scope = test_params.get("scope", "file")
            path = test_params.get("path", "")
            max_comp_str = str(test_params.get("max_complexity", "10"))
            regex_patterns_str = "\n".join(test_params.get("regex_patterns", [".*"]))
            extensions_str = ",".join(test_params.get("extensions", []))
            include_lines_flag = test_params.get("include_lines", False)
        else:
            scope = self.analysis_scope.get()
            path = self.target_path.get().strip()
            max_comp_str = self.max_complexity.get()
            regex_patterns_str = self.regex_text.get("1.0", tk.END).strip()
            extensions_str = self.file_extensions.get().strip()
            include_lines_flag = self.include_lines.get()

        self.test_output = []

        if not path:
            message = "Error: Please select a file or directory path."
            if not test_params:
                messagebox.showerror("Error", message)
            self._display_output(message)
            return

        if not max_comp_str or not max_comp_str.isdigit():
            message = "Error: Please enter a valid integer for Maximum Complexity."
            if not test_params:
                messagebox.showerror("Error", message)
            self._display_output(message)
            return

        max_comp = int(max_comp_str)

        if not regex_patterns_str:
            message = "Error: Please provide at least one regex pattern (e.g., .*)."
            if not test_params:
                messagebox.showerror("Error", message)
            self._display_output(message)
            return

        regex_patterns_list = [p.strip() for p in regex_patterns_str.split("\n") if p.strip()]
        extensions_list = [
            ext.strip() if ext.strip().startswith(".") else "." + ext.strip()
            for ext in extensions_str.split(",") if ext.strip()
        ] if extensions_str else []

        if hasattr(self, 'output_text') and self.output_text.winfo_exists():
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.config(state=tk.DISABLED)

        self._display_output(f"Starting analysis ({scope})...")
        self._display_output(f"Path: {path}")
        self._display_output(f"Max Complexity: {max_comp}")
        self._display_output(f"Regex Patterns: {regex_patterns_list}")
        self._display_output(f"Extensions: {extensions_list if extensions_list else 'All'}")
        self._display_output(f"Include Lines: {include_lines_flag}")
        self._display_output("-" * 20)

        try:
            if scope == "file":
                if not os.path.isfile(path):
                    message = f"Error: File not found: {path}"
                    if not test_params:
                        messagebox.showerror("Error", message)
                    self._display_output(message)
                    return
                analysis_result = optima_backend.analyze_file(path, max_comp, regex_patterns_list)
                result = analysis_result.problematic_functions
            else:
                if not os.path.isdir(path):
                    message = f"Error: Directory not found: {path}"
                    if not test_params:
                        messagebox.showerror("Error", message)
                    self._display_output(message)
                    return
                analysis_result = optima_backend.analyze_directory(path, max_comp, regex_patterns_list, extensions_list)
                result = analysis_result.problematic_functions

            str = ""
            if not result:
                self._display_output("No problematic functions found matching the criteria.")
            else:
                self._display_output(f"Found {len(result)} problematic function(s):")
                for r in result:
                    if include_lines_flag:
                        self._display_output(f"  - {r.filepath} | {r.func_name} | Complexity: {r.complexity} | Lines: {r.line_begin}-{r.line_end}")
                        str += f"File: {r.filepath}, Function: {r.func_name}, Complexity: {r.complexity}, Lines: {r.line_begin}-{r.line_end}\n"
                    else:
                        self._display_output(f"  - {r.filepath} | {r.func_name} | Complexity: {r.complexity}")
                        str += f"File: {r.filepath}, Function: {r.func_name}, Complexity: {r.complexity}\n"

                    if self.selected_lines != (None, None):
                        line_start, line_end = self.selected_lines
                        try:
                            with open(r.filepath, "r") as f:
                                file_lines = f.readlines()[line_start - 1:line_end]
                                str += "".join(file_lines) + "\n"
                        except Exception as e:
                            str += f"[Error extracting selected lines: {e}]\n"
                    else:
                        str += f"{optima_backend.extract_function_code(r.filepath, r.line_begin, r.line_end)}\n"

                    self._display_output(str)

            language = optima_backend.detect_language(path)
            question = f"Here is a function written in {language}. Please analyze and suggest possible improvements in:\n{str}"
            self._display_output(f"Language: {language}")
            self._display_output("-" * 20)
            self._display_output("Analysis complete.")
            self._display_output("-" * 20)
            self._display_output(f"AI Suggestions:\n{optima_backend.handle_user_question(question)}")

        except Exception as e:
            error_message = f"An unexpected error occurred during analysis: {e}"
            if not test_params:
                messagebox.showerror("Analysis Error", error_message)
            self._display_output(f"Error: {error_message}")

def run_test(test_params):
    if not os.path.exists("optima_backend.py"):
        print("Error: optima_backend.py not found.")
        return ["Error: optima_backend.py not found."]

    app = OptimaConfigurator(test_mode=True)
    app._run_analysis(test_params=test_params)
    app.destroy()
    return app.test_output

if __name__ == "__main__":
    if not os.path.exists("optima_backend.py"):
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Startup Error", "Critical component optima_backend.py not found. Application cannot start.")
            root.destroy()
        except tk.TclError:
            pass
        exit(1)

    app = OptimaConfigurator()
    app.mainloop()
