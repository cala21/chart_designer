import tkinter as tk
from tkinter import messagebox, filedialog, Canvas, colorchooser
import matplotlib
matplotlib.use('TkAgg')  # Force matplotlib to use TkAgg backend
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# Fix for PyInstaller matplotlib backend issues
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    matplotlib.rcParams['backend'] = 'TkAgg'

# Global variable to store custom colors
custom_colors = {}

def get_colors(n):
    cmap = matplotlib.colormaps['tab20']
    colors = []
    for i in range(n):
        if i in custom_colors:
            # Use custom color if set
            colors.append(custom_colors[i])
        else:
            # Use default color from colormap
            colors.append(cmap(i / n))
    return colors

def hex_from_rgb(rgb):
    return '#%02x%02x%02x' % tuple(int(255*x) for x in rgb[:3])

def on_color_click(index, swatch, label_text):
    """Handle color swatch click to open color picker"""
    # Open color chooser dialog
    color = colorchooser.askcolor(
        title=f"Choose color for '{label_text}'",
        initialcolor=swatch['bg']
    )
    
    if color[0]:  # If a color was selected (not cancelled)
        # Convert RGB tuple to matplotlib format (0-1 range)
        rgb_matplotlib = tuple(c/255.0 for c in color[0])
        custom_colors[index] = rgb_matplotlib
        
        # Update the swatch color
        hex_color = color[1]  # This is the hex color from colorchooser
        swatch.config(bg=hex_color)
        
        # Update the preview
        on_update_labels()

def reset_colors():
    """Reset all colors to default"""
    global custom_colors
    custom_colors.clear()
    on_update_labels()

def preview_colors(labels):
    for widget in color_preview_frame.winfo_children():
        widget.destroy()
    
    colors = get_colors(len(labels))
    for i, label in enumerate(labels):
        hex_color = hex_from_rgb(colors[i])
        
        # Create clickable color swatch
        swatch = Canvas(
            color_preview_frame, width=20, height=20, bg=hex_color, 
            highlightthickness=1, highlightbackground='#888',
            cursor='hand2'  # Change cursor to indicate clickable
        )
        swatch.grid(row=i, column=0, padx=(0, 5), pady=2)
        
        # Bind click event to open color picker
        swatch.bind("<Button-1>", lambda e, idx=i, sw=swatch, lbl=label: on_color_click(idx, sw, lbl))
        
        # Add tooltip-like behavior
        def on_enter(e, sw=swatch):
            sw.config(highlightbackground='#333', highlightthickness=2)
        
        def on_leave(e, sw=swatch):
            sw.config(highlightbackground='#888', highlightthickness=1)
        
        swatch.bind("<Enter>", on_enter)
        swatch.bind("<Leave>", on_leave)
        
        lbl = tk.Label(color_preview_frame, text=label, font=("Arial", 11))
        lbl.grid(row=i, column=1, sticky='w', pady=2)
    
    # Add reset colors button
    if labels:  # Only show if there are labels
        reset_btn = tk.Button(
            color_preview_frame, text="Reset Colors", 
            command=reset_colors, font=("Arial", 9),
            relief="flat", bg="#f0f0f0", fg="#666"
        )
        reset_btn.grid(row=len(labels), column=0, columnspan=2, pady=(10, 0), sticky='w')
    
    color_preview_frame.update()

def make_chart(save_path=None):
    chart_type = var_chart_type.get()
    title = entry_title.get().strip()
    labels = [x.strip() for x in entry_labels.get().strip().split(',') if x.strip()]
    sizes_str = entry_sizes.get().strip().split(',')
    
    # Get checkbox states
    show_title = var_show_title.get()
    show_labels = var_show_labels.get()
    show_percentages = var_show_percentages.get()

    if not title or not labels or not entry_sizes.get().strip():
        messagebox.showerror("Input Error", "Please fill out all fields!")
        return

    try:
        sizes = [float(x) for x in sizes_str]
    except ValueError:
        messagebox.showerror("Input Error", "Values must be numbers, comma-separated (e.g. 10,20,30)")
        return

    if len(labels) != len(sizes):
        messagebox.showerror(
            "Input Error",
            f"Labels and values must have the same number of items.\n"
            f"Labels: {len(labels)}, Values: {len(sizes)}"
        )
        return

    colors = get_colors(len(labels))
    total = sum(sizes)
    percentages = [size / total * 100 for size in sizes]

    # Consistent text properties for all charts
    label_props = {'fontsize': 14, 'weight': 'medium', 'color': '#222'}
    pct_props = {'fontsize': 12, 'weight': 'bold', 'color': 'white'}
    pct_bbox = dict(boxstyle='round,pad=0.3', fc='#364FC7', alpha=0.9, ec='none')
    title_props = {'fontsize': 22, 'fontweight': 'bold', 'color': '#1a1a1a', 'pad': 30}

    fig, ax = plt.subplots(figsize=(7, 7), dpi=130)
    
    if chart_type == 'pie':
        # Calculate if slices are too small for internal labels
        min_pct_for_internal = 8.0
        
        # Determine what to show in pie chart
        pie_labels = labels if show_labels else None
        
        # Always use autopct='' and handle percentages manually
        wedges, texts, autotexts = ax.pie(
            sizes, labels=pie_labels, colors=colors,
            autopct='', startangle=90,
            wedgeprops=dict(edgecolor='#FAFAFA', linewidth=3, alpha=0.92, antialiased=True),
            textprops=label_props,
            labeldistance=1.15
        )
        
        # Add percentages manually if enabled
        if show_percentages:
            for i, (pct, wedge) in enumerate(zip(percentages, wedges)):
                ang = (wedge.theta2 - wedge.theta1) / 2. + wedge.theta1
                if pct >= min_pct_for_internal:
                    # Internal percentage
                    x = 0.7 * np.cos(np.radians(ang))
                    y = 0.7 * np.sin(np.radians(ang))
                    ax.text(x, y, f'{pct:.1f}%', ha='center', va='center',
                           color=pct_props['color'], fontsize=pct_props['fontsize'],
                           weight=pct_props['weight'], bbox=pct_bbox)
                else:
                    # External percentage for small slices
                    x = 1.15 * np.cos(np.radians(ang))
                    y = 1.1 * np.sin(np.radians(ang))
                    ax.text(x, y, f'{pct:.1f}%', ha='center', va='center',
                           color=pct_props['color'], fontsize=pct_props['fontsize']-1,
                           weight=pct_props['weight'], bbox=pct_bbox)
        
        if show_title:
            ax.set_title(title, **title_props)
        ax.axis('equal')
        
    elif chart_type == 'donut':
        # Calculate if slices are too small for internal labels
        min_pct_for_internal = 8.0
        
        # Determine what to show in donut chart
        donut_labels = labels if show_labels else None
        
        # Always use autopct='' and handle percentages manually
        wedges, texts, autotexts = ax.pie(
            sizes, labels=donut_labels, colors=colors,
            autopct='', startangle=90,
            wedgeprops=dict(width=0.5, edgecolor='#FAFAFA', linewidth=3, alpha=0.95, antialiased=True),
            textprops=label_props,
            labeldistance=1.15
        )
        centre_circle = plt.Circle((0,0), 0.50, fc='white', lw=0)
        fig.gca().add_artist(centre_circle)
        
        # Add percentages manually if enabled
        if show_percentages:
            for i, (pct, wedge) in enumerate(zip(percentages, wedges)):
                ang = (wedge.theta2 - wedge.theta1) / 2. + wedge.theta1
                if pct >= min_pct_for_internal:
                    # Internal percentage (in the donut ring)
                    x = 0.75 * np.cos(np.radians(ang))
                    y = 0.75 * np.sin(np.radians(ang))
                    ax.text(x, y, f'{pct:.1f}%', ha='center', va='center',
                           color=pct_props['color'], fontsize=pct_props['fontsize'],
                           weight=pct_props['weight'], bbox=pct_bbox)
                else:
                    # External percentage for small slices
                    x = 1.15 * np.cos(np.radians(ang))
                    y = 1.1 * np.sin(np.radians(ang))
                    ax.text(x, y, f'{pct:.1f}%', ha='center', va='center',
                           color=pct_props['color'], fontsize=pct_props['fontsize']-1,
                           weight=pct_props['weight'], bbox=pct_bbox)
        
        if show_title:
            ax.set_title(title, **title_props)
        ax.axis('equal')

    elif chart_type == 'radial':
        # Clear and create radial bar chart
        fig.clf()
        N = len(labels)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
        width = 2 * np.pi / N * 0.7
        ax = plt.subplot(111, polar=True)
        bars = ax.bar(
            angles, sizes, width=width, bottom=0.0, color=colors,
            edgecolor='#FFFFFF', linewidth=2, alpha=0.92
        )

        max_size = max(sizes)
        min_size = min(sizes)
        
        # Dynamic thresholds based on data distribution
        min_pct_for_internal = 8.0  # Same as pie chart
        min_size_for_internal = max_size * 0.25  # 25% of max size
        
        # Calculate dynamic label positioning
        avg_size = np.mean(sizes)
        base_label_distance = 1.08 + (0.15 * (avg_size / max_size))  # Dynamic base distance
        
        # Add percentages with better positioning if enabled
        if show_percentages:
            for i, (bar, angle, pct, size) in enumerate(zip(bars, angles, percentages, sizes)):
                r = bar.get_height()
                
                # More sophisticated percentage positioning
                if pct >= min_pct_for_internal and size >= min_size_for_internal:
                    # Internal percentage for larger bars
                    pct_position = 0.6 if pct > 15 else 0.7  # Higher position for larger percentages
                    ax.text(
                        angle, r * pct_position,
                        f"{pct:.1f}%", ha='center', va='center',
                        color=pct_props['color'], fontsize=pct_props['fontsize'],
                        fontweight=pct_props['weight'], bbox=pct_bbox
                    )
                else:
                    # External percentage for small bars - closer to the bar
                    external_radius = max(r * 0.3, max_size * 0.3)  # Minimum distance but not too far
                    ax.text(
                        angle, external_radius,
                        f"{pct:.1f}%", ha='center', va='center',
                        color=pct_props['color'], fontsize=pct_props['fontsize']-1,
                        fontweight=pct_props['weight'], bbox=pct_bbox
                    )
        
        # Add labels if enabled
        if show_labels:
            # Dynamic label positioning based on individual bar sizes
            for i, (angle, label, size) in enumerate(zip(angles, labels, sizes)):
                # Calculate dynamic label distance based on bar size
                size_factor = size / max_size
                label_distance = base_label_distance + (0.1 * size_factor)  # Closer for smaller bars
                label_radius = max_size * label_distance
                
                # Determine text alignment based on position
                ha = 'center'
                if np.cos(angle - np.pi/2) > 0.1:
                    ha = 'left'
                elif np.cos(angle - np.pi/2) < -0.1:
                    ha = 'right'
                    
                va = 'center'
                if np.sin(angle - np.pi/2) > 0.1:
                    va = 'bottom'
                elif np.sin(angle - np.pi/2) < -0.1:
                    va = 'top'
                
                ax.text(angle, label_radius, label, 
                    ha=ha, va=va, **label_props)

        if show_title:
            ax.set_title(title, **title_props)
        ax.set_ylim(0, max_size * (base_label_distance + 0.25))  # Dynamic spacing
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        ax.spines['polar'].set_visible(False)
        ax.grid(False)
        ax.set_frame_on(False)
        plt.tight_layout()

    elif chart_type == 'rose':
        fig.clf()
        N = len(labels)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
        width = 2 * np.pi / N
        radii = np.array(sizes)
        ax = plt.subplot(111, polar=True)
        bars = ax.bar(
            angles, radii, width=width, bottom=0.0, color=colors,
            edgecolor='#FAFAFA', linewidth=2, alpha=0.92
        )
        
        max_radius = max(radii)
        min_radius = min(radii)
        avg_radius = np.mean(radii)
        
        # Dynamic thresholds based on actual data distribution
        min_pct_for_internal = 8.0  # Same as pie chart
        min_radius_for_internal = max_radius * 0.2  # 20% of max radius
        
        # Calculate dynamic positioning factors
        radius_range = max_radius - min_radius
        base_label_distance = 1.12 + (0.08 * (avg_radius / max_radius))  # Dynamic base distance
        
        # Add percentages if enabled
        if show_percentages:
            for i, (bar, angle, pct, label) in enumerate(zip(bars, angles, percentages, labels)):
                r = bar.get_height()
                
                # More sophisticated percentage positioning
                if pct >= min_pct_for_internal and r >= min_radius_for_internal:
                    # Internal percentage for larger bars
                    pct_position = 0.65 if pct > 15 else 0.75  # Adjust position based on percentage
                    font_size = max(10, min(13, pct_props['fontsize'] * max(0.8, pct / 12)))
                    
                    ax.text(
                        angle, r * pct_position,
                        f"{pct:.1f}%", ha='center', va='center',
                        color=pct_props['color'], fontsize=font_size,
                        fontweight=pct_props['weight'],
                        bbox=pct_bbox
                    )
                else:
                    # External percentage for small bars - adaptive positioning
                    external_radius = max(r * 0.3, max_radius * 0.3)  # Closer to small bars
                    font_size = max(9, min(11, pct_props['fontsize'] * 0.85))
                    
                    ax.text(
                        angle, external_radius,
                        f"{pct:.1f}%", ha='center', va='center',
                        color=pct_props['color'], fontsize=font_size,
                        fontweight=pct_props['weight'],
                        bbox=pct_bbox
                    )
        
        # Add labels if enabled
        if show_labels:
            # Dynamic label positioning based on individual bar sizes
            for i, (angle, label, radius) in enumerate(zip(angles, labels, radii)):
                # Calculate dynamic label distance based on bar size
                radius_factor = radius / max_radius
                label_distance = base_label_distance + (0.06 * radius_factor)  # Closer for smaller bars
                label_radius = max_radius * label_distance
                
                # Determine text alignment based on position (like pie chart)
                ha = 'center'
                if np.cos(angle - np.pi/2) > 0.1:
                    ha = 'left'
                elif np.cos(angle - np.pi/2) < -0.1:
                    ha = 'right'
                    
                va = 'center'
                if np.sin(angle - np.pi/2) > 0.1:
                    va = 'bottom'
                elif np.sin(angle - np.pi/2) < -0.1:
                    va = 'top'
                
                # Position label without rotation
                ax.text(
                    angle, label_radius,
                    label,
                    ha=ha, va=va,
                    rotation=0,  # No rotation for better readability
                    **label_props
                )

        # Set chart limits and styling with dynamic spacing
        ax.set_ylim(0, max_radius * (base_label_distance + 0.2))
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        ax.spines['polar'].set_visible(False)
        ax.grid(False)
        ax.set_axisbelow(True)
        ax.set_frame_on(False)
        if show_title:
            ax.set_title(title, **title_props)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, bbox_inches='tight', dpi=150, transparent=True)
        plt.close(fig)
        messagebox.showinfo("Saved!", f"Chart saved as:\n{save_path}")
    else:
        plt.show()

def on_update_labels(event=None):
    labels = [x.strip() for x in entry_labels.get().strip().split(',') if x.strip()]
    if labels:
        preview_colors(labels)
    else:
        for widget in color_preview_frame.winfo_children():
            widget.destroy()

def save_chart():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        title="Save Chart As..."
    )
    if file_path:
        make_chart(save_path=file_path)

# ---- Tkinter GUI ----
root = tk.Tk()
root.title("Chart Designer")
root.geometry("570x650")  # Increased height for new checkboxes
root.resizable(False, False)

font_label = ("Arial", 13, "bold")
font_entry = ("Arial", 12)
padding = {'padx': 8, 'pady': 4}

tk.Label(root, text="Chart Title:", font=font_label).grid(row=0, column=0, sticky='e', **padding)
entry_title = tk.Entry(root, width=36, font=font_entry)
entry_title.insert(0, "My Chart")
entry_title.grid(row=0, column=1, sticky='w', **padding)

tk.Label(root, text="Labels (comma):", font=font_label).grid(row=1, column=0, sticky='e', **padding)
entry_labels = tk.Entry(root, width=36, font=font_entry)
entry_labels.insert(0, "Contact,Connect,Curate,Conclude,Reconnect")
entry_labels.grid(row=1, column=1, sticky='w', **padding)
entry_labels.bind("<KeyRelease>", on_update_labels)

tk.Label(root, text="Values (comma):", font=font_label).grid(row=2, column=0, sticky='e', **padding)
entry_sizes = tk.Entry(root, width=36, font=font_entry)
entry_sizes.insert(0, "20,20,20,20,20")
entry_sizes.grid(row=2, column=1, sticky='w', **padding)

tk.Label(root, text="Chart Type:", font=font_label).grid(row=3, column=0, sticky='e', **padding)
var_chart_type = tk.StringVar(value="pie")
chart_type_menu = tk.OptionMenu(root, var_chart_type, "pie", "donut", "rose", "radial")
chart_type_menu.config(font=font_entry)
chart_type_menu.grid(row=3, column=1, sticky='w', **padding)

# Display Options Section
tk.Label(root, text="Display Options:", font=font_label).grid(row=4, column=0, sticky='e', **padding)
display_frame = tk.Frame(root)
display_frame.grid(row=4, column=1, sticky='w', **padding)

# Checkboxes for display options (all pre-checked)
var_show_title = tk.BooleanVar(value=True)
var_show_labels = tk.BooleanVar(value=True)
var_show_percentages = tk.BooleanVar(value=True)

tk.Checkbutton(display_frame, text="Show Title", variable=var_show_title, font=("Arial", 11)).grid(row=0, column=0, sticky='w', padx=(0, 15))
tk.Checkbutton(display_frame, text="Show Labels", variable=var_show_labels, font=("Arial", 11)).grid(row=0, column=1, sticky='w', padx=(0, 15))
tk.Checkbutton(display_frame, text="Show Percentages", variable=var_show_percentages, font=("Arial", 11)).grid(row=0, column=2, sticky='w')

tk.Label(root, text="Colors (click to edit):", font=font_label).grid(row=5, column=0, sticky='ne', **padding)
color_preview_frame = tk.Frame(root)
color_preview_frame.grid(row=5, column=1, sticky='w', **padding)
on_update_labels()

btn_frame = tk.Frame(root)
btn_frame.grid(row=10, columnspan=2, pady=(28, 8))
tk.Button(
    btn_frame, text="Show Chart", command=lambda: make_chart(None), font=("Arial", 14, "bold"),
    width=16, height=2, relief="raised"
).grid(row=0, column=0, padx=18)
tk.Button(
    btn_frame, text="Save as PNG", command=save_chart, font=("Arial", 14, "bold"),
    width=16, height=2, relief="raised"
).grid(row=0, column=1, padx=18)

root.mainloop()