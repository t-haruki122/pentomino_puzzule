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
        self.xans_vars = []  # List of IntVar for X constraints
        self.yans_vars = []  # List of IntVar for Y constraints
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
        
        ttk.Label(constraint_frame, text="X Sums (wheel/drag to adjust):", 
                 font=('Arial', 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.xans_frame = ttk.Frame(constraint_frame)
        self.xans_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(constraint_frame, text="Y Sums (wheel/drag to adjust):", 
                 font=('Arial', 9)).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.yans_frame = ttk.Frame(constraint_frame)
        self.yans_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
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
        
        # Update constraint spinboxes
        self.update_constraint_spinboxes()
    
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
    
    def update_constraint_spinboxes(self):
        """Update constraint controls based on table size"""
        n = self.table_size.get()
        
        # Clear existing widgets
        for widget in self.xans_frame.winfo_children():
            widget.destroy()
        for widget in self.yans_frame.winfo_children():
            widget.destroy()
        
        # Clear and recreate IntVar lists
        self.xans_vars = []
        self.yans_vars = []
        
        # Create X constraint controls (horizontal layout)
        for i in range(n):
            var = tk.IntVar(value=0)
            self.xans_vars.append(var)
            
            # Container frame for each control
            control_frame = ttk.Frame(self.xans_frame)
            control_frame.grid(row=0, column=i, padx=5, pady=2)
            
            # Label for index
            ttk.Label(control_frame, text=f"X{i}", font=('Arial', 9, 'bold')).pack()
            
            # Interactive value display
            value_label = tk.Label(control_frame, textvariable=var, 
                                  font=('Arial', 14, 'bold'), 
                                  bg='#E3F2FD', fg='#1976D2',
                                  width=4, height=1, relief=tk.RAISED, bd=2,
                                  cursor='hand2')
            value_label.pack(pady=2)
            
            # Bind mouse events
            self._bind_interactive_events(value_label, var, n*n)
        
        # Create Y constraint controls (horizontal layout)
        for i in range(n):
            var = tk.IntVar(value=0)
            self.yans_vars.append(var)
            
            # Container frame for each control
            control_frame = ttk.Frame(self.yans_frame)
            control_frame.grid(row=0, column=i, padx=5, pady=2)
            
            # Label for index
            ttk.Label(control_frame, text=f"Y{i}", font=('Arial', 9, 'bold')).pack()
            
            # Interactive value display
            value_label = tk.Label(control_frame, textvariable=var, 
                                  font=('Arial', 14, 'bold'), 
                                  bg='#E8F5E9', fg='#388E3C',
                                  width=4, height=1, relief=tk.RAISED, bd=2,
                                  cursor='hand2')
            value_label.pack(pady=2)
            
            # Bind mouse events
            self._bind_interactive_events(value_label, var, n*n)
    
    def _bind_interactive_events(self, widget, var, max_val):
        """Bind mouse wheel and drag events to a widget"""
        # Mouse wheel support
        def on_wheel(event):
            current = var.get()
            if event.delta > 0:  # Scroll up
                new_val = min(current + 1, max_val)
            else:  # Scroll down
                new_val = max(current - 1, 0)
            var.set(new_val)
        
        widget.bind("<MouseWheel>", on_wheel)
        
        # Drag support with click detection
        drag_data = {'y': 0, 'start_val': 0, 'dragged': False}
        
        def on_drag_start(event):
            drag_data['y'] = event.y
            drag_data['start_val'] = var.get()
            drag_data['dragged'] = False
            widget.config(bg='#FFEB3B', relief=tk.SUNKEN)  # Yellow highlight during drag
        
        def on_drag_motion(event):
            # If mouse moved more than 3 pixels, it's a drag
            if abs(event.y - drag_data['y']) > 3:
                drag_data['dragged'] = True
                delta_y = drag_data['y'] - event.y  # Inverted: up = positive
                steps = delta_y // 10  # 10 pixels per step
                new_val = drag_data['start_val'] + steps
                new_val = max(0, min(new_val, max_val))
                var.set(new_val)
        
        def on_drag_end(event):
            # Restore original color based on which constraint this is
            if var in self.xans_vars:
                widget.config(bg='#E3F2FD', relief=tk.RAISED)
            else:
                widget.config(bg='#E8F5E9', relief=tk.RAISED)
            
            # If not dragged, it's a click - increment value
            if not drag_data['dragged']:
                current = var.get()
                if current < max_val:
                    var.set(current + 1)
        
        # Right-click to decrement
        def on_right_click(event):
            current = var.get()
            if current > 0:
                var.set(current - 1)
        
        widget.bind("<Button-1>", on_drag_start)
        widget.bind("<B1-Motion>", on_drag_motion)
        widget.bind("<ButtonRelease-1>", on_drag_end)
        widget.bind("<Button-3>", on_right_click)  # Right-click

        
        # Hover effect
        def on_enter(event):
            if var in self.xans_vars:
                widget.config(bg='#BBDEFB')  # Lighter blue
            else:
                widget.config(bg='#C8E6C9')  # Lighter green
        
        def on_leave(event):
            if var in self.xans_vars:
                widget.config(bg='#E3F2FD')  # Original blue
            else:
                widget.config(bg='#E8F5E9')  # Original green
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)


    
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
                mat = Material(dialog.result)
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
        
        dialog = MaterialDialog(self.root, "Edit Material", current_mat.positions)
        if dialog.result:
            try:
                self.materials[idx] = Material(dialog.result)
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
        
        # Example constraints - set spinbox values
        example_xans = [5, 4, 3, 2, 1]
        example_yans = [5, 4, 3, 2, 1]
        
        for i, val in enumerate(example_xans):
            self.xans_vars[i].set(val)
        
        for i, val in enumerate(example_yans):
            self.yans_vars[i].set(val)
        
        messagebox.showinfo("Success", "Example loaded successfully!")
    
    def solve_puzzle(self):
        """Solve the puzzle with current settings"""
        try:
            # Clear previous results
            self.log_text.delete(1.0, tk.END)
            if self.canvas_widget:
                self.canvas_widget.get_tk_widget().destroy()
                self.canvas_widget = None
            
            
            # Get constraints from spinboxes
            xans = [var.get() for var in self.xans_vars]
            yans = [var.get() for var in self.yans_vars]
            
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
    """Dialog for adding/editing materials with visual grid editor"""
    def __init__(self, parent, title, initial_positions=None):
        self.result = None
        self.grid_size = tk.IntVar(value=5)
        self.selected_cells = set()  # Set of (x, y) tuples
        
        # Parse initial positions if provided
        if initial_positions:
            self.selected_cells = set(initial_positions)
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        self.draw_grid()
        
        self.dialog.wait_window()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        # Top frame - Grid size control
        top_frame = ttk.Frame(self.dialog, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="Grid Size:").pack(side=tk.LEFT, padx=5)
        size_spinbox = ttk.Spinbox(top_frame, from_=3, to=15, textvariable=self.grid_size, 
                                   width=10, command=self.on_size_change)
        size_spinbox.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(top_frame, text="(Click cells to add/remove)", 
                 font=('Arial', 9, 'italic')).pack(side=tk.LEFT, padx=20)
        
        # Middle frame - Canvas for grid
        canvas_frame = ttk.Frame(self.dialog, padding="10")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, width=500, height=500, bg='white', 
                               highlightthickness=1, highlightbackground='gray')
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Info frame - Show selected positions
        info_frame = ttk.Frame(self.dialog, padding="10")
        info_frame.pack(fill=tk.X)
        
        ttk.Label(info_frame, text="Selected cells:").pack(side=tk.LEFT)
        self.info_label = ttk.Label(info_frame, text="None", foreground='blue')
        self.info_label.pack(side=tk.LEFT, padx=5)
        
        # Button frame
        btn_frame = ttk.Frame(self.dialog, padding="10")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
    
    def on_size_change(self):
        """Handle grid size change"""
        # Clear selections that are out of bounds
        new_size = self.grid_size.get()
        self.selected_cells = {(x, y) for x, y in self.selected_cells 
                              if -new_size < x < new_size and -new_size < y < new_size}
        self.draw_grid()
    
    def draw_grid(self):
        """Draw the material editor grid"""
        self.canvas.delete("all")
        size = self.grid_size.get()
        canvas_size = 500
        cell_size = canvas_size // size
        
        # Draw grid cells
        for row in range(size):
            for col in range(size):
                x1 = col * cell_size
                y1 = row * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                # Convert canvas coordinates to material coordinates
                # Material uses (x, y) where (0, 0) is at center-ish
                # We'll use bottom-left as origin for simplicity
                mat_x = col
                mat_y = size - 1 - row  # Flip Y axis
                
                # Check if this cell is selected
                is_selected = (mat_x, mat_y) in self.selected_cells
                
                color = '#4CAF50' if is_selected else 'white'
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, 
                                            outline='gray', width=1)
                
                # Draw coordinate label
                label = f"{mat_x},{mat_y}"
                text_color = 'white' if is_selected else 'gray'
                self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, 
                                       text=label, fill=text_color, 
                                       font=('Arial', 8))
        
        self.update_info()
    
    def on_canvas_click(self, event):
        """Handle click on canvas"""
        size = self.grid_size.get()
        canvas_size = 500
        cell_size = canvas_size // size
        
        col = event.x // cell_size
        row = event.y // cell_size
        
        if 0 <= col < size and 0 <= row < size:
            # Convert to material coordinates
            mat_x = col
            mat_y = size - 1 - row
            
            # Toggle selection
            if (mat_x, mat_y) in self.selected_cells:
                self.selected_cells.remove((mat_x, mat_y))
            else:
                self.selected_cells.add((mat_x, mat_y))
            
            self.draw_grid()
    
    def update_info(self):
        """Update the info label with selected positions"""
        if not self.selected_cells:
            self.info_label.config(text="None (click cells to add)")
        else:
            # Normalize positions to start from (0, 0)
            positions = self.normalize_positions(list(self.selected_cells))
            pos_str = ", ".join([f"({x},{y})" for x, y in sorted(positions)[:5]])
            if len(positions) > 5:
                pos_str += "..."
            self.info_label.config(text=f"{len(positions)} cells - {pos_str}")
    
    def normalize_positions(self, positions):
        """Normalize positions so minimum x and y are 0"""
        if not positions:
            return []
        
        min_x = min(x for x, y in positions)
        min_y = min(y for x, y in positions)
        
        return [(x - min_x, y - min_y) for x, y in positions]
    
    def clear_all(self):
        """Clear all selected cells"""
        self.selected_cells.clear()
        self.draw_grid()
    
    def on_ok(self):
        """OK button handler"""
        if not self.selected_cells:
            messagebox.showwarning("Warning", "Please select at least one cell")
            return
        
        # Normalize and return positions
        self.result = self.normalize_positions(list(self.selected_cells))
        self.dialog.destroy()
    
    def on_cancel(self):
        """Cancel button handler"""
        self.result = None
        self.dialog.destroy()



def main():
    root = tk.Tk()
    app = PentominoPuzzleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
