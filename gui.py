import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from main import scan_apps, research_web, run_llm, parse_result, install_missing_requirements
import sys
import subprocess


class AppsAnalystGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Apps Analyst - Security Scanner")
        self.root.geometry("900x700")

        # configure grid weights for sections (rows 0..4)
        # rows: 0=scan (~1/4), 1=selection (~1/3), 2=analyze button (fixed),
        # 3=results (~1/3), 4=bottom controls (fixed)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=2)
        self.root.grid_rowconfigure(1, weight=4)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_rowconfigure(3, weight=4)
        self.root.grid_rowconfigure(4, weight=0)

        self.registry_apps = []
        self.exe_apps = []
        self.selected_apps = []
        self.analysis_results = []
        self.scanning = False
        self.analyzing = False

        self.setup_ui()
    
    def setup_ui(self):
        # === SCAN SECTION ===
        scan_frame = ttk.LabelFrame(self.root, text="Step 1: Scan System", padding=10)
        # keep the scan section compact so lower sections get more vertical space
        scan_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        scan_frame.pack_propagate(False)
        # slightly larger to fit two checkboxes comfortably (trim margins)
        scan_frame.configure(height=120)
        
        # Checkboxes for scan options placed on the left, big SCAN button on the right
        self.check_registry = tk.BooleanVar(value=True)
        self.check_exe = tk.BooleanVar(value=True)

        options_frame = ttk.Frame(scan_frame)
        options_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2,6), pady=4)

        ttk.Checkbutton(options_frame, text="Scan Installed Programs (Registry)", 
               variable=self.check_registry).pack(anchor=tk.W, pady=1)
        ttk.Checkbutton(options_frame, text="Scan Executable Files (Filesystem)", 
               variable=self.check_exe).pack(anchor=tk.W, pady=1)

        # Blue scan button to the right
        scan_btn = tk.Button(scan_frame, text="SCAN", bg="#0066CC", fg="white",
                font=("Arial", 18, "bold"), command=self.on_scan_clicked,
                width=14, padx=10, pady=12)
        scan_btn.pack(side=tk.RIGHT, padx=6, pady=6)

        # status label under options (left)
        self.scan_status = tk.Label(scan_frame, text="", fg="blue")
        self.scan_status.pack(side=tk.LEFT, padx=6)
        
        # === RESULTS SECTION ===
        results_frame = ttk.LabelFrame(self.root, text="Step 2: Select Programs to Analyze", padding=10)
        results_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Search bar for filtering results
        search_frame = ttk.Frame(results_frame)
        search_frame.pack(fill=tk.X, pady=(0,6))
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0,6))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.bind('<KeyRelease>', lambda e: self.filter_results())
        clear_search_btn = ttk.Button(search_frame, text="Clear", command=self._clear_search)
        clear_search_btn.pack(side=tk.LEFT, padx=6)

        # Scrollable frame for checkboxes
        canvas = tk.Canvas(results_frame)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # place the analyze button on the main grid at row 2 so it stays visible
        # analyze button: put in its own row so it sizes to its text and centers
        analyze_container = ttk.Frame(self.root)
        analyze_container.grid(row=2, column=0, sticky="nsew", padx=10)
        analyze_container.columnconfigure(0, weight=1)
        analyze_btn = tk.Button(analyze_container, text="Analyze Selected", bg="#00AA00",
                   fg="white", font=("Arial", 12, "bold"),
                   command=self.on_analyze_clicked)
        analyze_btn.pack(anchor="center", pady=6)
        
        # === RESULTS DISPLAY ===
        results_display_frame = ttk.LabelFrame(self.root, text="Analysis Results", padding=10)
        results_display_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        results_display_frame.pack_propagate(False)
        self.results_display_frame = results_display_frame

        # adjust sizes on window resize to ensure results area >= 30% height
        self.root.bind('<Configure>', self._on_root_resize)
        
        # Larger results area and slightly larger font for readability
        self.results_text = scrolledtext.ScrolledText(results_display_frame, height=20, 
                                  wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 11))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Analysis/loading status label
        self.analysis_status = tk.Label(results_display_frame, text="", fg="blue")
        self.analysis_status.pack(anchor=tk.W)
        
        # bottom controls under results display
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        clear_btn = tk.Button(bottom_frame, text="Clear Results", 
                             command=self.on_clear_clicked, padx=15, pady=8)
        clear_btn.pack(side=tk.LEFT, padx=5)
        export_pdf_btn = tk.Button(bottom_frame, text="Export PDF", 
                       command=self.on_export_pdf, padx=15, pady=8)
        export_pdf_btn.pack(side=tk.LEFT, padx=5)
        export_csv_btn = tk.Button(bottom_frame, text="Export CSV", 
                       command=self.on_export_csv, padx=15, pady=8)
        export_csv_btn.pack(side=tk.LEFT, padx=5)
    
    def on_scan_clicked(self):
        if self.scanning:
            messagebox.showwarning("Scanning", "Scan already in progress!")
            return
        
        if not self.check_registry.get() and not self.check_exe.get():
            messagebox.showwarning("No Options", "Select at least one scan option!")
            return
        
        self.scan_status.config(text="Scanning...", fg="blue")
        self.root.update()
        
        # Run scan in thread to avoid freezing UI
        thread = threading.Thread(target=self._run_scan)
        thread.daemon = True
        thread.start()
        self.start_loading(kind="scan")
    
    def _run_scan(self):
        self.scanning = True
        try:
            all_registry, all_exe = scan_apps()
            
            # Filter based on checkboxes
            self.registry_apps = all_registry if self.check_registry.get() else []
            self.exe_apps = all_exe if self.check_exe.get() else []
            
            self.root.after(0, self._display_scan_results)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Scan Error", str(e)))
        finally:
            self.scanning = False
            self.root.after(0, lambda: self.stop_loading(kind="scan"))
    
    def _display_scan_results(self):
        # Clear previous checkboxes
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.app_vars = {}
        # Sort apps alphabetically by name for each category
        self.registry_apps = sorted(self.registry_apps, key=lambda a: (a.get('name') or '').lower())
        self.exe_apps = sorted(self.exe_apps, key=lambda a: (a.get('name') or '').lower())
        total = len(self.registry_apps) + len(self.exe_apps)
        
        if total == 0:
            self.scan_status.config(text="No apps found!", fg="red")
            return
        
        # Registry apps section
        if self.registry_apps:
            reg_label = ttk.Label(self.scrollable_frame, text="Installed Programs:", 
                                 font=("Arial", 10, "bold"))
            reg_label.pack(anchor=tk.W, pady=(10, 5))
            self.reg_label = reg_label
            for app in self.registry_apps:
                var = tk.BooleanVar()
                cb = ttk.Checkbutton(self.scrollable_frame, 
                                   text=f"  • {app['name']} ({app.get('version', 'Unknown')})",
                                   variable=var)
                cb.pack(anchor=tk.W, padx=20)
                self.app_vars[id(app)] = (var, app, cb)
        
        # EXE apps section
        if self.exe_apps:
            exe_label = ttk.Label(self.scrollable_frame, text="Executable Files:", 
                                 font=("Arial", 10, "bold"))
            exe_label.pack(anchor=tk.W, pady=(15, 5))
            self.exe_label = exe_label
            for app in self.exe_apps:
                var = tk.BooleanVar()
                cb = ttk.Checkbutton(self.scrollable_frame, 
                                   text=f"  • {app['name']} ({app.get('install_location', 'Unknown')})",
                                   variable=var)
                cb.pack(anchor=tk.W, padx=20)
                self.app_vars[id(app)] = (var, app, cb)
        
        self.scan_status.config(text=f"✓ Found {total} items", fg="green")
        # stop scan loading indicator if running
        self.stop_loading(kind="scan")
    
    def on_analyze_clicked(self):
        
        selected = [app for var, app, _ in self.app_vars.values() if var.get()]
        
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one program!")
            return
        
        self.selected_apps = selected
        self.analyzing_index = 0
        # Initialize LLM before starting analysis
        self.append_result("[*] Initializing LLM...")
        thread = threading.Thread(target=self._initialize_and_analyze)
        thread.daemon = True
        thread.start()
        self.start_loading(kind="analysis")
    
    def _initialize_and_analyze(self):
        """Initialize LLM, then proceed with analysis if successful"""
        try:
            from main import setup_llm
            if setup_llm():
                self.root.after(0, self.analyze_next)
            else:
                self.root.after(0, lambda: (
                    self.append_result("[!] Failed to initialize LLM"),
                    self.stop_loading(kind="analysis")
                ))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: (
                self.append_result(f"[!] LLM initialization error: {error_msg}"),
                self.stop_loading(kind="analysis")
            ))
    
    def analyze_next(self):
        if self.analyzing_index >= len(self.selected_apps):
            # All analyses complete; generate and display final report
            self.root.after(0, self._generate_final_report)
            return
        
        app = self.selected_apps[self.analyzing_index]
        self.append_result(f"\n[*] Analyzing: {app['name']}")
        
        thread = threading.Thread(target=self._run_analysis, args=(app,))
        thread.daemon = True
        thread.start()
    
    def _generate_final_report(self):
        """Generate a final summary report grouped by risk category."""
        self.append_result("\n")
        self.append_result("=" * 70)
        self.append_result("FINAL SECURITY REPORT")
        self.append_result("=" * 70)
        
        # Risk categories in order
        risk_labels = ["Remote Administration", "Remote File Sharing", "Keylogging", "Server Hosting"]
        risk_indices = [0, 1, 2, 3]
        
        # For each risk category, find all apps flagged as positive
        for label, idx in zip(risk_labels, risk_indices):
            flagged_apps = [
                result["name"] for result in self.analysis_results
                if result.get("risk_vector", [False]*4)[idx]
            ]
            
            # Display risk category section
            self.append_result(f"\n[{label}]")
            if flagged_apps:
                self.append_result(f"  Status: FLAGGED - {len(flagged_apps)} app(s) detected")
                for app_name in flagged_apps:
                    self.append_result(f"    • {app_name}")
            else:
                self.append_result(f"  Status: CLEAR - No apps detected with this capability")
        
        self.append_result("\n" + "=" * 70)
        self.append_result("✓ Analysis complete")
        self.append_result("=" * 70)
        self.stop_loading(kind="analysis")
    
    def _run_analysis(self, app):
        try:
            # Step: Research web
            self.root.after(0, lambda: self.append_result(f"  [*] Researching web..."))
            web_info = research_web(app)
            
            # Step: Run LLM
            self.root.after(0, lambda: self.append_result(f"  [*] Running LLM analysis..."))
            llm_result = run_llm(web_info)
            
            if llm_result:
                # Step: Parse result
                risk_vector = parse_result(llm_result)
                # store structured result for later export
                self.analysis_results.append({
                    "name": app.get('name'),
                    "web_info": web_info,
                    "llm_text": llm_result,
                    "risk_vector": risk_vector
                })
                
                # Format output
                labels = ["Remote Administration", "Remote File Sharing", "Keylogging", "Server Hosting"]
                self.root.after(0, lambda: self.append_result(f"\n  [v] Risk Assessment:"))
                for label, risk in zip(labels, risk_vector):
                    status = "YES ⚠️" if risk else "no"
                    self.root.after(0, lambda l=label, s=status: 
                                   self.append_result(f"      {l}: {s}"))
            
            self.analyzing_index += 1
            self.root.after(0, self.analyze_next)
            
        except Exception as e:
            self.root.after(0, lambda: self.append_result(f"  [!] Error: {str(e)}"))
            self.analyzing_index += 1
            self.root.after(0, self.analyze_next)
        finally:
            # ensure analysis loading indicator is active only while analyzing
            if self.analyzing_index >= len(self.selected_apps):
                self.root.after(0, lambda: self.stop_loading(kind="analysis"))
    
    def append_result(self, text):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, text + "\n")
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)
    
    def on_clear_clicked(self):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state=tk.DISABLED)
        self.analysis_results = []

    # ---------- Loading animation helpers ----------
    def start_loading(self, kind="scan"):
        # kind: "scan" or "analysis"
        if kind == "scan":
            self.loading_target = self.scan_status
        else:
            self.loading_target = self.analysis_status
        self.loading_frames = ["|", "/", "-", "\\"]
        self.loading_index = 0
        self._loading_running = True
        self._animate_loading()

    def _animate_loading(self):
        if not getattr(self, '_loading_running', False):
            return
        frame = self.loading_frames[self.loading_index % len(self.loading_frames)]
        text = f"Loading {frame}"
        try:
            self.loading_target.config(text=text)
        except Exception:
            pass
        self.loading_index += 1
        self.root.after(200, self._animate_loading)

    def stop_loading(self, kind="scan"):
        self._loading_running = False
        if kind == "scan":
            self.scan_status.config(text="")
        else:
            self.analysis_status.config(text="")

    def _on_root_resize(self, event=None):
        # ensure results display frame uses at least 30% of total window height
        try:
            total_h = self.root.winfo_height()
            min_h = max(150, int(total_h * 0.30))
            # set the frame height (pack_propagate False respects it)
            self.results_display_frame.configure(height=min_h)
        except Exception:
            pass

    # ---------- Search / Filter helpers ----------
    def _clear_search(self):
        self.search_var.set("")
        self.filter_results()

    def filter_results(self):
        query = (self.search_var.get() or "").strip().lower()
        # Iterate over stored widgets and show/hide based on match
        for entry in list(self.app_vars.values()):
            # entry can be (var, app) for older entries; guard for length
            if len(entry) == 3:
                var, app, widget = entry
            else:
                # fallback: no widget stored
                continue
            name = app.get('name','').lower()
            if not query or query in name:
                if not widget.winfo_ismapped():
                    widget.pack(anchor=tk.W, padx=20)
            else:
                if widget.winfo_ismapped():
                    widget.pack_forget()

        # Show/hide section labels depending on any visible child
        if getattr(self, 'reg_label', None):
            any_reg = any(app in self.registry_apps and widget.winfo_ismapped() for (var, app, widget) in [v for v in self.app_vars.values() if len(v)==3])
            if any_reg:
                if not self.reg_label.winfo_ismapped():
                    self.reg_label.pack(anchor=tk.W, pady=(10,5))
            else:
                if self.reg_label.winfo_ismapped():
                    self.reg_label.pack_forget()

        if getattr(self, 'exe_label', None):
            any_exe = any(app in self.exe_apps and widget.winfo_ismapped() for (var, app, widget) in [v for v in self.app_vars.values() if len(v)==3])
            if any_exe:
                if not self.exe_label.winfo_ismapped():
                    self.exe_label.pack(anchor=tk.W, pady=(15,5))
            else:
                if self.exe_label.winfo_ismapped():
                    self.exe_label.pack_forget()

    # ---------- Export helpers ----------
    def on_export_csv(self):
        if not self.analysis_results:
            messagebox.showwarning("No Data", "No analysis results to export.")
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files','*.csv')])
        if not path:
            return
        import csv
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['name','remote_admin','remote_file_sharing','keylogging','server_hosting','llm_text'])
                for r in self.analysis_results:
                    vec = r.get('risk_vector', [False,False,False,False])
                    writer.writerow([r.get('name'), int(vec[0]), int(vec[1]), int(vec[2]), int(vec[3]), r.get('llm_text','')])
            messagebox.showinfo('Export CSV','CSV saved successfully.')
        except Exception as e:
            messagebox.showerror('Export CSV', str(e))

    def on_export_pdf(self):
        if not self.analysis_results:
            messagebox.showwarning("No Data", "No analysis results to export.")
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF files','*.pdf')])
        if not path:
            return
        # Try to use reportlab if available
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except Exception:
            messagebox.showerror('Export PDF', 'reportlab is required to export PDF. Install with: pip install reportlab')
            return
        try:
            c = canvas.Canvas(path, pagesize=letter)
            width, height = letter
            y = height - 40
            c.setFont('Helvetica-Bold', 14)
            c.drawString(40, y, 'AppsAnalyst - Analysis Results')
            y -= 30
            c.setFont('Helvetica', 10)
            for r in self.analysis_results:
                if y < 80:
                    c.showPage()
                    y = height - 40
                c.drawString(40, y, f"Name: {r.get('name')}")
                y -= 14
                vec = r.get('risk_vector', [False,False,False,False])
                labels = ['Remote Administration','Remote File Sharing','Keylogging','Server Hosting']
                for lab, v in zip(labels, vec):
                    status = 'YES' if v else 'no'
                    c.drawString(60, y, f"{lab}: {status}")
                    y -= 12
                y -= 8
            c.save()
            messagebox.showinfo('Export PDF','PDF saved successfully.')
        except Exception as e:
            messagebox.showerror('Export PDF', str(e))


def run_gui():
    root = tk.Tk()
    app = AppsAnalystGUI(root)
    root.mainloop()


if __name__ == "__main__":
    install_missing_requirements()
    run_gui()
