"""
William Reisman
ENAE380 - Section 102

noseconebuilder.py script creates nosecone building interface to use in sandbox mode
"""
#tkinter imports
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as mb

#matplotlib imports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#rocketpy imports
from rocketpy import NoseCone

import numpy as np

import os #file path management

#create and return default nosecone object using RocketPy
def create_nosecone():
    nosecone = NoseCone(
        length=0.5, kind="von karman", base_radius=0.1, power = 0.5
    )
    return nosecone

# Tkinter UI class for viewing and editing fins
class NoseconeEditor(tk.Tk):
    # initialize the nosecone editor window and UI
    def __init__(self):
        super().__init__()
        self.title("Nosecone Editor")
        self.geometry("1400x800")

        # create default nosecone
        self.nosecone = create_nosecone()

        # make UI panels
        self._build_left_panel()
        self._build_right_panel()

        #draw initial nosecone
        self.draw_nosecone()

    # creates the left panel with nosecone parameter inputs. includes length, radius, type, and save functionality.
    def _build_left_panel(self):
        # create left frame
        left = ttk.Frame(self, padding=10)
        left.pack(side="left", fill="y")

        #title
        ttk.Label(left, text="Nosecone Parameters", font=("Arial", 14)).pack(pady=10)

        # Variables in tk linked to each of the nosecone parameters
        self.length_var = tk.DoubleVar(value=self.nosecone.length)
        self.radius_var = tk.DoubleVar(value=self.nosecone.base_radius)
        self.kind_var = tk.StringVar(value=self.nosecone.kind)

        #variable to store export filename in tk
        self.file_name = tk.StringVar(value="untitled_nosecone")

        ttk.Label(left, text="Length").pack(anchor="c", pady=(10, 0))
        #add spinbox to control nosecone length
        ttk.Spinbox(left, textvariable=self.length_var, width=20, justify="center", from_=0, to=50, increment=0.1).pack(anchor="c")

        ttk.Label(left, text="Base Radius").pack(anchor="c", pady=(10, 0))
        #add spinbox to control base radius
        ttk.Spinbox(left, textvariable=self.radius_var, width=20, justify="center", from_=0, to=50, increment=0.1).pack(anchor="c")

        #Nosecone kind dropdown select
        ttk.Label(left, text="Nosecone Type").pack(pady=(10, 0))
       
        # Tk combobox dropdown with all nosecone types
        self.fin_dropdown = ttk.Combobox(
            left, 
            textvariable=self.kind_var, 
            values=["conical",
            "ogive",
            "elliptical",
            "tangent",
            "von karman",
            "parabolic",
            "powerseries",
            "lvhaack"],
            state="readonly"
            )
        self.fin_dropdown.pack(pady=5)
    
        #Creates button to update the nosecone with user's values, calls update_nosecone function
        ttk.Button(left, text="Update Nosecone", command=self.update_nosecone,width=20).pack(
            pady=20
        )

        #creates file name entry box
        ttk.Label(left, text="File Name").pack(anchor="c", pady=(10, 0))
        ttk.Entry(left, textvariable=self.file_name, width=20, justify="center").pack(anchor="c")

        #Creates button to save nosecone configuration, calls save_nosecone()
        ttk.Button(left, text="Save and Export", command=self.save_nosecone,width=20).pack(
            pady=20
        )

    # create the right UI panel with a matplotlib figure to represent nosecone
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

    # updates nosecone object with current parameter values from the tk UI
    # checks if inputs are valid and draws the nosecone
    def update_nosecone(self):

        self.saveable = True #store if part is valid

        #check that dimensions are <50m
        if self.length_var.get() > 50.0 or self.radius_var.get() > 50.0:
            mb.showwarning("Invalid Part Size","Dimensions are too large (max 50m), adjust part parameters.")
            self.saveable = False
            return
        
        #check that dimensions are >0
        if self.length_var.get() <= 0 or self.radius_var.get() <= 0:
            mb.showwarning("Invalid Part Size","Dimensions cannot be <=0, adjust part parameters.")
            self.saveable = False
            return
        
        #update variables with the ui values
        self.nosecone.length = self.length_var.get()
        self.nosecone.kind = self.kind_var.get()
        self.nosecone.base_radius = self.radius_var.get()
       
        #draw the updated nosecone
        self.draw_nosecone()

    def save_nosecone(self):
        """
        Saves the current nosecone configuration to a text file,
        exports all parameters, calculated properties, and game-related info.
        """
        #first, make sure nosecone is updated
        self.update_nosecone()

        #get the file name from the ui
        filename = self.file_name.get()

        #ensure file name is valid
        illegal_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        if not filename or any(char in filename for char in illegal_chars):
            mb.showerror("Invalid Filename", "Please enter a valid file name.")
            return

        #create part directory if none exists
        os.makedirs("data/nosecones", exist_ok=True)

        #create file_path string using part name
        file_path = "data/nosecones/"+filename+".txt"

        # store list of entries for the file with corresponding vars
        entries = [
            ("Length", self.length_var.get()),
            ("Base Radius", self.radius_var.get()),
            ("Kind", self.kind_var.get()),
            ("Volume", self.nosecone_vol(thickness=0.1*self.radius_var.get())), #assume thickness is 10% of radius
            ("Mass", self.nosecone_mass()),
            ("CoM", self.nosecone_CoM()),
            ("Cost", 0.0), #makes custom parts free
            ("Level", 10) #makes custom parts unusable in career mode
        ]

        #if valid, write entries to the txt file
        if self.saveable:
            with open(file_path, "w") as f:
                for label, var in entries:
                    f.write(str(label)+ ": " + str(var) + "\n") #write each line as label: var

            mb.showinfo("Save Successful", filename +" was successfully saved.")

    def nosecone_vol(self, thickness=0.0):
        """
        Calculates the volume of the nosecone shell using numerical integration
        
        Parameters:
            thickness (float): wall thickness of the nosecone shell (m)
            if 0, treats as solid.
        
        Returns:
            float: volume in m^3
        """
        # get nosecone shape profile from RocketPy
        x, y = self.nosecone.shape_vec
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

    # calculates and returns mass of nosecone (kg) using nosecone_vol()
    def nosecone_mass(self):
        density = 1000.0 #assumed density in kg/m^3
        return self.nosecone_vol(thickness=0.1*self.radius_var.get()) * density #assume thickness is 10% of radius
    
    def nosecone_CoM(self):
        """
        Calculates the center of mass position in the axial direction
        Uses first moment of area integration
        
        Returns:
            float: distance from nosecone tip to CoM (m)
        """
        # get nosecone shape profile from RocketPy
        x, y = self.nosecone.shape_vec
        x = np.array(x)
        y = np.array(y)

        nose_thickness = 0.1*self.radius_var.get()
        if nose_thickness > 0:
            y_inner = y - nose_thickness
        else:
            y_inner = np.zeros_like(y)


        # calculate cross-section area at each position
        A = np.pi * (y**2 - y_inner**2)
        # calculate first moment of area: M = ∫x * A(x) dx
        M = np.trapz(x * A, x)
        #store nosecone volume
        volume = self.nosecone_vol(thickness=nose_thickness)
        # return CoM
    
        return M / volume
        
    # draws the nosecone on the matplotlib figure using RocketPy data, shows the center of mass
    def draw_nosecone(self):
        #clear last plot
        self.ax.clear()
        self.ax.set_aspect("equal") #have axes scale with the nosecone
        self.ax.grid(True)

        # RocketPy stores nose shape in nose.shape_vec
        x, y = self.nosecone.shape_vec  # x = length along axis, y = radius

        # Plot top side of the nose cone
        self.ax.plot(x, y, color="blue", linewidth=2)
        # Plot bottom side (y is mirrored)
        self.ax.plot(x, [-i for i in y], color="blue", linewidth=2)

        #draw vertical base line using last shape index
        base_x = x[-1]
        base_y = y[-1]
        self.ax.plot([base_x, base_x], [-base_y, base_y], color="blue", linewidth=2)
        
        #draw CoM and corresponding legend
        com_x = self.nosecone_CoM()
        self.ax.plot(com_x, 0, 'bo', markersize=5, label='Center of Mass')
        self.ax.legend()

        # set the plot title and labels
        self.ax.set_title("Nose Cone Builder")
        self.ax.set_xlabel("Axial Distance (m)")
        self.ax.set_ylabel("Radius (m)")

        # draw the plot
        self.canvas.draw()

        #update the mass label if it exists
        if hasattr(self, 'mass_value_label'):
            self.mass_value_label.config(text=str(round(self.nosecone_mass(),4))+" (kg)")

        #update the volume label if it exists
        if hasattr(self, 'vol_value_label'):
            self.vol_value_label.config(text=str(round(self.nosecone_vol(thickness=0.1*self.radius_var.get()),4))+" (m^3)") #assume thickness is always 10% of the base radius


if __name__ == "__main__":
    app = NoseconeEditor()
    app.mainloop() #start tkinter and keeps window running
