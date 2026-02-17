import pandas as pd
import numpy as np
import random
from triggers import setParallelData
from psychopy import visual, core, event, gui, monitors

"""
Setting Variables
"""
MON_DISTANCE = 60  # Distance between subject's eyes and monitor 
MON_WIDTH = 40  # Width of your monitor in cm
MON_SIZE = [1920, 1080]  # Pixel-dimensions of your monitor
FRAME_RATE=60 # Hz
SAVE_FOLDER = 'EEG_data'

"""
Getting participant info
"""

# Intro-dialogue. Get subject-id and other variables.
# Save input variables in "V" dictionary (V for "variables")
V= {'ID':'','age':'','gender':['female','male','other']}
if not gui.DlgFromDict(V, order=['ID','age','gender']).OK: # dialog box; order is a list of keys 
    core.quit()
"""
Monitor stuff
"""

my_monitor = monitors.Monitor('testMonitor', width=MON_WIDTH, distance=MON_DISTANCE)  # Create monitor object from the variables above. This is needed to control size of stimuli in degrees.
my_monitor.setSizePix(MON_SIZE)

# Use your MON_SIZE variable here
win = visual.Window(
    fullscr=True,       # You requested fullscreen
    monitor=my_monitor, # Use the monitor object you created
    units='deg',         # Or 'pix', 'cm', etc.
    color='black'
)

"""
Specifying time and monitor
"""

stopwatch = core.Clock()


stim_fix = visual.TextStim(win, '+')
"""
Stimuli section
"""
import os
os.chdir(r"C:\Users\asger\OneDrive\Dokumenter\GitHub\eeg_project") #double checking we're in the correct directory

# Load with semicolon
wordlist = pd.read_csv('word_dataset.csv', sep=';')
# Remove spaces from column names
wordlist.columns = wordlist.columns.str.strip()
# FORCE the condition column to be integers
wordlist['condition'] = pd.to_numeric(wordlist['condition'], errors='coerce')

#function for displaying text
def dis_txt(text_to_display):
    #Creates message, draws it and flips the window
    mes = visual.TextStim(win,text_to_display,color="white")
    mes.draw(win)
    win.flip()
    
def experiment(wordlist_df):
    # --- 1. Setup ---
    results = [] 
    
    # Define the questions for each condition
    condition_labels = {
        1: "Includes 'A'?",
        2: "Living?"
    }
    
    # 15-minute timer (900 seconds)
    experiment_timer = core.CountdownTimer(15 * 60)
    
    # avoiding repetition
    used_indices = set()
    
    # --- 2. The Main Loop ---
    while experiment_timer.getTime() > 0:
        
        # A. Randomly choose Condition (1 or 2)
        condition = random.choice([1, 2])
        task_text = condition_labels[condition]
        
        # B. Display the task text (Condition Label) for 1.5 seconds
        dis_txt(task_text)
        core.wait(1.5)
        
        # C. Filter wordlist by condition and pick a random word
        # Note: This assumes your CSV has a column named 'condition'
        # Filter by condition AND remove already-used words
        sub_list = wordlist_df[
            (wordlist_df['condition'] == condition) &
            (~wordlist_df.index.isin(used_indices))
        ]

        if sub_list.empty:
            print(f"No unused words left for condition {condition}")
            continue

        random_row = sub_list.sample(n=1).iloc[0]
        current_word = random_row['word']

        # Mark word as used
        used_indices.add(random_row.name)
        
        # D. Display stimulus word and start timing
        dis_txt(current_word)
        stopwatch.reset()
        
        # E. Wait for user response
        keys = event.waitKeys(keyList=["y", "n", "escape"])
        rt = stopwatch.getTime()
        
        if not keys: continue
        pressed_key = keys[0]

        # Emergency exit - Move this ABOVE the results.append
        if pressed_key == 'escape':
            print("Experiment quit by user.")
            break
        
        #creating the fixation cross for 3 seconds until proceeding with the next word
        win.flip()
        stim_fix.draw()
        win.flip()
        core.wait(3.0)
        
        # F. Record Data (Fixes the Case Sensitivity)
        results.append({
            "ID": V['ID'],         
            "Age": V['age'],       
            "Gender": V['gender'],
            "Condition_ID": condition,
            "Condition_Prompt": task_text,
            "Word": current_word,
            "Response": pressed_key,
            "Reaction_time": rt
        })
        
        # Brief blank screen (Inter-Stimulus Interval) to clear the eyes

    # --- 3. Wrap Up ---
    if results:
        df_experiment = pd.DataFrame(results)
        print(f"Experiment Complete. {len(df_experiment)} trials recorded.")
        return df_experiment
    else:
        print("No data collected.")
        return pd.DataFrame()

# Create the stimulus once at the top of your script
# wrapWidth=30 is a good starting point for 'deg' units to keep text centered
intro_stim = visual.TextStim(win, text="", color="white", height=0.6, wrapWidth=30)

def show_intro(text_list):
    # Join the list into a single string with double line breaks
    formatted_text = "\n\n".join(text_list)
    
    # Update the stimulus and draw
    intro_stim.text = formatted_text
    intro_stim.draw()
    win.flip()
    
    # Wait for the user to press 't' to start
    event.waitKeys(keyList=['t'])

consent_txt = [
    u'Welcome to the experiment!:)',
    u'The data will be used for a Cognitive Science exam project.',
    u'Your data will be anonymized and by continuing you accept that your data will be used.',
    u'It will not be used for any other purpose.'
    u'By pressing "T" you agree to the conditions menioned above and continue'
]

# Define your text list
introText1 = [
    u'The experiment contains 2 conditions:',
    u'1. Includes "A": Press “Y” if the word contains A, “N” if not.',
    u'2. Living?: Press “Y” if it is a living thing, “N” if not.',
    u'Press "T" to begin. The experiment starts 5 seconds after.'
]

# --- 1. Display the Intro and Wait for 'T' ---
show_intro(consent_txt)

show_intro(introText1)

# --- 2. The 5-second countdown wait ---
# Clear text and show fixation
stim_fix.draw()
win.flip()
core.wait(5.0)

# 1. Run the experiment and capture the data
final_data = experiment(wordlist)

# 2. Save the data (using the ID from your GUI)

if not final_data.empty:

    # Create EEG_data folder if it does not exist
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    filename = f"data_p{V['ID']}.csv"
    full_path = os.path.join(SAVE_FOLDER, filename)

    final_data.to_csv(full_path, index=False)

    print(f"Data saved to: {full_path}")

# 3. Clean up
win.close()
core.quit()




