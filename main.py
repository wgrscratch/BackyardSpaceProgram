"""
William Reisman
ENAE380 - Section 102

main.py script creates main menu to launch the game in different modes
"""
#tkinter imports
import tkinter as tk
from tkinter import ttk

import subprocess #launch multiple scripts
import sys

# main menu screen for the game
class TitleScreen(tk.Tk):
    # initialize the screen window
    def __init__(self):
        super().__init__()
        self.title("Backyard Space Program - Main Menu")
        self.geometry("800x500")
        self.configure(bg="#1a1a1a")

        #create the main menu ui
        self.build_ui()

    def build_ui(self):
        #game title
        title_label = tk.Label(
            self,
            text="Backyard Space Program",
            font=("Agency FB", 36, "bold"),
            fg="#dadada",
            bg="#1a1a1a",
        )
        title_label.pack(pady=15)

        # Menu Frame
        menu_frame = tk.Frame(self, bg="#1a1a1a")
        menu_frame.pack()

        # Buttons for launching game and other actions
        career_button = ttk.Button(menu_frame, text="Career Mode", command=self.career, width=20).pack(pady=20)

        sandbox_button = ttk.Button(menu_frame, text="Sandbox Mode", command=self.sandbox,width=20).pack(pady=20)

        about_button = ttk.Button(menu_frame, text="About", command=self.about,width=20).pack(pady=20)

        quit_button = ttk.Button(menu_frame, text="Quit", command=self.quit, width=20).pack(pady=20)

    #writes career mode config to config.py with initial player level and gamemode
    #launches game window, quits main menu
    def career(self):
        with open("config.py", "w") as f:
            f.write("PLAYER_LEVEL = 1\n")
            f.write("GAME_MODE = 'career'")
        subprocess.Popen([sys.executable, "rocket_tk_ui.py"])
        self.quit()
    
    #writes sandbox mode config to config.py with player level and gamemode
    #launches game window, quits main menu
    def sandbox(self):
        with open("config.py", "w") as f:
            f.write("PLAYER_LEVEL = 100\n")
            f.write("GAME_MODE = 'sandbox'")
        subprocess.Popen([sys.executable, "rocket_tk_ui.py"])
        self.quit()

    #Displays the about page
    def about(self):
            
            about_window = tk.Toplevel(self)
            about_window.title("About")
            about_window.geometry("700x600")
            about_window.configure(bg="#1a1a1a")
            
            container = tk.Frame(about_window, bg="#1a1a1a")
            container.pack(fill="both", expand=True, padx=30, pady=20)
            
            # Title
            title_label = tk.Label(
                container,
                text="About",
                font=("Agency FB", 28, "bold"),
                fg="#ffffff",
                bg="#1a1a1a"
            )
            title_label.pack(pady=(0, 10))
            
            
            # description frame with border
            desc_frame = tk.Frame(container, bg="#2d2d44", bd=2)
            desc_frame.pack(fill="x", pady=10)
            
            description = tk.Label(
                desc_frame,
                text="Backyard Space Program simulates realistic rocket launches using RocketPy"
                "\nIn career mode, the player completes a set of missions to meet altitude goals"
                "\nIn sandbox mode, the player can design rockets freely and create custom rocket parts",
                font=("Arial", 13),
                fg="white",
                bg="#2d2d44",
                justify="center",
                padx=20,
                pady=15
            ).pack()

            credit_frame = tk.Frame(container, bg="#2d2d44", bd=2)
            credit_frame.pack(fill="x", pady=10)

            credits = tk.Label(
                credit_frame,
                text="Sources:\n"
                "RocketPy Documentation: https://docs.rocketpy.org/"
                "\nRichard Nakka's Page on Fin Design: https://www.nakka-rocketry.net/RD_fin.htm"
                "\nRocket Motor Data: https://www.thrustcurve.org/"
                "\nReal-Life Rocket Inspirations:"
                "\n   ●https://www.uscrpl.com/traveler-iv"
                "\n   ●https://cosmicresearch.org/bondar/"
                "\n   ●http://www.astronautix.com/s/s-520.html"
                "\n   ●http://www.astronautix.com/a/a-7.html"
                "\nWeather Data: https://weather.uwyo.edu/"
                "\nTkinter Documentation: https://docs.python.org/3/library/tkinter.html",
                font=("Arial", 13),
                fg="white",
                bg="#2d2d44",
                justify="left",
                padx=20,
                pady=15
            )
            credits.pack(anchor="w")

            bottom = tk.Frame(about_window, bg="#1a1a1a")
            bottom.pack(side="bottom", fill="y")
            
            tk.Label(bottom, text="Created by William Reisman",font=("Arial", 12),fg="white",bg="#1a1a1a",).pack(anchor="c", pady=(10, 10))


if __name__ == "__main__":
    app = TitleScreen()
    app.mainloop()
