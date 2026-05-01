"""
William Reisman
ENAE380 - Section 102

tailbuilder.py script creates tail building interface to use in sandbox mode
"""
#tkinter imports
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as mb

#matplotlib imports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#rocketpy imports
from rocketpy import Tail

import numpy as np

import os #file path management

#create and return default tail object using RocketPy
def create_tail():
    tail = Tail(
        top_radius=0.0635, 
        bottom_radius=0.0435, 
        length=0.060,
        rocket_radius=0.0635
    )
    tail.position = -1.0 #must be assigned
    return tail


# Tkinter UI class for viewing and editing tail
class TailEditor(tk.Tk):
    def __init__(self):
        # initialize the tail editor window and UI
        super().__init__()
        self.title("Tail Editor")
        self.geometry("1400x800")

        # create default tail
        self.tail = create_tail()

        #make UI panels
        self._build_left_panel()
        self._build_right_panel()

        #draw initial tail
        self.draw_tail()

    #creates the left panel with tail parameter inputs. includes top radius, bottom radius, length, and save functionality.
    def _build_left_panel(self):
        # create left frame
        left = ttk.Frame(self, padding=10)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="Tail Parameters", font=("Arial", 14)).pack(pady=10)

        # Variables in tk linked to each of the tail parameters
        self.top_rad = tk.DoubleVar(value=self.tail.top_radius)
        self.bot_rad = tk.DoubleVar(value=self.tail.bottom_radius)
        self.length_var = tk.DoubleVar(value=self.tail.length)

        #variable to store filename in tk
        self.file_name = tk.StringVar(value="untitled_tail")

        #list of tuples to pair each label to its variable
        entries = [
            ("Top Radius", self.top_rad),
            ("Bottom Radius", self.bot_rad),
            ("Length", self.length_var),
        ]

        # Creates label and spinbox for user to enter values for each variable
        for label, var in entries:
            ttk.Label(left, text=label).pack(anchor="c", pady=(10, 0))
            ttk.Spinbox(left, textvariable=var, width=20, justify="center", from_=0, to=50, increment=0.1).pack(anchor="c")

        #Creates button to update the tail with user's values, calls update_tail function
        ttk.Button(left, text="Update Tail", command=self.update_tail,width=20).pack(
            pady=20
        )

        #creates file name entry box
        ttk.Label(left, text="File Name").pack(anchor="c", pady=(10, 0))
        ttk.Entry(left, textvariable=self.file_name, width=20, justify="center").pack(anchor="c")

        #Creates button to save tail configuration
        ttk.Button(left, text="Save and Export", command=self.save_tail,width=20).pack(
            pady=20
        )

    # create the right UI panel with a matplotlib figure to represent tail
    def _build_right_panel(self):
        # create right frame
        right = ttk.Frame(self)
        right.pack(side="right", fill="both", expand=True)

        #frame for matplotlib figure
        self.part_frame = ttk.Frame(right)
        self.part_frame.pack(side="left", fill="both", expand=True)

        #put the matplotlib figure into the tk canvas
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.part_frame)
        # fill the canvas entirely
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        #part info frame
        self.info_panel = ttk.Frame(right, padding=30, width=200)
        self.info_panel.pack(side="right", fill="y")
        ttk.Label(self.info_panel, text="Part Info", font=("Arial", 14)).pack(pady=0)

        #part mass label
        ttk.Label(self.info_panel, text="Mass", font=("Arial", 20)).pack(pady=10)
        self.mass_value_label = ttk.Label(self.info_panel, text="0", font=("Arial", 20),foreground="blue")
        self.mass_value_label.pack(pady=10)

        #part volume label
        ttk.Label(self.info_panel, text="Volume", font=("Arial", 20)).pack(pady=10)
        self.vol_value_label = ttk.Label(self.info_panel, text="0", font=("Arial", 20),foreground="blue")
        self.vol_value_label.pack(pady=10)

    # updates tail object with current parameter values from the tk UI
    # checks if inputs are valid and draws the tail
    def update_tail(self):
        self.saveable = True #store if part is valid

        #check that dimensions are <50m
        if self.bot_rad.get() > 50.0 or self.top_rad.get() > 50.0 or self.length_var.get() > 50.0:
            mb.showwarning("Invalid Part Size","Dimensions are too large (max 50m), adjust part parameters.")
            self.saveable =  False
            return
        
        #check that dimensions are >0
        if self.bot_rad.get() <=0 or self.top_rad.get() <=0 or self.length_var.get() <=0:
            mb.showwarning("Invalid Part Size","Dimensions cannot be <=0, adjust part parameters.")
            self.saveable = False
            return
        
        #make sure the center of pressure is defined
        r = self.top_rad.get() / self.bot_rad.get()
        try:
            cpz = (self.length_var.get() / 3) * (1 + (1 - r) / (1 - r**2))
        except ZeroDivisionError:
            mb.showwarning("Part Invalid","Center of pressure is undefined. Adjust part parameters.")
            self.saveable = False
            return
        
        #update variables with the ui values
        self.tail.bottom_radius = self.bot_rad.get()
        self.tail.top_radius = self.top_rad.get()
        self.tail.length = self.length_var.get()

        #draw the updated tail
        self.draw_tail()

    def save_tail(self):
        #first, make sure tail is updated
        self.update_tail()

        #get the file name from the ui
        filename = self.file_name.get()

        #ensure file name is valid
        illegal_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        if not filename or any(char in filename for char in illegal_chars):
            mb.showerror("Invalid Filename", "Please enter a valid file name.")
            return

        #create part directory if none exists
        os.makedirs("data/tails", exist_ok=True)

        #create file_path string using part name
        file_path = "data/tails/"+filename+".txt"

        # store list of entries for the file with corresponding vars
        entries = [
            ("Top Radius", self.top_rad.get()),
            ("Bottom Radius", self.bot_rad.get()),
            ("Length", self.length_var.get()),
            ("Volume", self.tail_vol(thickness=0.1*self.top_rad.get())), #assume thickness is 10% of top radius
            ("Mass", self.tail_mass()),
            ("CoM", self.tail_CoM()),
            ("Cost", 0.0), #makes custom parts free
            ("Level", 10) #makes custom parts unusable in career mode
        ]
        
        if self.saveable:
            #if valid, write entries to the txt file
            with open(file_path, "w") as f:
                for label, var in entries:
                    f.write(str(label)+ ": " + str(var) + "\n") #write each line as label: var

            mb.showinfo("Save Successful", filename +" was successfully saved.") 


    def tail_vol(self, thickness=0.0):
        """
        Calculates the volume of the tail shell using numerical integration
        
        Parameters:
            thickness (float): wall thickness of the tail shell (m)
            if 0, treats as solid.
        
        Returns:
            float: volume in m^3
        """
        # get tail shape profile from RocketPy
        x, y = self.tail.shape_vec
        x = np.array(x)
        y = np.array(y)

        # store inner radius if hollow
        if thickness > 0:
            y_inner = y - thickness
        else:
            y_inner = np.zeros_like(y) #otherwise, y_inner is array of 0s

        # calculate cross-sectional area at each position
        A = np.pi * (y**2 - y_inner**2)

        # use trapezoidal integration to find volume
        volume = np.trapz(A, x)

        return volume
    
    # calculates and returns mass of tail (kg) using tail_vol()
    def tail_mass(self):
        density = 500.0 #assumed density in kg/m^3
        return self.tail_vol(thickness=0.1*self.top_rad.get()) * density #assume thickness is 10% of top radius
    
    def tail_CoM(self):
        """
        Calculates the center of mass position in the axial direction
        Uses first moment of area integration
        
        Returns:
            float: distance from top radius to CoM (m)
        """
        
        # Generate 100 point shape vector instead of using just 2 points
        x = np.linspace(0, self.tail.length, 100)
        top_rad = self.top_rad.get()
        bot_rad = self.bot_rad.get()
        length = self.length_var.get()

        #get all radii using equation of line (because tail is a truncated cone)
        y = top_rad + (bot_rad - top_rad) * (x / length)
        
        tail_thickness = 0.1*top_rad
        if tail_thickness > 0:
            y_inner = y - tail_thickness
        else:
            y_inner = np.zeros_like(y)

        # calculate cross-section area at each position
        A = np.pi * (y**2 - y_inner**2)
        # calculate first moment of area: M = ∫x * A(x) dx
        M = np.trapz(x * A, x)
        #store nosecone volume
        volume = self.tail_vol(thickness=tail_thickness)
        # return CoM
        return M / volume
        
    
    # draws the tail on the matplotlib figure using RocketPy data, shows the center of mass
    def draw_tail(self):
        #clear last plot
        self.ax.clear()
        self.ax.set_aspect("equal") #have axes scale with the tail
        self.ax.grid(True)

        # RocketPy stores tail shape in tail.shape_vec
        x, y = self.tail.shape_vec

        # Plot top edge of the tail
        self.ax.plot(x, y, color="blue", linewidth=2)
        # Plot bottom edge of tail
        self.ax.plot(x, [-i for i in y], color="blue", linewidth=2)

        #top radius line using first shape index
        top_x = x[0]
        top_y = y[0]
        self.ax.plot([top_x, top_x], [-top_y, top_y], color="blue", linewidth=2)

        #bottom radius line using last shape index
        bot_x = x[-1]
        bot_y = y[-1]
        self.ax.plot([bot_x, bot_x], [-bot_y, bot_y], color="blue", linewidth=2)

        #draw CoM and corresponding legend
        com_x = self.tail_CoM()
        self.ax.plot(com_x, 0, 'bo', markersize=5, label='Center of Mass')
        self.ax.legend()

        # set the plot title and labels
        self.ax.set_title("Tail Builder")
        self.ax.set_xlabel("Axial Distance (m)")
        self.ax.set_ylabel("Radius (m)")

        # draw the plot
        self.canvas.draw()

        #update the mass label if it exists
        if hasattr(self, 'mass_value_label'):
            self.mass_value_label.config(text=str(round(self.tail_mass(),4))+" (kg)")

        #update the volume label if it exists
        if hasattr(self, 'vol_value_label'):
            self.vol_value_label.config(text=str(round(self.tail_vol(thickness=0.1*self.top_rad.get()),4))+" (m^3)") #assume thickness is always 10% of the top radius

if __name__ == "__main__":
    app = TailEditor()
    app.mainloop() #start tkinter and keeps window running
