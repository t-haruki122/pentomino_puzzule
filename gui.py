import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import io
from contextlib import redirect_stdout
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Import from main.py
from main import Table, Material


class PentominoPuzzleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pentomino Puzzle Solver")
        self.root.geometry("1400x800")
        
        # Data storage
        self.table_size = tk.IntVar(value=5)
        self.materials = []  # List of Material objects
        self.xans = []
        self.yans = []
        self.initial_board = None
        self.canvas_widget = None
        
        self.setup_ui()
        self.update_board_size()
    
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Left panel - Input controls
        left_panel = ttk.Frame(main_frame, padding="5")
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Right panel - Visualization
        right_panel = ttk.Frame(main_frame, padding="5")
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)
        
        self.setup_left_panel(left_panel)
        self.setup_right_panel(right_panel)
    
    def setup_left_panel(self, parent):
        # Table Size
        size_frame = ttk.LabelFrame(parent, text="Table Size", padding="10")
        size_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(size_frame, text="Size (NxN):").grid(row=0, column=0, sticky=tk.W)
        size_spinbox = ttk.Spinbox(size_frame, from_=3, to=10, textvariable=self.table_size, 
                                   width=10, command=self.update_board_size)
        size_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Materials
        mat_frame = ttk.LabelFrame(parent, text="Materials", padding="10")
        mat_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        parent.rowconfigure(1, weight=1)
        
        # Material list
        self.mat_listbox = tk.Listbox(mat_frame, height=8)
        self.mat_listbox.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        mat_frame.rowconfigure(0, weight=1)
        mat_frame.columnconfigure(0, weight=1)
        
        ttk.Button(mat_frame, text="Add", command=self.add_material).grid(row=1, column=0, padx=2)
        ttk.Button(mat_frame, text="Edit", command=self.edit_material).grid(row=1, column=1, padx=2)
        ttk.Button(mat_frame, text="Delete", command=self.delete_material).grid(row=1, column=2, padx=2)
        
        # Constraints (xans, yans)
        constraint_frame = ttk.LabelFrame(parent, text="Constraints", padding="10")
        constraint_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(constraint_frame, text="X Sums (comma-separated):").grid(row=0, column=0, sticky=tk.W)
        self.xans_entry = ttk.Entry(constraint_frame, width=30)
        self.xans_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(constraint_frame, text="Y Sums (comma-separated):").grid(row=2, column=0, sticky=tk.W)
        self.yans_entry = ttk.Entry(constraint_frame, width=30)
        self.yans_entry.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Initial Board State
        board_frame = ttk.LabelFrame(parent, text="Initial Board State", padding="10")
        board_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(board_frame, text="Click cells: 0→1→-1→0").grid(row=0, column=0, sticky=tk.W)
        
        self.board_canvas = tk.Canvas(board_frame, width=250, height=250, bg='white')
        self.board_canvas.grid(row=1, column=0, pady=5)
        self.board_canvas.bind("<Button-1>", self.on_board_click)
        
        # Solve button
        solve_btn = ttk.Button(parent, text="Solve Puzzle", command=self.solve_puzzle, 
                              style='Accent.TButton')
        solve_btn.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # Load example button
        example_btn = ttk.Button(parent, text="Load Example", command=self.load_example)
        example_btn.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)
    
    def setup_right_panel(self, parent):
        # Progress log
        log_frame = ttk.LabelFrame(parent, text="Solver Progress", padding="5")
        log_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        parent.rowconfigure(0, weight=0)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=60)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        # Visualization area
        viz_frame = ttk.LabelFrame(parent, text="Puzzle Solution", padding="5")
        viz_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        viz_frame.rowconfigure(0, weight=1)
        viz_frame.columnconfigure(0, weight=1)
        
        self.viz_container = ttk.Frame(viz_frame)
        self.viz_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.viz_container.rowconfigure(0, weight=1)
        self.viz_container.columnconfigure(0, weight=1)
    
    def update_board_size(self):
        """Update board when size changes"""
        n = self.table_size.get()
        self.initial_board = [[0 for _ in range(n)] for _ in range(n)]
        self.draw_board()
        
        # Update constraint entries with default values
        self.xans_entry.delete(0, tk.END)
        self.yans_entry.delete(0, tk.END)
    
    def draw_board(self):
        """Draw the initial board state grid"""
        self.board_canvas.delete("all")
        n = self.table_size.get()
        cell_size = 250 // n
        
        for r in range(n):
            for c in range(n):
                x1 = c * cell_size
                y1 = r * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                val = self.initial_board[r][c]
                
                # Color based on value
                if val == 0:
                    color = 'white'
                elif val == 1:
                    color = '#333333'
                elif val == -1:
                    color = '#D3D3D3'
                else:
                    color = 'white'
                
                self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='black')
                
                # Draw value
                if val != 0:
                    text_color = 'white' if val == 1 else 'black'
                    self.board_canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, 
                                                 text=str(val), fill=text_color, 
                                                 font=('Arial', 10, 'bold'))
    
    def on_board_click(self, event):
        """Handle clicks on the board canvas"""
        n = self.table_size.get()
        cell_size = 250 // n
        
        c = event.x // cell_size
        r = event.y // cell_size
        
        if 0 <= r < n and 0 <= c < n:
            # Cycle through 0 -> 1 -> -1 -> 0
            current = self.initial_board[r][c]
            if current == 0:
                self.initial_board[r][c] = 1
            elif current == 1:
                self.initial_board[r][c] = -1
            else:
                self.initial_board[r][c] = 0
            
            self.draw_board()
    
    def add_material(self):
        """Add a new material"""
        dialog = MaterialDialog(self.root, "Add Material")
        if dialog.result:
            try:
                positions = self.parse_positions(dialog.result)
                mat = Material(positions)
                self.materials.append(mat)
                self.update_material_list()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid material format: {e}")
    
    def edit_material(self):
        """Edit selected material"""
        selection = self.mat_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a material to edit")
            return
        
        idx = selection[0]
        current_mat = self.materials[idx]
        current_str = ", ".join([f"({x},{y})" for x, y in current_mat.positions])
        
        dialog = MaterialDialog(self.root, "Edit Material", current_str)
        if dialog.result:
            try:
                positions = self.parse_positions(dialog.result)
                self.materials[idx] = Material(positions)
                self.update_material_list()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid material format: {e}")
    
    def delete_material(self):
        """Delete selected material"""
        selection = self.mat_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a material to delete")
            return
        
        idx = selection[0]
        del self.materials[idx]
        self.update_material_list()
    
    def update_material_list(self):
        """Update the material listbox"""
        self.mat_listbox.delete(0, tk.END)
        for i, mat in enumerate(self.materials):
            pos_str = ", ".join([f"({x},{y})" for x, y in mat.positions[:3]])
            if len(mat.positions) > 3:
                pos_str += "..."
            self.mat_listbox.insert(tk.END, f"Material {i+1}: {pos_str} ({mat.n} cells)")
    
    def parse_positions(self, text):
        """Parse position string like '(0,0), (1,0), (1,1)'"""
        positions = []
        # Remove spaces and split by parentheses
        text = text.replace(" ", "")
        pairs = text.split("),(")
        
        for pair in pairs:
            pair = pair.strip("()")
            if pair:
                x, y = map(int, pair.split(","))
                positions.append((x, y))
        
        if not positions:
            raise ValueError("No positions provided")
        
        return positions
    
    def parse_constraint(self, text):
        """Parse comma-separated integers"""
        if not text.strip():
            return []
        return [int(x.strip()) for x in text.split(",")]
    
    def load_example(self):
        """Load the example from main.py"""
        self.table_size.set(5)
        self.update_board_size()
        
        # Example materials
        self.materials = [
            Material([(0, 0), (0, 1), (1, 1)]),
            Material([(0, 0), (1, 0), (1, 1), (2, 0)]),
            Material([(0, 0), (1, 0), (2, 0), (2, -1)]),
            Material([(0, 0), (1, 0), (1, 1), (2, 1)])
        ]
        self.update_material_list()
        
        # Example constraints
        self.xans_entry.delete(0, tk.END)
        self.xans_entry.insert(0, "5, 4, 3, 2, 1")
        
        self.yans_entry.delete(0, tk.END)
        self.yans_entry.insert(0, "5, 4, 3, 2, 1")
        
        messagebox.showinfo("Success", "Example loaded successfully!")
    
    def solve_puzzle(self):
        """Solve the puzzle with current settings"""
        try:
            # Clear previous results
            self.log_text.delete(1.0, tk.END)
            if self.canvas_widget:
                self.canvas_widget.get_tk_widget().destroy()
                self.canvas_widget = None
            
            # Parse constraints
            xans = self.parse_constraint(self.xans_entry.get())
            yans = self.parse_constraint(self.yans_entry.get())
            
            n = self.table_size.get()
            
            if len(xans) != n or len(yans) != n:
                messagebox.showerror("Error", f"Constraints must have {n} values each")
                return
            
            if not self.materials:
                messagebox.showerror("Error", "Please add at least one material")
                return
            
            # Create table with initial board
            table = Table(self.initial_board)
            
            # Redirect stdout to capture logs
            log_capture = io.StringIO()
            
            with redirect_stdout(log_capture):
                table.eval(xans, yans, self.materials)
            
            # Display logs
            logs = log_capture.getvalue()
            self.log_text.insert(tk.END, logs)
            self.log_text.see(tk.END)
            
            # Display visualization
            fig = table.visualize(xans, yans, show=False)
            
            if fig:
                self.canvas_widget = FigureCanvasTkAgg(fig, master=self.viz_container)
                self.canvas_widget.draw()
                self.canvas_widget.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                
                messagebox.showinfo("Success", "Puzzle solved! See visualization below.")
            else:
                messagebox.showwarning("No Solution", "No solution found for this puzzle.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to solve puzzle: {e}")
            import traceback
            self.log_text.insert(tk.END, f"\n\nError:\n{traceback.format_exc()}")


class MaterialDialog:
    """Dialog for adding/editing materials"""
    def __init__(self, parent, title, initial_value=""):
        self.result = None
        
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.transient(parent)
        dialog.grab_set()
        
        # Instructions
        ttk.Label(dialog, text="Enter positions as (x,y) pairs, comma-separated:").pack(pady=10)
        ttk.Label(dialog, text="Example: (0,0), (1,0), (1,1)", font=('Arial', 9, 'italic')).pack()
        
        # Entry
        entry = ttk.Entry(dialog, width=50)
        entry.pack(pady=10, padx=10)
        entry.insert(0, initial_value)
        entry.focus()
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        def on_ok():
            self.result = entry.get()
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        entry.bind("<Return>", lambda e: on_ok())
        
        dialog.wait_window()


def main():
    root = tk.Tk()
    app = PentominoPuzzleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
