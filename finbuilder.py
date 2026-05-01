"""
William Reisman
ENAE380 - Section 102

finbuilder.py script creates fin building interface to use in sandbox mode
"""
#tkinter imports
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as mb

#matplotlib imports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#rocketpy imports
from rocketpy import TrapezoidalFins

import os #file path management

#create and return default fins object using RocketPy
def create_fins():
    fins = TrapezoidalFins(
        n=4,
        root_chord=0.1,
        tip_chord=0.05,
        span=0.1,
        cant_angle=0.0,
        rocket_radius=1.0,
    )
    fins.position = 0.5 #must be assigned
    return fins


# Tkinter UI class for viewing and editing fins
class FinEditor(tk.Tk):
    def __init__(self):
        # initialize the tail editor window and UI
        super().__init__()
        self.title("Fin Editor")
        self.geometry("1400x800")

        # create default fins
        self.fins = create_fins()

        #make UI panels
        self._build_left_panel()
        self._build_right_panel()

        #draw initial fins
        self.draw_fins()

    # creates the left panel with fin parameter inputs. includes root_chord, tip_chord, span, and save functionality.
    def _build_left_panel(self):
        # create left frame
        left = ttk.Frame(self, padding=10)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="Fin Parameters", font=("Arial", 14)).pack(pady=10)

        # Variables in tk linked to each of the fin parameters
        self.root_var = tk.DoubleVar(value=self.fins.root_chord)
        self.tip_var = tk.DoubleVar(value=self.fins.tip_chord)
        self.span_var = tk.DoubleVar(value=self.fins.span)

        #variable to store filename in tk
        self.file_name = tk.StringVar(value="untitled_fins")

        #list of tuples to pair each label to its variable
        entries = [
            ("Root chord", self.root_var),
            ("Tip chord", self.tip_var),
            ("Span", self.span_var),
        ]

        # Creates label and entry box for user to enter values for the variables
        for label, var in entries:
            ttk.Label(left, text=label).pack(anchor="c", pady=(10, 0))
            ttk.Spinbox(left, textvariable=var, width=20, justify="center", from_=0, to=50, increment=0.1).pack(anchor="c")

        #Creates button to update the fins with user's values, calls update_fins function
        ttk.Button(left, text="Update Fins", command=self.update_fins,width=20).pack(
            pady=20
        )

        #creates file name entry box
        ttk.Label(left, text="File Name").pack(anchor="c", pady=(10, 0))
        ttk.Entry(left, textvariable=self.file_name, width=20, justify="center").pack(anchor="c")

        #Creates button to save fin configuration
        ttk.Button(left, text="Save and Export", command=self.save_fins,width=20).pack(
            pady=20
        )

    # create the right UI panel with a matplotlib figure
    def _build_right_panel(self):
        right = ttk.Frame(self)
        right.pack(side="right", fill="both", expand=True)

        self.part_frame = ttk.Frame(right)
        self.part_frame.pack(side="left", fill="both", expand=True)

        #put the matplotlib figure into the tk canvas
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.part_frame)
        # fill the canvas entirely
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.info_panel = ttk.Frame(right, padding=30, width=200)
        self.info_panel.pack(side="right", fill="y")
        ttk.Label(self.info_panel, text="Part Info", font=("Arial", 14)).pack(pady=0)

        ttk.Label(self.info_panel, text="Mass", font=("Arial", 20)).pack(pady=10)
        self.mass_value_label = ttk.Label(self.info_panel, text="0", font=("Arial", 20),foreground="blue")
        self.mass_value_label.pack(pady=10)

        ttk.Label(self.info_panel, text="Area", font=("Arial", 20)).pack(pady=10)
        self.area_value_label = ttk.Label(self.info_panel, text="0", font=("Arial", 20),foreground="blue")
        self.area_value_label.pack(pady=10)

    # updates fin object with current parameter values from the tk UI
    # checks if inputs are valid and draws the fins
    def update_fins(self):

        self.saveable = True #store if part is valid
        
        #check that dimensions are <50m
        if self.root_var.get() > 50.0 or self.tip_var.get() > 50.0 or self.span_var.get() > 50.0:
            mb.showwarning("Invalid Part Size","Dimensions are too large (max 50m), adjust part parameters.")
            self.saveable = False
            return
        
        #check that dimensions are >0
        if self.root_var.get() <= 0 or self.tip_var.get() <= 0 or self.span_var.get() <= 0:
            mb.showwarning("Invalid Part Size","Dimensions cannot be <=0, adjust part parameters.")
            self.saveable = False
            return
        
        if self.root_var.get() < self.tip_var.get():
            mb.showwarning("Invalid Part Shape","Root Radius must be >= Tip Radius. Adjust part parameters.")
            self.saveable = False
            return

        #update variables with the ui values
        self.fins.root_chord = self.root_var.get()
        self.fins.tip_chord = self.tip_var.get()
        self.fins.span = self.span_var.get()
        
        #draw the updated fins
        self.draw_fins()

    def save_fins(self):
        #first, make sure fins are updated
        self.update_fins()

        #get the file name from the ui
        filename = self.file_name.get()

        #ensure file name is valid
        illegal_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        if not filename or any(char in filename for char in illegal_chars):
            mb.showerror("Invalid Filename", "Please enter a valid file name.")
            return

        #create part directory if none exists
        os.makedirs("data/fins", exist_ok=True)

        #create file_path string using part name
        file_path = "data/fins/"+filename+".txt"

        # store list of entries for the file with corresponding vars
        entries = [
            ("Root Chord", self.root_var.get()),
            ("Tip Chord", self.tip_var.get()),
            ("Span", self.span_var.get()),
            ("Area", self.fin_area()),
            ("Mass", self.fin_mass(thickness=0.05*self.root_var.get())),#assume thickness is 5% of root chord
            ("CoM", self.fin_CoM()[0]),
            ("Cost", 0.0), #makes custom parts free
            ("Level", 10) #makes custom parts unusable in career mode
        ]

        if self.saveable:
            #if valid, write entries to the txt file
            with open(file_path, "w") as f:
                for label, var in entries:
                    f.write(str(label)+ ": " + str(var) + "\n") #write each line as label: var

            mb.showinfo("Save Successful", filename +" was successfully saved.")

    # Calculates and returns the area of the trapezoidal fin
    def fin_area(self):
        root = self.fins.root_chord
        tip = self.fins.tip_chord
        span = self.fins.span
        return 0.5*(root+tip)*span #simple trapezoid area formula
    
    # Calculates and returns mass of fins with default thickness of 1cm and density of 1000kg/m^3
    def fin_mass(self, density=1000, thickness=0.01):
        volume = self.fin_area() * thickness
        return volume * density

    def fin_CoM(self):
        """
        Calculates the center of mass position in x and y directions relative to origin
        Uses Richard Nakka's Excel spreadsheet calculations for C.G. of a flat plate fin
        Works by splitting the fin into two right triangles

        Returns:
            tuple of floats: y_bar and x_bar (m)
        """
        #get fin values
        h = self.fins.root_chord
        t = self.fins.tip_chord
        w = self.fins.span

        # define the fin with these points
        x=[0,0,0,0,w,w/2,w,w]
        y=[h,0,0,h/2,0,0,t,t/2]
        
        # triangle B centroid coordinates found using centroid of a right triangle
        Bx = x[5]-(x[5]-x[0])/3
        By = y[5]-(y[5]-y[0])/3

        # triangle C centroid coordinates found using centroid of a right triangle
        Cx = x[7]-(x[7]-x[0])/3
        Cy = y[7]+(y[0]-y[7])/3

        # triangle B base and height
        Bh = y[0]-y[2]
        Bb = x[4]-x[2]

        # triangle C base and height
        Ch = x[6]-x[0]
        Cb = y[6]-y[4]

        # areas of each triangle and combined area
        AreaB = 0.5*Bh*Bb
        AreaC = 0.5*Ch*Cb
        Atotal = AreaB + AreaC

        # area-weighted centers of mass for each triangle
        CGxB = AreaB*Bx
        CGyB = AreaB*By
        CGxC = AreaC*Cx
        CGyC= AreaC*Cy

        # final centroid location using weighted average
        CGx = (CGxB + CGxC)/Atotal
        CGy = (CGyB + CGyC)/Atotal

        #flipped to match my coordinates
        return (CGy, CGx)


    # draws fin on the matplotlib figure using fin parameters, shows the center of mass
    def draw_fins(self):
        #clear last plot
        self.ax.clear()
        self.ax.set_aspect("equal") #have axes scale with the fin
        self.ax.grid(True)

        #get fin values
        root = self.fins.root_chord
        tip = self.fins.tip_chord
        span = self.fins.span

        #store the vertices of the trapezoidal fin in x and y
        x = [0, root, tip, 0, 0]
        y = [0, 0, span, span, 0]

        # Plot the fin shape
        self.ax.plot(x, y, color="blue", linewidth=2)

        #draw CoM at x_bar, y_bar and show corresponding legend
        com_x = self.fin_CoM()[0]
        com_y = self.fin_CoM()[1]
        self.ax.plot(com_x, com_y, 'bo', markersize=5, label='Center of Mass')
        self.ax.legend()

        # set the plot title and labels
        self.ax.set_title("Fin Builder")
        self.ax.set_xlabel("Chord (m)")
        self.ax.set_ylabel("Span (m)")

        # draw the plot
        self.canvas.draw()

        #update the mass label if it exists
        if hasattr(self, 'mass_value_label'):
            self.mass_value_label.config(text=str(round(self.fin_mass(thickness=0.05*self.root_var.get()),4))+" (kg)")

        #update the area label if it exists
        if hasattr(self, 'area_value_label'):
            self.area_value_label.config(text=str(round(self.fin_area(),4))+" (m^2)")

if __name__ == "__main__":
    app = FinEditor()
    app.mainloop() #start tkinter and keeps window running
