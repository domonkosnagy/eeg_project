import pandas as pd
import numpy as np
import random
from psychopy import visual, core, event

"""
Setting Variables
"""

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
Specifying time and monitor
"""

stopwatch = core.Clock()

win = visual.Window(monitor=my_monitor, units='deg', fullscr=True, allowGUI=False, color='black')

stim_fix = visual.TextStim(win, '+')
"""
Stimuli section
"""
import os
os.chdir("C:\Users\asger\OneDrive\Dokumenter\AUdocuments\Cognitive Neuroscience\EEG_experiment") #double checking we're in the correct directory

wordlist=pd.read_csv('wordlist.txt', sep='\t')

#function for displaying text
def dis_txt(text_to_display):
    #Creates message, draws it and flips the window
    mes = visual.TextStim(win,text_to_display,color="white")
    mes.draw(win)
    win.flip()
    
def experiment(wordlist_df):
    # --- 1. Setup ---
    results = [] 
    ID = random.randrange(1000)
    
    # Define the questions for each condition
    condition_labels = {
        1: "Includes 'A'?",
        2: "Living?"
    }
    
    # 15-minute timer (900 seconds)
    experiment_timer = core.CountdownTimer(15 * 60)
    
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
        sub_list = wordlist_df[wordlist_df['condition'] == condition]
        
        if sub_list.empty:
            print(f"Warning: No words found for condition {condition}")
            continue 
            
        random_row = sub_list.sample(n=1).iloc[0]
        current_word = random_row['word'] # Assumes column is named 'word'
        
        # D. Display stimulus word and start timing
        dis_txt(current_word)
        stopwatch.reset()
        
        # E. Wait for user response
        keys = event.waitKeys(keyList=["y","n", "escape"])
        # F. Record Reaction Time and trial info
        rt = stopwatch.getTime()
        
        # Emergency exit
        if pressed_key == 'escape':
            print("Experiment quit by user.")
            break
            
        
        results.append({
            "ID": ID,
            "Condition_ID": condition,
            "Condition_Prompt": task_text,
            "Word": current_word,
            "Response": pressed_key,
            "Reaction_time": rt
        })
        
        # Brief blank screen (Inter-Stimulus Interval) to clear the eyes
        dis_txt("") 
        core.wait(0.2)

    # --- 3. Wrap Up ---
    if results:
        df_experiment = pd.DataFrame(results)
        print(f"Experiment Complete. {len(df_experiment)} trials recorded.")
        return df_experiment
    else:
        print("No data collected.")
        return pd.DataFrame()


win.close()
core.quit()
