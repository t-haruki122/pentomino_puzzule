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
        self.root.geometry("900x750")
        
        # Data storage
        self.table_size = tk.IntVar(value=5)
        self.materials = []  # List of Material objects
        self.xans = []  # X constraints
        self.yans = []  # Y constraints
        self.initial_board = []  # Initial board state
        self.solution_board = None  # Solution board
        self.mode = tk.StringVar(value='edit')  # 'edit' or 'result'
        
        # Grid buttons
        self.grid_buttons = {}  # {(row, col): button}
        self.constraint_buttons = {}  # {'x0': button, 'y0': button, ...}
        
        self.canvas_widget = None
        
        self.setup_ui()
        self.update_board_size()
        
        # Hidden shortcut for Load Example (Ctrl+L)
        self.root.bind('<Control-l>', lambda e: self.load_example())
    
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Top panel - Controls (with background color)
        top_panel = ttk.Frame(main_frame, padding="5")
        top_panel.grid(row=0, column=0, sticky=(tk.W, tk.E))
        top_panel.configure(style='Header.TFrame')
        
        # Configure style for header
        style = ttk.Style()
        style.configure('Header.TFrame', background='#e0e0e0')
        
        # Grid panel - Interactive grid
        grid_panel = ttk.Frame(main_frame, padding="5")
        grid_panel.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Bottom panel - Log
        bottom_panel = ttk.Frame(main_frame, padding="5")
        bottom_panel.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        self.setup_top_panel(top_panel)
        self.setup_grid_panel(grid_panel)
        self.setup_bottom_panel(bottom_panel)
    
    def setup_top_panel(self, parent):
        # Left side - Materials and controls
        left_frame = ttk.Frame(parent)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Table Size
        ttk.Label(left_frame, text="Size:").grid(row=0, column=0, padx=5)
        
        # Table Size - Interactive button
        self.size_display = tk.Button(left_frame, text=str(self.table_size.get()),
                                     width=4, font=('Arial', 10, 'bold'),
                                     bg='white', fg='black',
                                     relief=tk.RAISED, bd=2)
        self.size_display.grid(row=0, column=1, padx=5)
        self.setup_size_events()
        
        # Materials
        ttk.Label(left_frame, text="Materials:").grid(row=0, column=2, padx=5)
        self.mat_listbox = tk.Listbox(left_frame, height=3, width=30)
        self.mat_listbox.grid(row=0, column=3, padx=5)
        self.mat_listbox.bind('<Delete>', lambda e: self.delete_material())
        
        ttk.Button(left_frame, text="Add", command=self.add_material, width=6).grid(row=0, column=4, padx=2)
        ttk.Button(left_frame, text="Edit", command=self.edit_material, width=6).grid(row=0, column=5, padx=2)
        
        # Right side - Action buttons
        right_frame = ttk.Frame(parent)
        right_frame.grid(row=0, column=1, sticky=(tk.E))
        parent.columnconfigure(1, weight=1)
        
        # Mode toggle
        ttk.Label(right_frame, text="Mode:").grid(row=0, column=0, padx=5)
        mode_edit = ttk.Radiobutton(right_frame, text="Edit", variable=self.mode, value='edit', 
                                    command=self.update_grid_display)
        mode_edit.grid(row=0, column=1, padx=2)
        mode_result = ttk.Radiobutton(right_frame, text="Result", variable=self.mode, value='result',
                                      command=self.update_grid_display)
        mode_result.grid(row=0, column=2, padx=2)
        
        ttk.Button(right_frame, text="Solve Puzzle", command=self.solve_puzzle, 
                  style='Accent.TButton').grid(row=0, column=3, padx=5)
    
    def setup_grid_panel(self, parent):
        # Create main container
        container = ttk.Frame(parent)
        container.pack(expand=True, fill=tk.BOTH)
        
        # Grid frame
        self.grid_frame = ttk.Frame(container)
        self.grid_frame.pack(expand=True)
        
        # Button frame (bottom-right)
        self.grid_button_frame = ttk.Frame(container)
        self.grid_button_frame.pack(side=tk.BOTTOM, anchor=tk.E, padx=10, pady=5)
        
        ttk.Button(self.grid_button_frame, text="Reset All", 
                  command=self.reset_all).pack(side=tk.LEFT, padx=5)
    
    def setup_bottom_panel(self, parent):
        # Log output
        log_label = ttk.Label(parent, text="Console Log:")
        log_label.grid(row=0, column=0, sticky=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(parent, height=8, width=100, wrap=tk.WORD)
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        parent.columnconfigure(0, weight=1)
    
    def create_grid(self):
        # Clear existing grid
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        self.grid_buttons.clear()
        self.constraint_buttons.clear()
        
        n = self.table_size.get()
        
        # Calculate button size
        btn_size = min(50, 500 // (n + 1))
        
        # Corner (empty)
        corner = tk.Label(self.grid_frame, text="", width=btn_size//7, height=btn_size//14, 
                         relief=tk.FLAT, bg='#f0f0f0')
        corner.grid(row=0, column=0, padx=1, pady=1)
        
        # X constraints (top row)
        for c in range(n):
            btn = tk.Button(self.grid_frame, text=str(self.xans[c]), 
                           width=6, height=2,
                           bg='#E3F2FD', fg='#1976D2', font=('Arial', 12, 'bold'),
                           relief=tk.RAISED, bd=2)
            btn.grid(row=0, column=c+1, padx=1, pady=1)
            
            # Bind events
            self.setup_constraint_events(btn, c, 'x')
            self.constraint_buttons[f'x{c}'] = btn
        
        # Y constraints (left column) and grid cells
        for r in range(n):
            # Y constraint
            btn = tk.Button(self.grid_frame, text=str(self.yans[r]), 
                           width=6, height=2,
                           bg='#E8F5E9', fg='#388E3C', font=('Arial', 12, 'bold'),
                           relief=tk.RAISED, bd=2)
            btn.grid(row=r+1, column=0, padx=1, pady=1)
            
            # Bind events
            self.setup_constraint_events(btn, r, 'y')
            self.constraint_buttons[f'y{r}'] = btn
            
            # Grid cells
            for c in range(n):
                cell_btn = tk.Button(self.grid_frame, text="", 
                                    width=6, height=2,
                                    bg='white', font=('Arial', 11, 'bold'),
                                    relief=tk.RAISED, bd=2)
                cell_btn.grid(row=r+1, column=c+1, padx=1, pady=1)
                
                # Bind events
                cell_btn.bind('<Button-1>', lambda e, row=r, col=c: self.on_cell_click(row, col))
                
                self.grid_buttons[(r, c)] = cell_btn
        
        self.update_grid_display()
    
    def setup_size_events(self):
        """Setup interactive events for size button"""
        drag_data = {'y': 0, 'start_val': 0, 'dragged': False}
        
        # Mouse wheel
        def on_wheel(event):
            delta = 1 if event.delta > 0 else -1
            new_val = max(3, min(self.table_size.get() + delta, 10))
            self.set_table_size(new_val)
        
        self.size_display.bind('<MouseWheel>', on_wheel)
        
        # Drag
        def on_drag_start(event):
            drag_data['y'] = event.y
            drag_data['start_val'] = self.table_size.get()
            drag_data['dragged'] = False
            self.size_display.config(bg='#FFEB3B')
        
        def on_drag_motion(event):
            if abs(event.y - drag_data['y']) > 3:
                drag_data['dragged'] = True
                delta_y = drag_data['y'] - event.y
                steps = delta_y // 10
                new_val = max(3, min(drag_data['start_val'] + steps, 10))
                self.set_table_size(new_val)
        
        def on_drag_end(event):
            self.size_display.config(bg='white')
            
            # If not dragged, it's a click - increment
            if not drag_data['dragged']:
                new_val = min(self.table_size.get() + 1, 10)
                if new_val > 10:
                    new_val = 3  # Wrap around
                self.set_table_size(new_val)
        
        # Right-click to decrement
        def on_right_click(event):
            new_val = max(self.table_size.get() - 1, 3)
            self.set_table_size(new_val)
        
        self.size_display.bind('<Button-1>', on_drag_start)
        self.size_display.bind('<B1-Motion>', on_drag_motion)
        self.size_display.bind('<ButtonRelease-1>', on_drag_end)
        self.size_display.bind('<Button-3>', on_right_click)
    
    def setup_constraint_events(self, button, index, constraint_type):
        n = self.table_size.get()
        max_val = n * n
        constraints = self.xans if constraint_type == 'x' else self.yans
        
        drag_data = {'y': 0, 'start_val': 0, 'dragged': False}
        
        # Mouse wheel
        def on_wheel(event):
            delta = -1 if event.delta > 0 else 1
            new_val = max(0, min(constraints[index] + delta, max_val))
            constraints[index] = new_val
            button.config(text=str(new_val))
        
        button.bind('<MouseWheel>', on_wheel)
        
        # Drag
        def on_drag_start(event):
            drag_data['y'] = event.y
            drag_data['start_val'] = constraints[index]
            drag_data['dragged'] = False
            button.config(bg='#FFEB3B')
        
        def on_drag_motion(event):
            if abs(event.y - drag_data['y']) > 3:
                drag_data['dragged'] = True
                delta_y = drag_data['y'] - event.y
                steps = delta_y // 10
                new_val = max(0, min(drag_data['start_val'] + steps, max_val))
                constraints[index] = new_val
                button.config(text=str(new_val))
        
        def on_drag_end(event):
            # Restore color
            if constraint_type == 'x':
                button.config(bg='#E3F2FD')
            else:
                button.config(bg='#E8F5E9')
            
            # If not dragged, it's a click - increment
            if not drag_data['dragged']:
                new_val = min(constraints[index] + 1, max_val)
                constraints[index] = new_val
                button.config(text=str(new_val))
        
        # Right-click to decrement
        def on_right_click(event):
            new_val = max(constraints[index] - 1, 0)
            constraints[index] = new_val
            button.config(text=str(new_val))
        
        button.bind('<Button-1>', on_drag_start)
        button.bind('<B1-Motion>', on_drag_motion)
        button.bind('<ButtonRelease-1>', on_drag_end)
        button.bind('<Button-3>', on_right_click)
    
    def on_cell_click(self, row, col):
        if self.mode.get() == 'edit':
            # Cycle: 0 -> 1 -> -1 -> 0
            current = self.initial_board[row][col]
            new_val = 1 if current == 0 else (-1 if current == 1 else 0)
            self.initial_board[row][col] = new_val
            self.update_cell_display(row, col)
    
    def update_cell_display(self, row, col):
        button = self.grid_buttons[(row, col)]
        
        if self.mode.get() == 'edit':
            # Edit mode - show initial board state
            val = self.initial_board[row][col]
            if val == 0:
                button.config(text="", bg='white', fg='black')
            elif val == 1:
                button.config(text="1", bg='#333333', fg='white')
            elif val == -1:
                button.config(text="X", bg='#D3D3D3', fg='black')
        else:
            # Result mode - show solution
            if self.solution_board:
                val = self.solution_board[row][col]
                if val == 0:
                    button.config(text="", bg='white', fg='black')
                elif val == -1:
                    button.config(text="X", bg='#D3D3D3', fg='black')
                else:
                    # Color by material
                    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
                             '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b',
                             '#27ae60', '#2980b9', '#8e44ad', '#f1c40f', '#d35400']
                    color = colors[val % len(colors)]
                    button.config(text=str(val), bg=color, fg='white', font=('Arial', 11, 'bold'))
            else:
                button.config(text="", bg='white', fg='black')
    
    def update_grid_display(self):
        n = self.table_size.get()
        for r in range(n):
            for c in range(n):
                self.update_cell_display(r, c)
    
    def set_table_size(self, size):
        """Set table size and update grid"""
        self.table_size.set(size)
        self.size_display.config(text=str(size))
        self.update_board_size()
    
    def update_board_size(self):
        n = self.table_size.get()
        old_n = len(self.initial_board) if self.initial_board else 0
        
        # Update constraints
        self.xans = [0] * n
        self.yans = [0] * n
        
        # Preserve initial board if possible, otherwise create new
        if old_n == n:
            # Keep existing board
            pass
        else:
            # Create new board, preserving what we can
            new_board = [[0 for _ in range(n)] for _ in range(n)]
            if old_n > 0:
                # Copy old values
                for r in range(min(old_n, n)):
                    for c in range(min(old_n, n)):
                        new_board[r][c] = self.initial_board[r][c]
            self.initial_board = new_board
        
        # Reset solution
        self.solution_board = None
        
        # Recreate grid
        self.create_grid()
    
    # Material management methods (keep existing implementation)
    def add_material(self):
        MaterialEditorDialog(self.root, None, self.on_material_saved)
    
    def edit_material(self):
        selection = self.mat_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a material to edit")
            return
        
        index = selection[0]
        material = self.materials[index]
        MaterialEditorDialog(self.root, material, 
                           lambda m: self.on_material_edited(index, m),
                           lambda: self.on_material_deleted(index))
    
    def delete_material(self):
        selection = self.mat_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a material to delete")
            return
        
        index = selection[0]
        if messagebox.askyesno("Confirm Delete", f"Delete material {index}?"):
            del self.materials[index]
            self.update_material_list()
    
    def on_material_saved(self, material):
        self.materials.append(material)
        self.update_material_list()
    
    def on_material_edited(self, index, material):
        self.materials[index] = material
        self.update_material_list()
    
    def on_material_deleted(self, index):
        """Called when material is deleted from editor"""
        del self.materials[index]
        self.update_material_list()
    
    def update_material_list(self):
        self.mat_listbox.delete(0, tk.END)
        for i, mat in enumerate(self.materials):
            self.mat_listbox.insert(tk.END, f"Mat{i}: {len(mat.positions)} cells")
    
    def load_example(self):
        self.table_size.set(5)
        self.update_board_size()
        
        # Example materials
        self.materials = [
            Material([(0, 0), (0, 1), (1, 1)]),
            Material([(0, 0), (1, 0), (1, 1), (2, 0)]),
            Material([(0, 0), (1, 0), (2, 0), (2, -1)]),
            Material([(0, 0), (1, 0), (1, 1), (2, 1)])
        ]
        
        # Example constraints
        self.xans = [5, 4, 3, 2, 1]
        self.yans = [5, 4, 3, 2, 1]
        
        # Update display
        self.update_material_list()
        self.create_grid()
        
        messagebox.showinfo("Success", "Example loaded!")
    
    def reset_all(self):
        """Reset all settings to initial state"""
        if messagebox.askyesno("Confirm Reset", "Reset all settings (materials, size, constraints, board)? This cannot be undone."):
            # Reset materials
            self.materials = []
            self.update_material_list()
            
            # Reset size to default
            self.set_table_size(5)
            
            # Reset constraints
            n = self.table_size.get()
            self.xans = [0] * n
            self.yans = [0] * n
            
            # Reset board
            self.initial_board = [[0 for _ in range(n)] for _ in range(n)]
            
            # Reset solution
            self.solution_board = None
            
            # Switch to edit mode
            self.mode.set('edit')
            
            # Recreate grid
            self.create_grid()
            
            messagebox.showinfo("Reset Complete", "All settings have been reset to initial values")
    
    def clear_board(self):
        """Clear initial board state"""
        if messagebox.askyesno("Confirm Clear", "Clear the initial board state? This cannot be undone."):
            n = self.table_size.get()
            self.initial_board = [[0 for _ in range(n)] for _ in range(n)]
            self.mode.set('edit')
            self.update_grid_display()
            messagebox.showinfo("Cleared", "Board cleared successfully")
    
    def clear_solution(self):
        """Clear solution"""
        if self.solution_board is None:
            messagebox.showinfo("No Solution", "There is no solution to clear")
            return
        
        if messagebox.askyesno("Confirm Clear", "Clear the current solution?"):
            self.solution_board = None
            self.mode.set('edit')
            self.update_grid_display()
            messagebox.showinfo("Cleared", "Solution cleared successfully")
    
    def solve_puzzle(self):
        if not self.materials:
            messagebox.showerror("Error", "Please add at least one material")
            return
        
        # Create table
        n = self.table_size.get()
        table = Table(self.initial_board)
        
        # Redirect stdout to log
        self.log_text.delete(1.0, tk.END)
        log_stream = io.StringIO()
        
        try:
            with redirect_stdout(log_stream):
                result = table.eval(self.xans.copy(), self.yans.copy(), self.materials)
            
            # Display log
            self.log_text.insert(tk.END, log_stream.getvalue())
            self.log_text.see(tk.END)
            
            if result:
                self.solution_board = result.internal
                self.mode.set('result')
                self.update_grid_display()
                messagebox.showinfo("Success", "Solution found!")
            else:
                messagebox.showerror("No Solution", "No solution found")

        
        except Exception as e:
            self.log_text.insert(tk.END, f"\nError: {str(e)}\n")
            messagebox.showerror("Error", str(e))


class MaterialEditorDialog:
    def __init__(self, parent, material, callback, delete_callback=None):
        self.callback = callback
        self.delete_callback = delete_callback
        self.selected_cells = set()
        
        if material:
            for x, y in material.positions:
                self.selected_cells.add((x, y))
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Material Editor")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        # Grid size control
        top_frame = ttk.Frame(self.dialog, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="Grid Size:").pack(side=tk.LEFT, padx=5)
        self.grid_size = tk.IntVar(value=5)
        
        # Interactive grid size button
        self.grid_size_display = tk.Button(top_frame, text=str(self.grid_size.get()),
                                          width=4, font=('Arial', 10, 'bold'),
                                          bg='white', fg='black',
                                          relief=tk.RAISED, bd=2)
        self.grid_size_display.pack(side=tk.LEFT, padx=5)
        self.setup_grid_size_events()
        
        # Canvas
        self.canvas = tk.Canvas(self.dialog, width=400, height=400, bg='white')
        self.canvas.pack(pady=10)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        
        # Selected cells display
        info_frame = ttk.Frame(self.dialog, padding="10")
        info_frame.pack(fill=tk.X)
        
        ttk.Label(info_frame, text="Selected:").pack(side=tk.LEFT)
        self.selected_label = ttk.Label(info_frame, text="None")
        self.selected_label.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog, padding="10")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Clear", command=self.clear_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Material", command=self.delete_current).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Save", command=self.save_material).pack(side=tk.RIGHT, padx=5)
        
        self.draw_grid()
    
    def setup_grid_size_events(self):
        """Setup interactive events for grid size button"""
        drag_data = {'y': 0, 'start_val': 0, 'dragged': False}
        
        # Mouse wheel
        def on_wheel(event):
            delta = 1 if event.delta > 0 else -1
            new_val = max(3, min(self.grid_size.get() + delta, 10))
            self.set_grid_size(new_val)
        
        self.grid_size_display.bind('<MouseWheel>', on_wheel)
        
        # Drag
        def on_drag_start(event):
            drag_data['y'] = event.y
            drag_data['start_val'] = self.grid_size.get()
            drag_data['dragged'] = False
            self.grid_size_display.config(bg='#FFEB3B')
        
        def on_drag_motion(event):
            if abs(event.y - drag_data['y']) > 3:
                drag_data['dragged'] = True
                delta_y = drag_data['y'] - event.y
                steps = delta_y // 10
                new_val = max(3, min(drag_data['start_val'] + steps, 10))
                self.set_grid_size(new_val)
        
        def on_drag_end(event):
            self.grid_size_display.config(bg='white')
            
            # If not dragged, it's a click - increment
            if not drag_data['dragged']:
                new_val = min(self.grid_size.get() + 1, 10)
                if new_val > 10:
                    new_val = 3  # Wrap around
                self.set_grid_size(new_val)
        
        # Right-click to decrement
        def on_right_click(event):
            new_val = max(self.grid_size.get() - 1, 3)
            self.set_grid_size(new_val)
        
        self.grid_size_display.bind('<Button-1>', on_drag_start)
        self.grid_size_display.bind('<B1-Motion>', on_drag_motion)
        self.grid_size_display.bind('<ButtonRelease-1>', on_drag_end)
        self.grid_size_display.bind('<Button-3>', on_right_click)
    
    def set_grid_size(self, size):
        """Set grid size and redraw"""
        self.grid_size.set(size)
        self.grid_size_display.config(text=str(size))
        self.draw_grid()
    
    def draw_grid(self):
        self.canvas.delete("all")
        size = self.grid_size.get()
        cell_size = 400 // size
        
        for r in range(size):
            for c in range(size):
                x1 = c * cell_size
                y1 = r * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                fill = '#4CAF50' if (c, r) in self.selected_cells else 'white'
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline='black')
                self.canvas.create_text(x1 + cell_size//2, y1 + cell_size//2, 
                                       text=f"{c},{r}", font=('Arial', 8))
        
        self.update_selected_label()
    
    def on_canvas_click(self, event):
        size = self.grid_size.get()
        cell_size = 400 // size
        
        c = event.x // cell_size
        r = event.y // cell_size
        
        if 0 <= c < size and 0 <= r < size:
            if (c, r) in self.selected_cells:
                self.selected_cells.remove((c, r))
            else:
                self.selected_cells.add((c, r))
            
            self.draw_grid()
    
    def clear_selection(self):
        self.selected_cells.clear()
        self.draw_grid()
    
    def update_selected_label(self):
        if self.selected_cells:
            cells = sorted(list(self.selected_cells))
            self.selected_label.config(text=str(cells))
        else:
            self.selected_label.config(text="None")
    
    def save_material(self):
        if not self.selected_cells:
            messagebox.showwarning("Empty Material", "Please select at least one cell")
            return
        
        # Normalize positions
        positions = list(self.selected_cells)
        min_x = min(x for x, y in positions)
        min_y = min(y for x, y in positions)
        normalized = [(x - min_x, y - min_y) for x, y in positions]
        
        material = Material(normalized)
        self.callback(material)
        self.dialog.destroy()
    
    def delete_current(self):
        """Delete the current material being edited"""
        if self.delete_callback is None:
            messagebox.showinfo("Cannot Delete", "Cannot delete a new material that hasn't been saved yet")
            return
        
        if messagebox.askyesno("Confirm Delete", "Delete this material?"):
            self.delete_callback()
            self.dialog.destroy()


def main():
    root = tk.Tk()
    app = PentominoPuzzleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
