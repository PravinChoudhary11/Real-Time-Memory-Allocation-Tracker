import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
import numpy as np

# Visualization class (Modified to integrate with tkinter)
class MemoryVisualizer:
    def __init__(self):
        # Create matplotlib figure with two subplots with increased height
        self.fig, self.axes = plt.subplots(2, 1, figsize=(14, 9))  # Increased height
        self.fig.tight_layout(pad=4.0)  # Increased padding
        self.process_colors = {}
        self.color_cycle = iter(mcolors.TABLEAU_COLORS)
        
        # Cache for optimization
        self.memory_patches = []
        self.page_table_patches = []
        
        # Memory axes - adjusted margins for better text display
        self.memory_ax = self.axes[0]
        self.memory_ax.set_title('Memory Allocation', fontsize=14)
        self.memory_ax.set_xlim(0, 1)
        self.memory_ax.set_ylim(0, 1)
        self.memory_ax.set_xticks([])
        self.memory_ax.set_yticks([])
        
        # Add padding to axes
        self.memory_ax.set_position([0.125, 0.55, 0.775, 0.4])  # [left, bottom, width, height]
        
        # Page/Segment table axes
        self.table_ax = self.axes[1]
        self.table_ax.set_title('Page/Segment Table', fontsize=14)
        self.table_ax.set_xlim(0, 1)
        self.table_ax.set_ylim(0, 1)
        self.table_ax.set_xticks([])
        self.table_ax.set_yticks([])
        
        # Add padding to axes
        self.table_ax.set_position([0.125, 0.1, 0.775, 0.4])  # [left, bottom, width, height]
        # Create matplotlib figure with two subplots
        self.fig, self.axes = plt.subplots(2, 1, figsize=(12, 8))
        self.fig.tight_layout(pad=4.0)  # Increased padding between subplots
        self.process_colors = {}
        self.color_cycle = iter(mcolors.TABLEAU_COLORS)
            
            # Cache for optimization
        self.memory_patches = []
        self.page_table_patches = []
            
            # Memory axes
        self.memory_ax = self.axes[0]
        self.memory_ax.set_title('Memory Allocation', fontsize=14)  # Increased title font size
        self.memory_ax.set_xlim(0, 1)
        self.memory_ax.set_ylim(0, 1)
        self.memory_ax.set_xticks([])
        self.memory_ax.set_yticks([])
            
            # Page/Segment table axes
        self.table_ax = self.axes[1]
        self.table_ax.set_title('Page/Segment Table', fontsize=14)  # Increased title font size
        self.table_ax.set_xlim(0, 1)
        self.table_ax.set_ylim(0, 1)
        self.table_ax.set_xticks([])
        self.table_ax.set_yticks([])
        
    def get_figure(self):
        """Return the matplotlib figure for embedding in tkinter"""
        return self.fig
    
    def _get_process_color(self, process_id):
        if process_id is None:
            return 'lightgrey'
        if process_id not in self.process_colors:
            try:
                self.process_colors[process_id] = next(self.color_cycle)
            except StopIteration:
                self.color_cycle = iter(mcolors.TABLEAU_COLORS)
                self.process_colors[process_id] = next(self.color_cycle)
        return self.process_colors[process_id]

    def update_memory_view(self, memory_snapshot, total_memory_size):
        for patch in self.memory_patches:
            patch.remove()
        self.memory_patches = []
        
        # Adjust height and position to provide more space for text
        height = 0.6  # Reduced height to leave more room for labels
        y_pos = 0.25  # Moved up slightly to center in available space
        
        for block in memory_snapshot:
            start_pct = block['start'] / total_memory_size
            width_pct = block['size'] / total_memory_size
            
            color = self._get_process_color(block['process_id'])
            rect = patches.Rectangle((start_pct, y_pos), width_pct, height, 
                                    facecolor=color, edgecolor='black', linewidth=1)
            self.memory_ax.add_patch(rect)
            self.memory_patches.append(rect)
            
            # Only add process text if block is wide enough
            if block['size'] / total_memory_size > 0.05:
                text_x = start_pct + width_pct / 2
                text_y = y_pos + height / 2
                text = f"P{block['process_id']}" if block['process_id'] is not None else "Free"
                text_obj = self.memory_ax.text(text_x, text_y, text, ha='center', va='center', fontsize=12)
                self.memory_patches.append(text_obj)
            
            # Staggered position for address labels to prevent overlap
            index = memory_snapshot.index(block)
            if index % 2 == 0:
                # Top position for even-indexed blocks
                start_text = self.memory_ax.text(start_pct, y_pos + height + 0.05, f"{block['start']}", 
                                            ha='center', va='bottom', fontsize=10)
            else:
                # Bottom position for odd-indexed blocks
                start_text = self.memory_ax.text(start_pct, y_pos - 0.05, f"{block['start']}", 
                                            ha='center', va='top', fontsize=10)
            self.memory_patches.append(start_text)
            
            # Only add end address for the last block
            if block == memory_snapshot[-1]:
                end_text = self.memory_ax.text(start_pct + width_pct, y_pos - 0.05, f"{block['end']}", 
                                        ha='center', va='top', fontsize=10)
                self.memory_patches.append(end_text)
        
        self.memory_ax.set_title('Memory Allocation', fontsize=14)

    def update_page_table_view(self, page_table_snapshot, page_size, total_memory_size, method):
        # Clear the axis first
        self.table_ax.clear()
        
        # Carefully handle patch removal with error protection
        for patch in self.page_table_patches:
            try:
                if patch in self.table_ax.patches or hasattr(patch, 'remove'):
                    patch.remove()
            except (NotImplementedError, ValueError):
                # Skip items that can't be removed
                pass
        
        # Reset the patches list
        self.page_table_patches = []
        
        # Set up common axis properties
        self.table_ax.set_xlim(0, 1)
        self.table_ax.set_ylim(0, 1)
        self.table_ax.set_xticks([])
        self.table_ax.set_yticks([])
        
        if method == "paging":
            num_frames = len(page_table_snapshot)
            # Calculate optimal grid size based on number of frames
            grid_size = max(2, int(np.ceil(np.sqrt(num_frames))))
            
            # Adjust cell dimensions to leave more padding
            cell_width = 0.9 / grid_size
            cell_height = 0.9 / grid_size
            
            # Start with a margin from edges
            start_x = 0.05
            start_y = 0.95
            
            for i, frame in enumerate(page_table_snapshot):
                row = i // grid_size
                col = i % grid_size
                
                x = start_x + col * (cell_width * 1.1)  # Add 10% spacing between cells
                y = start_y - (row + 1) * (cell_height * 1.1)  # Add 10% spacing between rows
                
                color = self._get_process_color(frame['process_id'])
                rect = patches.Rectangle((x, y), cell_width, cell_height,
                                        facecolor=color, edgecolor='black', linewidth=1)
                self.table_ax.add_patch(rect)
                self.page_table_patches.append(rect)
                
                text = f"F{frame['frame_id']}"
                if frame['process_id'] is not None:
                    text += f"\nP{frame['process_id']}"
                text_obj = self.table_ax.text(x + cell_width/2, y + cell_height/2, 
                                            text, ha='center', va='center', fontsize=10)
                self.page_table_patches.append(text_obj)
            
            self.table_ax.set_title('Page Table', fontsize=14)
            
        else:  # segmentation
            self.table_ax.set_title('Segment Table', fontsize=14)

            segments = [block for block in page_table_snapshot if block['process_id'] is not None]

            table_start_x = 0.1
            table_start_y = 0.9
            table_width = 0.8
            col_width = table_width / 4

            # Header row
            header_y = table_start_y
            header_process = self.table_ax.text(table_start_x + col_width*0, header_y, "Process", 
                                ha='center', fontsize=11, weight='bold')
            header_base = self.table_ax.text(table_start_x + col_width*1, header_y, "Base", 
                                ha='center', fontsize=11, weight='bold')
            header_limit = self.table_ax.text(table_start_x + col_width*2, header_y, "Limit", 
                                ha='center', fontsize=11, weight='bold')
            header_end = self.table_ax.text(table_start_x + col_width*3, header_y, "End", 
                                ha='center', fontsize=11, weight='bold')
            self.page_table_patches.extend([header_process, header_base, header_limit, header_end])

            # Separator line
            line = patches.Rectangle((table_start_x - 0.05, header_y - 0.05), 
                                    table_width + 0.1, 0.01, facecolor='black')
            self.table_ax.add_patch(line)
            self.page_table_patches.append(line)

            # Spacing setup
            initial_row_gap = 0.13   # Increased spacing between header and first row
            row_spacing = 0.12
            max_rows = min(len(segments), int(0.8 / row_spacing))

            for i, segment in enumerate(segments[:max_rows]):
                row_y = header_y - initial_row_gap - (i * row_spacing)

                color = self._get_process_color(segment['process_id'])
                proc_indicator = patches.Rectangle((table_start_x - 0.03, row_y - 0.02), 0.02, 0.02,
                                                facecolor=color, edgecolor='black')
                self.table_ax.add_patch(proc_indicator)
                self.page_table_patches.append(proc_indicator)

                pid_text = self.table_ax.text(table_start_x + col_width*0, row_y, f"P{segment['process_id']}", 
                                            ha='center', fontsize=10)
                base_text = self.table_ax.text(table_start_x + col_width*1, row_y, f"{segment['start']}", 
                                            ha='center', fontsize=10)
                limit_text = self.table_ax.text(table_start_x + col_width*2, row_y, f"{segment['size']}", 
                                                ha='center', fontsize=10)
                end_text = self.table_ax.text(table_start_x + col_width*3, row_y, f"{segment['end']}", 
                                            ha='center', fontsize=10)

                self.page_table_patches.extend([pid_text, base_text, limit_text, end_text])

            if len(segments) > max_rows:
                more_text = self.table_ax.text(0.5, header_y - initial_row_gap - (max_rows * row_spacing), 
                                            f"+ {len(segments) - max_rows} more segments", 
                                            ha='center', fontsize=9, style='italic')
                self.page_table_patches.append(more_text)

            self.table_ax.figure.canvas.draw_idle()

    def update_visualization(self, memory_snapshot, page_table_snapshot, stats, events,
                             total_memory_size, page_size, method):
        """
        Update the visualization for both memory allocation and page/segment table.
        
        Parameters:
        - memory_snapshot: List of memory blocks with their allocation status
        - page_table_snapshot: List of page table entries (for paging) or segment table entries (for segmentation)
        - stats: Dictionary of memory statistics
        - events: List of recent memory events
        - total_memory_size: Total size of memory
        - page_size: Size of each page (for paging)
        - method: Allocation method ("paging" or "segmentation")
        """
        self.update_memory_view(memory_snapshot, total_memory_size)
    
        # Update page or segment table view based on method
        if method == "segmentation":
            # For segmentation, use memory_snapshot for the segment table
            self.update_page_table_view(memory_snapshot, page_size, total_memory_size, method)
        else:
            # For paging, use page_table_snapshot
            self.update_page_table_view(page_table_snapshot, page_size, total_memory_size, method)

        # Make sure the layout is properly adjusted
        self.fig.tight_layout(pad=4.0)
        
        # Ensure axes don't overlap
        # Change in update_visualization method
        self.memory_ax.set_position([0.1, 0.58, 0.85, 0.38])  # Wider, slightly higher
        self.table_ax.set_position([0.1, 0.08, 0.85, 0.43])  # Give more space to the table

from tkinter import ttk, font

from tkinter import ttk, font

class ModernUI:
    BACKGROUND = "#f5f5f7"
    FRAME_BG = "#ffffff"
    PRIMARY = "#0066cc"
    SECONDARY = "#5ac8fa"
    # Changed SUCCESS from green to blue
    SUCCESS = "#1a73e8"
    WARNING = "#ff9500"
    DANGER = "#ff3b30"
    TEXT = "#1d1d1f"
    SUBTEXT = "#86868b"
    
    @classmethod
    def apply_theme(cls, root):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background=cls.FRAME_BG)
        style.configure('TLabel', background=cls.FRAME_BG, foreground=cls.TEXT)
        style.configure('TButton', background=cls.PRIMARY, foreground='white', borderwidth=0)
        style.map('TButton', 
                  background=[('active', cls.SECONDARY), ('pressed', cls.PRIMARY)],
                  relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        style.configure('Primary.TButton', background=cls.PRIMARY, foreground='white')
        style.map('Primary.TButton',
                  background=[('active', cls.SECONDARY), ('pressed', cls.PRIMARY)])
        
        style.configure('Success.TButton', background=cls.SUCCESS, foreground='white')
        style.map('Success.TButton',
                  background=[('active', cls.SECONDARY), ('pressed', cls.SUCCESS)])
        
        style.configure('Danger.TButton', background=cls.DANGER, foreground='white')
        style.map('Danger.TButton',
                  background=[('active', '#ff6b60'), ('pressed', cls.DANGER)])
        
        style.configure('TLabelframe', background=cls.FRAME_BG)
        style.configure('TLabelframe.Label', background=cls.FRAME_BG, foreground=cls.PRIMARY, font=('Helvetica', 12, 'bold'))  # Increased font size
        
        style.configure('TScale', background=cls.FRAME_BG, troughcolor=cls.SUBTEXT)
        style.configure('TCombobox', background=cls.FRAME_BG, fieldbackground=cls.FRAME_BG)
        style.map('TCombobox', fieldbackground=[('readonly', cls.FRAME_BG)])
        
        root.configure(background=cls.BACKGROUND)
        
        # Increased font sizes
        return {
            'title': font.Font(family='Helvetica', size=14, weight='bold'),  # Increased size
            'heading': font.Font(family='Helvetica', size=12, weight='bold'),  # Increased size
            'normal': font.Font(family='Helvetica', size=11),  # Increased size
            'small': font.Font(family='Helvetica', size=10)  # Increased size
        }