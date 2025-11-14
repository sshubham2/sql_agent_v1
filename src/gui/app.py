"""Tkinter GUI Application for SQL Agent"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import os
from pathlib import Path
import pandas as pd
from datetime import datetime


class SQLAgentGUI:
    """Main GUI application for SQL Agent"""

    def __init__(self, root, workflow_runner):
        """
        Initialize the GUI

        Args:
            root: Tkinter root window
            workflow_runner: Function to run the workflow
        """
        self.root = root
        self.workflow_runner = workflow_runner
        self.current_state = {}
        self.workflow_thread = None
        self.message_queue = queue.Queue()

        # Setup window
        self.root.title("SQL Agent - Measure Query Assistant")
        self.root.geometry("1200x900")

        # Create GUI elements
        self.create_widgets()

        # Start checking message queue
        self.check_queue()

    def create_widgets(self):
        """Create all GUI widgets"""

        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        current_row = 0

        # === Query Input Section ===
        ttk.Label(main_frame, text="User Query:", font=('Arial', 10, 'bold')).grid(
            row=current_row, column=0, sticky=tk.W, pady=(0, 5)
        )
        current_row += 1

        self.query_text = scrolledtext.ScrolledText(main_frame, height=4, width=100, wrap=tk.WORD)
        self.query_text.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        main_frame.rowconfigure(current_row, weight=0)
        current_row += 1

        # Submit button
        self.submit_btn = ttk.Button(main_frame, text="Submit Query", command=self.submit_query)
        self.submit_btn.grid(row=current_row, column=0, sticky=tk.W, pady=(0, 15))
        current_row += 1

        # === Identification Display ===
        ttk.Label(main_frame, text="Identified Measures & Dimensions:", font=('Arial', 10, 'bold')).grid(
            row=current_row, column=0, sticky=tk.W, pady=(0, 5)
        )
        current_row += 1

        self.identification_label = ttk.Label(main_frame, text="(Not yet identified)", foreground="gray")
        self.identification_label.grid(row=current_row, column=0, sticky=tk.W, pady=(0, 15))
        current_row += 1

        # === Rewritten Query Section ===
        ttk.Label(main_frame, text="Rewritten Query (Review & Edit):", font=('Arial', 10, 'bold')).grid(
            row=current_row, column=0, sticky=tk.W, pady=(0, 5)
        )
        current_row += 1

        self.rewritten_text = scrolledtext.ScrolledText(main_frame, height=6, width=100, wrap=tk.WORD)
        self.rewritten_text.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.rewritten_text.config(state=tk.DISABLED)
        main_frame.rowconfigure(current_row, weight=0)
        current_row += 1

        # Confirm rewritten query button
        self.confirm_query_btn = ttk.Button(
            main_frame, text="Confirm Query", command=self.confirm_rewritten_query, state=tk.DISABLED
        )
        self.confirm_query_btn.grid(row=current_row, column=0, sticky=tk.W, pady=(0, 15))
        current_row += 1

        # === SQL Display Section ===
        ttk.Label(main_frame, text="Generated SQL:", font=('Arial', 10, 'bold')).grid(
            row=current_row, column=0, sticky=tk.W, pady=(0, 5)
        )
        current_row += 1

        self.sql_text = scrolledtext.ScrolledText(main_frame, height=8, width=100, wrap=tk.WORD)
        self.sql_text.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.sql_text.config(state=tk.DISABLED)
        main_frame.rowconfigure(current_row, weight=0)
        current_row += 1

        # SQL review checkbox and buttons frame
        sql_control_frame = ttk.Frame(main_frame)
        sql_control_frame.grid(row=current_row, column=0, sticky=tk.W, pady=(0, 15))
        current_row += 1

        self.sql_review_var = tk.BooleanVar(value=True)
        self.sql_review_checkbox = ttk.Checkbutton(
            sql_control_frame, text="Review SQL before execution",
            variable=self.sql_review_var
        )
        self.sql_review_checkbox.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))

        self.confirm_sql_btn = ttk.Button(
            sql_control_frame, text="Confirm & Execute SQL",
            command=self.confirm_and_execute_sql, state=tk.DISABLED
        )
        self.confirm_sql_btn.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))

        self.upload_json_btn = ttk.Button(
            sql_control_frame, text="Upload Measure JSON",
            command=self.upload_measure_json
        )
        self.upload_json_btn.grid(row=0, column=2, sticky=tk.W)

        # === Results Section ===
        ttk.Label(main_frame, text="Results:", font=('Arial', 10, 'bold')).grid(
            row=current_row, column=0, sticky=tk.W, pady=(0, 5)
        )
        current_row += 1

        # Results treeview with scrollbars
        results_frame = ttk.Frame(main_frame)
        results_frame.grid(row=current_row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        main_frame.rowconfigure(current_row, weight=1)
        current_row += 1

        # Scrollbars
        results_vsb = ttk.Scrollbar(results_frame, orient="vertical")
        results_hsb = ttk.Scrollbar(results_frame, orient="horizontal")

        self.results_tree = ttk.Treeview(
            results_frame,
            yscrollcommand=results_vsb.set,
            xscrollcommand=results_hsb.set
        )

        results_vsb.config(command=self.results_tree.yview)
        results_hsb.config(command=self.results_tree.xview)

        results_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        results_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Export button
        self.export_btn = ttk.Button(main_frame, text="Export to CSV", command=self.export_to_csv, state=tk.DISABLED)
        self.export_btn.grid(row=current_row, column=0, sticky=tk.W, pady=(0, 10))
        current_row += 1

        # === Status Bar ===
        self.status_label = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=current_row, column=0, sticky=(tk.W, tk.E))

    def update_status(self, message: str):
        """Update status bar"""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def submit_query(self):
        """Submit user query and start workflow"""
        query = self.query_text.get("1.0", tk.END).strip()

        if not query:
            messagebox.showwarning("Input Required", "Please enter a query")
            return

        # Disable submit button
        self.submit_btn.config(state=tk.DISABLED)
        self.update_status("Processing query...")

        # Clear previous results
        self.clear_results()

        # Create initial state
        initial_state = {
            'user_query': query,
            'sql_review_enabled': self.sql_review_var.get(),
            'identified_measures': [],
            'identified_dimensions': [],
            'rewritten_query': '',
            'user_confirmed_query': '',
            'measure_configs': {},
            'generated_sql': '',
            'user_confirmed_sql': None,
            'execution_results': None,
            'csv_path': None,
            'error': None
        }

        self.current_state = initial_state

        # Run workflow in separate thread
        self.workflow_thread = threading.Thread(target=self.run_workflow_thread, args=(initial_state,))
        self.workflow_thread.start()

    def run_workflow_thread(self, initial_state):
        """Run workflow in background thread"""
        try:
            # Import here to avoid circular imports
            from ..agent.graph import create_workflow

            workflow = create_workflow()

            # We'll run the workflow step by step with pauses
            # For now, let's run it fully and handle pauses differently
            # This is a simplified version - full implementation would use streaming

            # For demonstration, we'll simulate the workflow steps
            self.simulate_workflow(initial_state)

        except Exception as e:
            self.message_queue.put(('error', str(e)))

    def simulate_workflow(self, state):
        """Simulate workflow execution with GUI updates"""
        # Import nodes
        from ..agent import nodes

        try:
            # Node 1: Input
            state = nodes.input_node(state)
            self.message_queue.put(('status', 'Processing input...'))

            # Node 2: Identify measures
            state = nodes.identify_measures_node(state)
            if state.get('error'):
                self.message_queue.put(('error', state['error']))
                return

            self.message_queue.put(('identified', state))

            # Node 3: Rewrite query
            state = nodes.rewrite_query_node(state)
            if state.get('error'):
                self.message_queue.put(('error', state['error']))
                return

            self.message_queue.put(('rewritten', state))

            # Node 4: Wait for human confirmation (handled by GUI)
            self.message_queue.put(('wait_confirm_query', state))
            # Thread will pause here, resumed by confirm button

        except Exception as e:
            self.message_queue.put(('error', str(e)))

    def continue_workflow_after_query_confirmation(self):
        """Continue workflow after query confirmation"""
        from ..agent import nodes

        def continue_thread():
            try:
                state = self.current_state

                # Node 5: JSON Lookup
                state = nodes.json_lookup_node(state)
                if state.get('error'):
                    self.message_queue.put(('error', state['error']))
                    return

                self.message_queue.put(('status', 'Measure configurations loaded'))

                # Node 6: SQL Generation
                state = nodes.sql_generation_node(state)
                if state.get('error'):
                    self.message_queue.put(('error', state['error']))
                    return

                self.message_queue.put(('sql_generated', state))

                # Node 7: Conditional SQL review
                if state.get('sql_review_enabled'):
                    self.message_queue.put(('wait_confirm_sql', state))
                else:
                    # Auto-execute
                    state['user_confirmed_sql'] = state['generated_sql']
                    self.execute_workflow(state)

            except Exception as e:
                self.message_queue.put(('error', str(e)))

        threading.Thread(target=continue_thread).start()

    def execute_workflow(self, state):
        """Execute the final SQL query"""
        from ..agent import nodes

        def execute_thread():
            try:
                # Node 8: Execute and export
                state = nodes.execute_and_export_node(state)

                if state.get('error'):
                    self.message_queue.put(('error', state['error']))
                    return

                self.message_queue.put(('results', state))
                self.message_queue.put(('status', 'Query executed successfully!'))

            except Exception as e:
                self.message_queue.put(('error', str(e)))

        threading.Thread(target=execute_thread).start()

    def check_queue(self):
        """Check message queue for updates from workflow thread"""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()

                if msg_type == 'status':
                    self.update_status(data)

                elif msg_type == 'identified':
                    measures = ', '.join(data.get('identified_measures', []))
                    dimensions = ', '.join(data.get('identified_dimensions', []))
                    self.identification_label.config(
                        text=f"Measures: {measures} | Dimensions: {dimensions}",
                        foreground="black"
                    )

                elif msg_type == 'rewritten':
                    self.rewritten_text.config(state=tk.NORMAL)
                    self.rewritten_text.delete("1.0", tk.END)
                    self.rewritten_text.insert("1.0", data.get('rewritten_query', ''))
                    self.current_state = data

                elif msg_type == 'wait_confirm_query':
                    self.confirm_query_btn.config(state=tk.NORMAL)
                    self.rewritten_text.config(state=tk.NORMAL)
                    self.update_status("Please review and confirm the rewritten query")

                elif msg_type == 'sql_generated':
                    self.sql_text.config(state=tk.NORMAL)
                    self.sql_text.delete("1.0", tk.END)
                    self.sql_text.insert("1.0", data.get('generated_sql', ''))
                    self.sql_text.config(state=tk.DISABLED)
                    self.current_state = data

                elif msg_type == 'wait_confirm_sql':
                    self.sql_text.config(state=tk.NORMAL)  # Allow editing
                    self.confirm_sql_btn.config(state=tk.NORMAL)
                    self.update_status("Please review and confirm the SQL statement")

                elif msg_type == 'results':
                    self.display_results(data.get('execution_results', []))
                    self.current_state = data

                elif msg_type == 'error':
                    messagebox.showerror("Error", data)
                    self.update_status(f"Error: {data}")
                    self.submit_btn.config(state=tk.NORMAL)

        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.check_queue)

    def confirm_rewritten_query(self):
        """User confirmed the rewritten query"""
        confirmed = self.rewritten_text.get("1.0", tk.END).strip()
        self.current_state['user_confirmed_query'] = confirmed

        self.confirm_query_btn.config(state=tk.DISABLED)
        self.rewritten_text.config(state=tk.DISABLED)
        self.update_status("Query confirmed, loading measure configurations...")

        # Continue workflow
        self.continue_workflow_after_query_confirmation()

    def confirm_and_execute_sql(self):
        """User confirmed the SQL, execute it"""
        confirmed_sql = self.sql_text.get("1.0", tk.END).strip()
        self.current_state['user_confirmed_sql'] = confirmed_sql

        self.confirm_sql_btn.config(state=tk.DISABLED)
        self.sql_text.config(state=tk.DISABLED)
        self.update_status("Executing SQL query...")

        # Execute workflow
        self.execute_workflow(self.current_state)

    def display_results(self, results):
        """Display query results in treeview"""
        # Clear existing data
        self.results_tree.delete(*self.results_tree.get_children())

        if not results or len(results) == 0:
            self.update_status("Query executed but returned no results")
            return

        # Get column names
        columns = list(results[0].keys())

        # Configure treeview columns
        self.results_tree['columns'] = columns
        self.results_tree['show'] = 'headings'

        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=100)

        # Insert data
        for row in results:
            values = [row.get(col, '') for col in columns]
            self.results_tree.insert('', tk.END, values=values)

        # Enable export button
        self.export_btn.config(state=tk.NORMAL)
        self.submit_btn.config(state=tk.NORMAL)

    def export_to_csv(self):
        """Export results to CSV file"""
        results = self.current_state.get('execution_results')

        if not results:
            messagebox.showwarning("No Data", "No results to export")
            return

        # Open file dialog
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"query_results_{timestamp}.csv"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_filename
        )

        if file_path:
            try:
                df = pd.DataFrame(results)
                df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Results exported to:\n{file_path}")
                self.update_status(f"Exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {e}")

    def upload_measure_json(self):
        """Upload a new measure JSON file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Select Measure JSON File"
        )

        if file_path:
            try:
                # Copy to measures directory
                import shutil
                measures_dir = Path("./measures")
                measures_dir.mkdir(exist_ok=True)

                dest_path = measures_dir / Path(file_path).name
                shutil.copy(file_path, dest_path)

                # Rescan directory
                from ..utils.json_loader import scan_measures_directory
                scan_measures_directory()

                messagebox.showinfo("Success", f"Measure JSON uploaded:\n{Path(file_path).name}")
                self.update_status(f"Uploaded {Path(file_path).name}")

            except Exception as e:
                messagebox.showerror("Upload Error", f"Failed to upload: {e}")

    def clear_results(self):
        """Clear all result displays"""
        self.identification_label.config(text="(Not yet identified)", foreground="gray")
        self.rewritten_text.config(state=tk.NORMAL)
        self.rewritten_text.delete("1.0", tk.END)
        self.rewritten_text.config(state=tk.DISABLED)
        self.sql_text.config(state=tk.NORMAL)
        self.sql_text.delete("1.0", tk.END)
        self.sql_text.config(state=tk.DISABLED)
        self.results_tree.delete(*self.results_tree.get_children())
        self.export_btn.config(state=tk.DISABLED)
        self.confirm_query_btn.config(state=tk.DISABLED)
        self.confirm_sql_btn.config(state=tk.DISABLED)


def launch_gui(workflow_runner=None):
    """
    Launch the Tkinter GUI

    Args:
        workflow_runner: Function to run the workflow (optional)
    """
    root = tk.Tk()
    app = SQLAgentGUI(root, workflow_runner)
    root.mainloop()
