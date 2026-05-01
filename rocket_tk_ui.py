"""
William Reisman
ENAE380 - Section 102

rocket_tk_ui.py script creates rocket building/game interface and simulates flights using RocketPy
"""
#tkinter imports
import tkinter as tk
from tkinter import ttk, filedialog
import tkinter.messagebox as mb

#matplotlib imports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

#RocketPy imports
from rocketpy import Environment, SolidMotor, Rocket, Flight, Tail, NoseCone, TrapezoidalFins

import numpy as np

#enable launching multiple scripts
import subprocess
import sys

import os #file path management

import config #config file

#set up RocketPy Environment using Wyoming Sounding Data
env = Environment(latitude=32.990254, longitude=-106.974998, elevation=1400) #Located at Spaceport America

url = "https://weather.uwyo.edu/cgi-bin/sounding?region=naconf&TYPE=TEXT%3ALIST&YEAR=2019&MONTH=04&FROM=2112&TO=2112&STNM=72672"

env.set_atmospheric_model(type="wyoming_sounding", file=url)

#class to create rocket building UI in tkinter 
class RocketViewer(tk.Tk):
    def __init__(self):
        # initialize the parent Tk class
        super().__init__()
        self.title("Backyard Space Program - " + config.GAME_MODE)

        self.state('zoomed') # ensures window is maximized
        
        # set the default size of the window
        self.geometry("1920x1080")

        #initialize game state-related variables
        self.player_level = config.PLAYER_LEVEL
        self.game_mode = config.GAME_MODE
        self.alt_goal = 0
        self.budget = 0
        self.max_impact_vel = 0
        self.sm_min = 0
        self.sm_max = 0
        self.flown = False
        
        # Build UI panels
        self._build_left_panel()
        self._build_right_panel()

        # update files, load and draw rocket once
        self.refresh_files()
        self.rocket = self.create_rocket()
        self.draw_rocket()
        
        # trigger tutorial and first mission if in career mode
        if self.game_mode == "career":
            self.tutorial()
            self.new_mission()
        else:
            self.sandbox_tutorial()
        

    # Create and return default/updated rocket object using RocketPy
    def create_rocket(self):

        #read in motor values from selected file
        motor_vals = self.read_file("motors",self.selected_motor_file.get())

        #create example solid rocket motor using RocketPy constructor
        self.example_solid = SolidMotor(
        thrust_source=motor_vals["Thrust Source"], #opens corresponding csv file
        dry_mass=float(motor_vals["Dry Mass"]), #mass without propellant
        # inertia calculated with helper function based on radius, height, mass, and thickness of 10% outer radius
        dry_inertia= self.tube_inertia(radius=float(motor_vals["Grain Outer Radius"]),length=float(motor_vals["Grain Height"])*int(motor_vals["Grain Number"]),mass=float(motor_vals["Dry Mass"]),thickness=0.1*float(motor_vals["Grain Outer Radius"])),
        nozzle_radius=float(motor_vals["Nozzle Radius"]),
        grain_number=int(motor_vals["Grain Number"]),
        grain_density=float(motor_vals["Grain Density"]),
        grain_outer_radius=float(motor_vals["Grain Outer Radius"]),
        grain_initial_inner_radius=float(motor_vals["Grain Inner Radius"]),
        grain_initial_height=float(motor_vals["Grain Height"]),
        grain_separation=float(motor_vals["Grain Separation"]),
        grains_center_of_mass_position=float(motor_vals["Grain CoM"]),
        center_of_dry_mass_position=float(motor_vals["CoDM"]),
        nozzle_position=float(motor_vals["Nozzle Position"]),
        burn_time=float(motor_vals["Burn Time"]),
        throat_radius=float(motor_vals["Throat Radius"]),
        coordinate_system_orientation="nozzle_to_combustion_chamber",
    )

        #read in nosecone values from selected file 
        nosecone_vals = self.read_file("nosecones",self.selected_nosecone_file.get())

        #create nosecone object
        self.nose = NoseCone(
            length=float(nosecone_vals["Length"]), 
            base_radius=float(nosecone_vals["Base Radius"]), 
            kind=nosecone_vals["Kind"]
        )
        
        #read in tail values from selected file 
        tail_vals = self.read_file("tails",self.selected_tail_file.get())

        #create tail object
        self.tail = Tail(
            top_radius=float(tail_vals["Top Radius"]), 
            bottom_radius=float(tail_vals["Bottom Radius"]), 
            length=float(tail_vals["Length"]), 
            rocket_radius=float(tail_vals["Top Radius"])
        )
        
        #read in fin values from selected file 
        fin_vals = self.read_file("fins",self.selected_fin_file.get())

        #create fin object
        self.fins = TrapezoidalFins(
            n=self.fin_num.get(),
            root_chord=float(fin_vals["Root Chord"]),
            tip_chord=float(fin_vals["Tip Chord"]),
            span=float(fin_vals["Span"]),
            cant_angle=0.0,
            airfoil=("data/airfoils/NACA0012-radians.csv","radians"), #default airfoil on all wings
            rocket_radius=float(tail_vals["Top Radius"])
        )

        #create rocket object with values acquired from helper functions
        user_rocket = Rocket(
                radius=self.nose.base_radius, #linked to nosecone radius
                mass=self.rocket_mass(with_motor=False), #get total rocket mass without motor
                inertia=self.tube_inertia(radius=self.rocket_radius.get(),length=self.tube_length(),mass=self.tube_mass(),thickness=0.2*self.rocket_radius.get()), #get inertia with rad, length, mass, thickness params
                power_off_drag="data/dragcurves/powerOffDragCurve.csv", #default drag curve
                power_on_drag="data/dragcurves/powerOffDragCurve.csv",
                center_of_mass_without_motor=self.rocket_CoM(), #center of mass based on part positions
                coordinate_system_orientation="tail_to_nose",
            )
        
        #add all parts to rocket at corresponding positions
        user_rocket.add_motor(self.example_solid, position=self.tail_pos.get() - self.tail.length) #motor always placed at tail
        user_rocket.add_tail(top_radius=self.tail.top_radius, bottom_radius=self.tail.bottom_radius, length=self.tail.length, position=self.tail_pos.get())
        user_rocket.add_trapezoidal_fins(n=self.fins.n, 
                                        root_chord=self.fins.root_chord, 
                                        tip_chord=self.fins.tip_chord,
                                        span=self.fins.span,
                                        cant_angle=self.fins.cant_angle,
                                        airfoil=self.fins.airfoil,
                                        position=self.fin_pos.get()
                                        )        
        user_rocket.add_nose(kind=self.nose.kind, 
                             length=self.nose.length, 
                             base_radius=self.nose.base_radius, 
                             position=self.nose_pos.get()+self.nose.length) #nosecone position starts at base
        
        #read in parachute values from selected file
        chute_vals = self.read_file("parachutes", self.selected_chute_file.get())
        
        #attach parachute to rocket
        self.chute = user_rocket.add_parachute(
            name="main",
            cd_s=float(chute_vals["CdS"]),
            trigger="apogee",      # ejection at apogee
            sampling_rate=105,
            lag=1.5,
            noise=(0, 8.3, 0.5)
        )
        
        return user_rocket
    
    #calculates and returns rocket tube length based on part positions
    def tube_length(self):
        nose_tip = self.nose_pos.get() + self.nose.length
        nose_length = self.nose.length
        tail_top = self.tail_pos.get()

        #tube length is defined as distance between tail top and nose base
        return abs((nose_tip-nose_length)-tail_top)
    
    #calculates and returns rocket tube volume assuming hollow tube with some thickness
    def tube_vol(self, thickness=0.0):
        length = self.tube_length()
        r_outer = self.rocket_radius.get()
        r_inner = r_outer - thickness
        return np.pi * length * (r_outer**2 - r_inner**2)
    
    #calculates and returns rocket tube mass assuming thickness is 20% the tube radius
    def tube_mass(self, density=1000):
        vol = self.tube_vol(thickness=0.2*self.rocket_radius.get())
        return vol * density
    
    #calculates and returns an inertia tuple (Ixx, Iyy, Izz) for a hollow rocket tube or motor with parameters of length, radius, and thickness
    def tube_inertia(self, length, radius, mass, thickness=0.0):
        r_outer = radius
        r_inner = r_outer - thickness
        Ixx = (1.0/12.0) * mass * (3*(r_outer**2 + r_inner**2) + length**2)
        Iyy = Ixx #symmetrical
        Izz = 0.5 * mass * (r_outer**2 + r_inner**2)
        inertia_tuple = (Ixx,Iyy,Izz)
        return inertia_tuple
    
    #calculates and returns the rocket's center of mass (without motor) relative to origin
    def rocket_CoM(self):
        #read in part values
        nosecone_vals = self.read_file("nosecones",self.selected_nosecone_file.get())
        fin_vals = self.read_file("fins",self.selected_fin_file.get())
        tail_vals = self.read_file("tails",self.selected_tail_file.get())

        #store part and rocket tube masses
        fin_m = float(fin_vals["Mass"])
        tail_m = float(tail_vals["Mass"])
        nose_m = float(nosecone_vals["Mass"])
        rocket_m = self.tube_mass()

        #store part CoMs
        fin_cm = float(fin_vals["CoM"])
        tail_cm = float(tail_vals["CoM"])
        nose_cm = float(nosecone_vals["CoM"]) #measured from tip

        #store part positions
        nose_tip = self.nose_pos.get() + self.nose.length
        tail_top = self.tail_pos.get()
        fin_top = self.fin_pos.get()

        #store CoM positions relative to origin
        x_rocket = self.tube_length()/2.0 + tail_top
        x_tail = tail_top - tail_cm
        x_fin = fin_top - fin_cm
        x_nose = abs(nose_tip - nose_cm)
        
        #store total mass of components (including all fins)
        total_mass = rocket_m + tail_m + nose_m + self.fin_num.get() * fin_m

        #store summation of x_cm * mass for each part
        sum = (x_rocket*rocket_m)+(x_tail*tail_m)+(x_nose*nose_m)+self.fin_num.get()*(x_fin*fin_m) 

        #return overall CoM (without motor)
        return sum/total_mass
    
    #calculates and returns total rocket mass with parameter to include/exclude motor mass
    def rocket_mass(self, with_motor = True):
        nosecone_vals = self.read_file("nosecones",self.selected_nosecone_file.get())
        fin_vals = self.read_file("fins",self.selected_fin_file.get())
        tail_vals = self.read_file("tails",self.selected_tail_file.get())

        fin_m = float(fin_vals["Mass"])
        tail_m = float(tail_vals["Mass"])
        nose_m = float(nosecone_vals["Mass"])
        rocket_m = self.tube_mass()

        if with_motor:
            motor_m = self.example_solid.total_mass(0)
        else:
            motor_m = 0
    
        total_mass = rocket_m + tail_m + nose_m + self.fin_num.get() * fin_m + motor_m
        
        return total_mass
    
    #calculate and return total rocket cost based on part values from files and tube cost density
    def rocket_cost(self):
        nosecone_vals = self.read_file("nosecones",self.selected_nosecone_file.get())
        fin_vals = self.read_file("fins",self.selected_fin_file.get())
        tail_vals = self.read_file("tails",self.selected_tail_file.get())
        motor_vals = self.read_file("motors",self.selected_motor_file.get())
        chute_vals = self.read_file("parachutes",self.selected_chute_file.get())

        fin_c = float(fin_vals["Cost"]) * self.fin_num.get()
        tail_c = float(tail_vals["Cost"])
        nose_c = float(nosecone_vals["Cost"])
        rocket_c = self.tube_mass() * 100.0 #cost/kg for rocket tube
        motor_c = float(motor_vals["Cost"])
        chute_c = float(chute_vals["Cost"])

        return fin_c + tail_c + nose_c + rocket_c + motor_c + chute_c

    # create the left tkinter control panel with rocket parameter inputs and other interactions
    def _build_left_panel(self):
        #create the left frame container
        left = ttk.Frame(self, padding=10)
        left.pack(side="left", fill="y")

        #add title label
        ttk.Label(left, text="Rocket Parameters", font=("Arial", 14)).pack(pady=45)

        #Initialize tkinter vars for rocket part parameters:

        #Fin params: number of fins, position
        self.fin_pos = tk.DoubleVar(value=1)
        self.fin_num = tk.IntVar(value=2)

        #Nosecone params: position
        self.nose_pos = tk.DoubleVar(value=3)

        #Tail params: position
        self.tail_pos = tk.DoubleVar(value=0)

        #Parachute param: deplot alt
        self.chute_deploy_alt = tk.DoubleVar(value=1000.0)
        
        #Rocket params: radius
        self.rocket_radius = tk.DoubleVar(value=0.0635)

        #### MOTOR PARAMETER WINDOW ####
        #create motor frame container
        motor_frame = ttk.LabelFrame(left, text="Motor", padding=5)
        motor_frame.pack(fill="x", padx=5)

        #Motor file dropdown select from data/motor directory using create_dropdown function
        self.selected_motor_file, self.motor_dropdown = self.create_dropdown(
                motor_frame,
                "Select Motor:",
                "data/motors"
                )

        #### NOSECONE PARAMETER WINDOW #####
        nose_frame = ttk.LabelFrame(left, text="Nosecone", padding=5)
        nose_frame.pack(fill="x", padx=5)

        if self.game_mode == "sandbox":
            #Creates button to launch the fin builder script
            ttk.Button(nose_frame, text="Create Nosecone", command=lambda: self.run_script("noseconebuilder.py"),width=20).pack(pady=10) #lambda so the program only runs when clicked

        #Nosecone file dropdown select
        self.selected_nosecone_file, self.nosecone_dropdown = self.create_dropdown(
                nose_frame,
                "Select Nosecone:",
                "data/nosecones"
                )
        
        ttk.Label(nose_frame, text="Nosecone Position (m)").pack(anchor="c", pady=(10, 0))
        #add spinbox to control nosecone position on rocket tube
        ttk.Spinbox(nose_frame, textvariable=self.nose_pos, width=20, justify="center", from_=-9999, to=9999, increment=0.1).pack(anchor="c")

        #### FIN PARAMETER WINDOW #####
        fins_frame = ttk.LabelFrame(left, text="Fins", padding=5)
        fins_frame.pack(fill="x", padx=5)

        if self.game_mode == "sandbox":
            #Creates button to launch the fin builder script
            ttk.Button(fins_frame, text="Create Fins", command=lambda: self.run_script("finbuilder.py"),width=20).pack(pady=10)

        #Fin file dropdown select
        self.selected_fin_file, self.fin_dropdown = self.create_dropdown(
        fins_frame,
        "Select Fin:",
        "data/fins"
        )

        #set maximum allowed fins depending on gamemode to balance rocket construction
        if self.game_mode == "career":
            max_fins = 6
        else:
            max_fins = 12

        ttk.Label(fins_frame, text="Number of Fins").pack(anchor="c", pady=(5, 0))
        #spinbox to control fin number (minimum 2 fins for simulation to work)
        ttk.Spinbox(fins_frame, textvariable=self.fin_num, width=20, justify="center", from_=2, to=max_fins, increment=1.0, state="readonly").pack(anchor="c")

        ttk.Label(fins_frame, text="Fin Position (m)").pack(anchor="c", pady=(10, 0))
        #spinbox to control fin position on rocket tube
        ttk.Spinbox(fins_frame, textvariable=self.fin_pos, width=20, justify="center", from_=-9999, to=9999, increment=0.1).pack(anchor="c")

        ### TAIL PARAMETER WINDOW ###
        tail_frame = ttk.LabelFrame(left, text="Tail", padding=5)
        tail_frame.pack(fill="x", padx=5)
        
        if self.game_mode == "sandbox":
            #Creates button to launch the tail builder script
            ttk.Button(tail_frame, text="Create Tail", command=lambda: self.run_script("tailbuilder.py"),width=20).pack(pady=10)

        #Fin file dropdown select
        self.selected_tail_file, self.tail_dropdown = self.create_dropdown(
        tail_frame,
        "Select Tail:",
        "data/tails"
        )

        ### PARACHUTE PARAMETER WINDOW ###
        chute_frame = ttk.LabelFrame(left, text="Parachute", padding=5)
        chute_frame.pack(fill="x", padx=5)

        #Parachute file dropdown select
        self.selected_chute_file, self.chute_dropdown = self.create_dropdown(
        chute_frame,
        "Select Parachute:",
        "data/parachutes"
        )

        ### LAUNCH RELATED BUTTONS ###

        #Creates button to update the rocket with user's values, calls update_rocket function
        ttk.Button(left, text="Update Rocket", command=self.update_rocket,width=20).pack(pady=10)

        #Creates help button to access tutorial
        ttk.Button(left, text="HELP", command=self.help,width=20).pack(pady=10)

        #Creates button to simulate rocket flight
        tk.Button(left, text="LAUNCH", command= self.test_flight, width=20, bg="green", fg="white").pack(pady=10)

    # create the right panel with rocket visualization and information
    def _build_right_panel(self):
        #create right frame container
        right = ttk.Frame(self, padding=10)
        right.pack(side="right", fill="both", expand=True)

        #create frame for rocket representation
        self.rocket_frame = ttk.Frame(right)
        self.rocket_frame.pack(side="left", fill="both", expand=True)

        # set up matplotlib figure and canvas for displaying rocket
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.rocket_frame) #embedded canvas for Matplotlib
        widget = self.canvas.get_tk_widget()
        widget.pack(fill="both", expand=True) #rocket representation will fill window

        # Add Matplotlib navigation toolbar to allow panning
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.rocket_frame)
        self.toolbar.update()
        self.toolbar.pack(side="top", fill="x")
        self.fig.tight_layout()

        #create rocket info frame
        self.info_panel = ttk.LabelFrame(right, padding=10, width=200)
        self.info_panel.pack(side="right", fill="y")
        
        ttk.Label(self.info_panel, text="Rocket Info", font=("Arial", 14)).pack(pady=20)

        #current rocket mass display
        ttk.Label(self.info_panel, text="Rocket Mass", font=("Arial", 20)).pack(pady=10)
        self.mass_value_label = ttk.Label(self.info_panel, text="0", font=("Arial", 20),foreground="blue")
        self.mass_value_label.pack(pady=10)

        #current cost display
        ttk.Label(self.info_panel, text="Rocket Cost", font=("Arial", 20)).pack(pady=10)
        self.cost_value_label = ttk.Label(self.info_panel, text="0", font=("Arial", 20),foreground="green")
        self.cost_value_label.pack(pady=10)

        #minimum static margin display (shows as red/green if negative/positive)
        ttk.Label(self.info_panel, text="Min. Static Margin", font=("Arial", 20)).pack(pady=10)
        self.sm_value_label = tk.Label(self.info_panel, text="0", font=("Arial", 20),fg="green")
        self.sm_value_label.pack(pady=10)

        #Creates button to plot the rocket's static margin over time
        ttk.Button(self.info_panel, text="Plot Static Margin", command= self.plot_static_margin,width=20).pack(pady=10)

        #Creates more info button
        ttk.Button(self.info_panel, text="More Info", command=self.more_info,width=20).pack(pady=10)

        #horizontal divider
        ttk.Separator(self.info_panel, orient='horizontal').pack(fill='x', pady=10)

        ### Mission Information ###
        #create mission info frame if career mode
        if self.game_mode == "career":
            mission_frame = ttk.Frame(self.info_panel)
            mission_frame.pack(fill="x", pady=(10, 0))

            ttk.Label(mission_frame, text="Mission Info", font=("Arial", 14)).pack(pady=20)

            #display target altitude
            ttk.Label(mission_frame, text="Target Altitude", font=("Arial", 20)).pack(pady=10)
            self.altitude_label = ttk.Label(mission_frame, text="0", font=("Arial", 20),foreground="purple")
            self.altitude_label.pack(pady=10)

            #display mission budget
            ttk.Label(mission_frame, text="Mission Budget", font=("Arial", 20)).pack(pady=10)
            self.budget_label = ttk.Label(mission_frame, text="0", font=("Arial", 20),foreground="green")
            self.budget_label.pack(pady=10)

            #display max impact velocity
            ttk.Label(mission_frame, text="Max Impact Velocity", font=("Arial", 20)).pack(pady=10)
            self.impact_label = ttk.Label(mission_frame, text="0", font=("Arial", 20),foreground="darkred")
            self.impact_label.pack(pady=10)
        
        ### Flight Information ###
        else:
            results_frame = ttk.Frame(self.info_panel)
            results_frame.pack(fill="x", pady=(10, 0))

            ttk.Label(results_frame, text="Flight Results", font=("Arial", 14)).pack(pady=20)

            #Creates info button
            ttk.Button(self.info_panel, text="Flight Info", command=self.flight_info,width=20).pack(pady=10)

            #export kml button
            ttk.Button(self.info_panel, text="Export KML", command=self.export_kml,width=20).pack(pady=10)


    def create_dropdown(self, side, label, file_path):
        """
        Create a dropdown menu containing files from a directory
        
        Parameters:
        side: parent frame to attach dropdown to
        label: text label to display above dropdown
        file_path: path to directory containing files to list
            
        Returns: Tuple of (tk StringVar for selected value, tk Combobox widget)
        """
        ttk.Label(side, text=label).pack()

        #get the folder name of the file
        folder = os.path.basename(file_path)
    
        # get unlocked files using helper function
        unlocked_files = self.unlocked_files(folder)

        # create display strings with filename and cost for the selection
        display = []
        for filename in unlocked_files:
            part_dict = self.read_file(folder, filename) #use part dictionary to obtain cost
            display.append(filename + " ($" + part_dict["Cost"] + ")")

        # Tk variable for combobox dropdown
        selected_file = tk.StringVar()
        dropdown = ttk.Combobox(
            side,
            width=25,
            textvariable=selected_file, 
            values=display, 
            state="readonly"
        )
        dropdown.pack(pady=5)

        #select first file by default
        dropdown.current(0)

        return (selected_file, dropdown)
  
    def refresh_files(self):
        """Refresh all file dropdowns with current folder contents"""
        #create a dictionary linking folder names to their corresponding dropdown
        file_dropdowns = {
            "nosecones": self.nosecone_dropdown,
            "fins": self.fin_dropdown,
            "tails": self.tail_dropdown,
            "motors": self.motor_dropdown,
            "parachutes": self.chute_dropdown
        }
    
        #iterate through each folder and its dropdown
        for folder, dropdown in file_dropdowns.items():
            # Get unlocked files using helper function
            unlocked = self.unlocked_files(folder)

            # create display strings with filename and cost for the selection
            display = []
            for filename in unlocked:
                part_dict = self.read_file(folder, filename)
                display.append(filename+" ($"+part_dict["Cost"]+")")
            
            # Update dropdown values
            dropdown.configure(values=display)
            
    def unlocked_files(self, folder):
        """
        returns list of filenames in folder that are unlocked for current player level
        parameter: name of part folder
        """
        # store all files in directory, strip the .txt 
        all_files = [os.path.splitext(file)[0] for file in os.listdir("data/"+folder)]
        
        unlocked = []
        #add only unlocked parts
        for filename in all_files:
            #store each file's part dictionary to access level
            part_dict = self.read_file(folder, filename)
            
            # Only add parts if their level is <= player's level
            if "Level" in part_dict:
                file_level = int(part_dict["Level"])
                if file_level <= self.player_level:
                    unlocked.append(filename)
        
        return unlocked

    # validate and update rocket configuration with current parameters
    def update_rocket(self):
        
        #refresh all files
        self.refresh_files()
        #replace rocket object with updated one
        self.rocket = self.create_rocket()
        #boolean to track if rocket can be launched
        self.launch_ready = True

        #find lowest static margin and store as sm_min
        sm0 = self.rocket.static_margin(0)
        burn_time = self.example_solid.burn_out_time
        smend = self.rocket.static_margin(burn_time)
        self.sm_min = min(sm0, smend)
        self.sm_max = max(sm0, smend)

        #change static margin label color to red if negative
        self.sm_value_label.config(fg="red" if self.sm_min < 0 else "green")

        #check that fin placement is valid, show messagebox warning if not
        #fins must be below nosecone and at least halfway on the tail
        if self.fin_pos.get() > self.nose_pos.get() or self.fin_pos.get() < (self.tail_pos.get()+self.fins.root_chord/2):
            mb.showwarning(
            "Invalid Fin Position",
            "Fin position is not on the body tube. Please adjust part positions."
            )
            self.launch_ready = False #do not allow rocket to be launched
            return
        
        motor_height = self.example_solid.grain_height(0)*(self.example_solid.grain_number+1)
        #check that tube is long enough to fit the motor
        if self.tube_length() < motor_height:
            mb.showwarning(
            "Invalid Tube Length",
            "Tube is too short to fit the motor.\n"
            "Tube Length: "+str(self.tube_length())+" (m)\n"
            "Motor Height: "+str(motor_height)+" (m)\n"
            "Please adjust part positions."
            )
            self.launch_ready = False
            return
    
        #check that tail and nosecone are same width
        if self.nose.base_radius != self.tail.top_radius:
            mb.showwarning(
            "Incompatible Parts",
            "Nosecone and Tail are different sizes.\n"
            "Nosecone Radius: "+str(self.nose.base_radius)+" (m)\n"
            "Tail Top Radius: "+str(self.tail.top_radius)+" (m)\n"
            "Please select different parts."
            )
            self.launch_ready = False
            return
        
        motor_width = self.example_solid.grain_outer_radius+self.example_solid.grain_inner_radius(0)
        #check that tube is wide enough to fit the motor
        if self.nose.base_radius < motor_width:
            mb.showwarning(
            "Invalid Tube Width",
            "Tube is too narrow to fit the motor.\n"
            "Tube Width: "+str(self.nose.base_radius)+" (m)\n"
            "Motor Width: "+str(motor_width)+" (m)\n"
            "Please select larger parts."
            )
            self.launch_ready = False
            return
        
        #only allow user 100m long tube
        if self.tube_length() > 100:
            mb.showwarning(
            "Tube Too Long. Max length is 100m",
            "Rocket Tube Too Long\nThat's definitely going to crash the simulation!"
            )
            self.launch_ready = False
            return

        #ensure tail is large enough to fit motor nozzle        
        if self.tail.bottom_radius < self.example_solid.nozzle_radius:
            mb.showwarning(
            "Tail Exit Too Small",
            "Tail cannot fit the motor nozzle.\n"
            "Tail Radius: "+str(self.tail.bottom_radius)+" (m)\n"
            "Nozzle Radius: "+str(self.example_solid.nozzle_radius)+" (m)\n"
            )
            self.launch_ready = False
            return

        #draw the rocket on the tk window
        self.draw_rocket()
    
    #function to launch external python scripts (used for custom part construction)
    def run_script(self, script_path):
        subprocess.Popen([sys.executable, script_path])

    #display static margin plot vs. time using RocketPy
    def plot_static_margin(self):
        self.rocket.plots.static_margin()

    #diplays additional rocket information using class variables and internal RocketPy functions
    def more_info(self):
        self.update_rocket()
        proceed = mb.askyesno("More Rocket Info",
                    "Rocket Radius: "+str(self.nose.base_radius)+" (m)\n"
                    "Rocket Tube Length: "+str(self.tube_length())+" (m)\n"
                    "Total Rocket Length: "+str(self.tail.length+self.tube_length()+self.nose.length)+" (m)\n"
                    "Dry Mass of Rocket: "+str(round((self.rocket.evaluate_dry_mass()),4))+" (kg)\n\n"
                    "Motor Mass (with propellant): "+str(round((self.example_solid.propellant_initial_mass+self.example_solid.dry_mass),4))+" (kg)\n"
                    "Dry Mass of Motor: "+str(self.example_solid.dry_mass)+" (kg)\n"
                    "Burn Time: "+str(self.example_solid.burn_out_time)+" (s)\n\n"
                    "Center of Mass Position: "+str(round((self.rocket.evaluate_center_of_mass()(0)),4))+" (m)\n"
                    "Static Center of Pressure Position: "+str(round((self.rocket.evaluate_center_of_pressure()(0)),4))+" (m)\n"
                    "Thrust to Weight Ratio: "+str(round(self.example_solid.max_thrust / (9.80665 * self.rocket.total_mass(0)), 4)) + "\n\n"
                    "Would you like to see ALL available rocket plots and data?\n"
                    "(Some information is shown in the terminal)",
                    icon="info"
                    )
        if proceed:
            self.rocket.all_info()
        else:
            return

    #displays flight information using flight test_flight object and internal RocketPy functions
    def flight_info(self):
        #ensure user has flown once
        if self.flown:
            apogee_altitude = self.test_flight.apogee
            apogee_agl = round((apogee_altitude - env.elevation),3)
            max_speed = round(self.test_flight.max_speed,3)
            max_mach = round(self.test_flight.max_mach_number,3)
            impact_vel = abs(round(self.test_flight.impact_velocity,3))
            
            proceed = mb.askyesno(
                        "Flight Results",
                        "Basic Flight Results:\n\n"
                        "Apogee Altitude (AGL): "+str(apogee_agl)+" (m)\n"
                        "Max Speed Achieved: "+str(max_speed)+" (m/s), or Mach: "+str(max_mach)+
                        "\nImpact Velocity: "+str(impact_vel)+" (m/s)\n\n"
                        "Would you like to see ALL available flight plots and data?\n"
                        "(Some information is shown in the terminal)",
                        icon="info"
                    )
            if not proceed:
                return
            
            # Show all available plots from RocketPy
            self.test_flight.all_info()
        
        else:
            mb.showerror("No Flights to Analyze","You have not flown a rocket yet, so there is no data to look at.")
            return
        
    #export flight path kml file for Google Earth analysis
    def export_kml(self):
        if self.flown:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".kml",
                filetypes=[("KML files", "*.kml")],
                title="Save Flight Trajectory As"
            )

            #if user cancels
            if not file_path:
                return

            self.test_flight.export_kml(
            file_name=file_path,
            extrude=True,
            altitude_mode="relative_to_ground",
            )
            mb.showinfo("Export Successful", "Trajectory saved to: \n"+file_path)

        else:
            mb.showerror("No Flights to Export","You have not flown a rocket yet, so there is no data to export.")
            return

                    
    def read_file(self, folder, filename):
        """
        reads part configuration from a text file
        
        Parameters:
            folder: part folder name (e.g. "motors")
            filename: name of file (without .txt)
            
        Returns:
            Dictionary with key-value pairs from file
        """
        filename = filename.split(" ($")[0] #take off price if it exists, needed because this function uses explicit dropdown values
        file_path = "data/" + folder + "/"+filename+".txt" #filepath string
        part_dict = {}

        #parse file as key:value pairs
        with open(file_path, "r") as f:
            for line in f:
                    key, value = line.strip().split(":") #split lines at the semicolon
                    part_dict[key.strip()] = value.strip() 
        return part_dict

    # update rocket representation in matplotlib canvas
    def draw_rocket(self):
        # clear the figure
        self.fig.clear()
        plt.close('all') #close all open plots and extra pop-ups
        
        # save original matplotlib functions
        orig_fig = plt.figure
        orig_show = plt.show

        # redirect RocketPy's plotting to our embedded figure
        # this prevents pop-up windows from RocketPy
        plt.figure = lambda *a, **k: self.fig #reuses self.fig by ignoring arguments
        plt.show = lambda *a, **k: None #prevents new windows

        #change default color settings
        vis_args = {
            "background": "white",
            "nose": "black",
            "tail": "black",
            "fins": "black",
            "body": "black",
            "motor": "black",
            "buttons": "black",
            "line_width": 1.5,
        }

        # RocketPy draws on self.fig now
        self.rocket.draw(vis_args=vis_args)
        
        # restore original Matplotlib functions
        plt.figure = orig_fig
        plt.show = orig_show
        
        # get current axes and fix view
        ax = self.fig.axes[0]
        ax.set_aspect("equal", adjustable="datalim")

        self.fig.tight_layout()
  
        # refresh Tkinter canvas to show updated drawing
        self.canvas.draw()

        #update the mass display label if it exists
        if hasattr(self, 'mass_value_label'):
            self.mass_value_label.config(text=str(round(self.rocket_mass(),2))+" (kg)")

        #update the cost label if it exists
        if hasattr(self, 'cost_value_label'):
            self.cost_value_label.config(text="$"+str(round(self.rocket_cost(),2)))

        #update the min. static margin if it exists
        if hasattr(self, 'sm_value_label'):
            self.sm_value_label.config(text=str(round(self.sm_min,3)))

        #update the target altitude label if it exists
        if self.game_mode == "career":
            self.altitude_label.config(text=str(round(self.alt_goal,2))+" (m)")

        #update the budget label if it exists
        if self.game_mode == "career":
            self.budget_label.config(text="$"+str(round(self.budget,2)))

        #update the max impact vel label if it exists
        if self.game_mode == "career":
            self.impact_label.config(text=str(round(self.max_impact_vel,2)))

    # run flight simulation in RocketPy and show the results
    def test_flight(self):
        #ensure rocket is updated
        self.rocket = self.create_rocket()
        self.update_rocket()

        #check that rocket is witin budget (if in career mode)
        if self.game_mode=="career" and (self.rocket_cost() > self.budget):
            mb.showwarning(
            "Over Budget",
            "Your Rocket is too expensive!\nMake sure to meet mission requirements."
            )
            self.launch_ready = False
            return
        
        if self.launch_ready: #ensure construction rocket is valid
            #static margin safety check to prevent game crashes
            if self.sm_min <= 0:
                # Warn user and ask user if they want to continue
                proceed = mb.askyesno(
                    "Warning: Rocket is Unstable", #title
                    "Warning: ROCKET IS UNSTABLE!\n\n"
                    "Static margin reaches " +str(round(self.sm_min,4))+ " calibers.\n"
                    "*Launching will likely crash the game!*\n"
                    "(Hint: You may want to adjust fins/nosecone)\n\n"
                    "Are you sure you want to simulate flight?",
                    icon="warning"
                )
                if not proceed:
                    return # don't run test flight if user hits no 
            
            #similar check for overstability
            if self.sm_max > 4.0:
                proceed = mb.askyesno(
                    "Warning: Rocket is Overstable", #title
                    "Warning: ROCKET IS OVERSTABLE!\n\n"
                    "Static margin reaches " +str(round(self.sm_max,4))+ " calibers.\n"
                    "*Launching will likely crash the game!*\n"
                    "(Hint: You may want to adjust fins/nosecone)\n\n"
                    "Are you sure you want to simulate flight?",
                    icon="warning"
                )
                if not proceed:
                    return # don't run test flight if user hits no 
            
            #check for overstability based on stability margin
            mach = np.linspace(0, 3, 100) #mach range
            time = np.linspace(0, self.example_solid.burn_out_time, 100) #time range
            max_stability = -9999

            #iterate over the entire surface to find maximum stability margin
            for t in time:
                time_slice = []

                for m in mach:
                    # find the stability margin across the full mach range at the current time
                    time_slice.append(self.rocket.stability_margin(m, t))

                # find the max stability margin at this time step
                local_max = np.max(time_slice)

                # update the max stability margin if a higher value is found
                if local_max > max_stability:
                    max_stability = local_max

            #warn user if overstable
            if max_stability > 3.5:
                proceed = mb.askyesno(
                    "Warning: Rocket is Overstable", #title
                    "Warning: ROCKET IS OVERSTABLE!\n\n"
                    "Stability margin reaches " +str(round(max_stability,4))+ " calibers.\n"
                    "*Launching will likely crash the game!*\n"
                    "(Hint: You may want to adjust fins/nosecone)\n\n"
                    "Are you sure you want to simulate flight?",
                    icon="warning"
                )
                if not proceed:
                    return 

            #create a flight object in RocketPy with user-made rocket, atmosphere from sounding, 90 degree inclination, and 0 degree heading
            self.test_flight = Flight(
                rocket=self.rocket, 
                environment=env, 
                rail_length=10.0, 
                inclination=90, 
                heading=0, 
                terminate_on_apogee=False,
                #max_time_step=10, 
                #min_time_step=0,
                max_time=3000,
                )
            
            self.flown = True
            #process flight data and plot 3d trajectory
            self.test_flight.post_process()
            self.test_flight.plots.trajectory_3d()

            #store important flight data like apogee, max speed
            apogee_altitude = self.test_flight.apogee
            apogee_agl = round((apogee_altitude - env.elevation),3)
            max_speed = round(self.test_flight.max_speed,3)
            max_mach = round(self.test_flight.max_mach_number,3)
            impact_vel = abs(round(self.test_flight.impact_velocity,3))

            ## Display Flight Results to player in tk messagebox ##
            heading_text = "Flight Results"
            default_text = "Your Apogee (above ground): "+str(apogee_agl)+" (m)\nYour Maximum Speed: "+str(max_speed)+" (m/s) or Mach "+str(max_mach)+"\nYour Impact Velocity: "+str(impact_vel)+" (m/s)"
            mission_text = ""
            mission_complete = False

            if self.game_mode == "career":
                #check if user surpassed altitude goal
                if apogee_agl >= self.alt_goal and impact_vel <= self.max_impact_vel:
                    mission_text = "You successfully reached an altitude of: "+str(self.alt_goal)+" (m)!\nYou touched down under: "+str(self.max_impact_vel)+" (m/s)\n\n"
                    heading_text = "Mission Success!"
                    mission_complete = True #allow user to progress if successful
                elif apogee_agl < self.alt_goal:
                    mission_text = "You failed to reach required altitude of: "+str(self.alt_goal)+" (m).\n\n"
                    heading_text = "Mission Failure!"
                else:
                    mission_text = "You hit the ground faster than: "+str(self.max_impact_vel)+" (m/s).\n\n"
                    heading_text = "Mission Failure!"

            mb.showinfo(heading_text, (mission_text+default_text))
            
            # increase player level if sucessful and move to next mission
            if self.game_mode == "career" and mission_complete:

                self.player_level += 1
                # game end condition
                if self.player_level > 3:
                    mb.showinfo("You Win!","Congratulations!\nYou reached space and now you can call yourself a rocket scientist!\nThanks for Playing!")
                    return
                #save the current user level to config.py
                self.save_config()
                #progress to next mission
                self.new_mission()
            
    #Save the current player level to config.py
    def save_config(self):
        
        with open("config.py", 'r') as file:
            lines = file.readlines()
            
        with open("config.py", 'w') as file:
            for line in lines:
                #find the PLAYER_LEVEL line and update with new player level
                if line.startswith("PLAYER_LEVEL"):
                    file.write("PLAYER_LEVEL = "+ str(self.player_level)+"\n")
                else:
                    file.write(line) #otherwise leave config alone

    # display next mission to player
    def new_mission(self):
        #get the mission data for the current player level
        mission_data = self.get_mission_data(self.player_level)

        #display the mission brief using helper function with mission data as parameters
        self.mission_brief(
            title=mission_data["title"],
            description=mission_data["description"],
            alt_goal=mission_data["alt_goal"],
            budget=mission_data["budget"],
            max_impact_vel=mission_data["max_impact_vel"]
        )
        
        #update the rocket and load new parts
        self.refresh_files()
        self.rocket = self.create_rocket()
        self.update_rocket()
        self.draw_rocket()
    
    # display the mission brief in a tk messagebox
    def mission_brief(self, title="untitled mission", description="mission description", alt_goal = 0, budget = 0, max_impact_vel=9999):
        mb.showinfo(title, (description+
                                           "\n\nYour rocket must reach an altitude of: " + str(alt_goal) + " (m)"
                                           +"\nYour mission budget is: $"+str(budget))+
                                           "\nMaximum allowed impact velocity is: "+str(max_impact_vel)+ " (m/s)"
                                           )
        self.budget = budget #store rocket budget
        self.alt_goal = alt_goal #store altitude goal
        self.max_impact_vel = max_impact_vel #store impact velocity goal
    
    # returns dictionary containing mission parameters for each player level
    def get_mission_data(self, level):
        #uses dictionary to access each mission based on level
        missions = {
        1: {
            "title": "Mission 1: First Launch",
            "description": "Welcome to Backyard Space Program!\nYour first mission is to build a basic sounding rocket.",
            "alt_goal": 4000,
            "budget": 3000.00,
            "max_impact_vel": 10.0
        },

        2: {
            "title": "Mission 2: High Altitude",
            "description": "Great work! Now let's aim higher, close to the edge of the stratosphere.\n\n**New Parts Have Unlocked**",
            "alt_goal": 7500,
            "budget": 7000.00,
            "max_impact_vel": 10.0
        },
        3: {
            "title": "Mission 3: Into Space",
            "description": "It's time to reach the final frontier.\nUse your rocket science skills to cross the Karman Line into space.\n\n**New Parts Have Unlocked**",
            "alt_goal": 100000,
            "budget": 13000.00,
            "max_impact_vel": 15.0
        }
    }
        return missions[level]
    
    # welcome message to ask if user wants to hear the tutorial
    def tutorial(self):
        ans = mb.askquestion("Welcome to Backyard Space Program!","Would you like to hear the tutorial?")
        if ans == "yes":
            self.help()
    
    #displays tutorial
    def help(self):
        mb.showinfo("Tutorial",
                        "===How To Play===\n\n"
                        "Left Panel - Rocket Parameters\n"
                        "---------------------------------------\n"
                        "Design rockets by selecting and adjusting parts.\n"
                        "**Click 'Update Rocket' to refresh your changes**\n\n"
                        "Right Panel - Rocket & Mission Info\n"
                        "----------------------------------------------\n"
                        "View information about your rocket and what your current mission requires.\n"
                        "*Part cost is shown on the Left. The Rocket body costs $100/kg*\n\n"
                        "Rocket Stability\n"
                        "--------------------\n"
                        "It is crucial to design rockets carefully so they are stable during flight."
                        "\nFor stability, the Static Center of Pressure must be BEHIND the Center of Mass"
                        "\nTo help, the 'Plot Static Margin' button can show you how stable your rocket is (values < 0 are unstable).\n\n"
                        "Once you are satisfied with your rocket, hit 'LAUNCH' to simulate a flight.\n"
                        "\n(Click 'HELP' anytime to return to this screen)"
        )

        #show additional sandbox tutorial
        if self.game_mode == "sandbox":
            self.sandbox_tutorial()

    # display sandbox information
    def sandbox_tutorial(self):
        mb.showinfo("Welcome to Sandbox Mode!",
                        "===Sandbox Mode===\n\n"
                        "In sandbox mode, you can design rockets without mission/budget constraints.\n\n"
                        "You can design custom parts by clicking the 'Create' buttons.\n"
                        "(Click 'Update Rocket' to refresh files)\n\n"
                        "Have Fun!"
        )

#run the script
if __name__ == "__main__":
    app = RocketViewer()
    app.mainloop() #keep program running indefinitely  