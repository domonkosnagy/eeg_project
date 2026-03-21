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
FRAME_RATE = 60  # Hz
SAVE_FOLDER = 'EEG_data'

# ─── TRIGGER CODES ────────────────────────────────────────────────────────────
TRIG_FIXATION    = 1   # Fixation cross onset
TRIG_COND1_LABEL = 2   # Condition 1 task label ("Includes A?") onset
TRIG_COND2_LABEL = 3   # Condition 2 task label ("Living?") onset
TRIG_COND1_WORD  = 4   # Stimulus word onset - condition 1
TRIG_COND2_WORD  = 5   # Stimulus word onset - condition 2
TRIG_RESP_Y      = 6   # Participant pressed "Y"
TRIG_RESP_N      = 7   # Participant pressed "N"
# ──────────────────────────────────────────────────────────────────────────────

"""
Getting participant info
"""
V = {'ID': '', 'age': '', 'gender': ['female', 'male', 'other']}
if not gui.DlgFromDict(V, order=['ID', 'age', 'gender']).OK:
    core.quit()

"""
Monitor stuff
"""
my_monitor = monitors.Monitor('testMonitor', width=MON_WIDTH, distance=MON_DISTANCE)
my_monitor.setSizePix(MON_SIZE)

win = visual.Window(
    fullscr=True,
    monitor=my_monitor,
    units='deg',
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
os.chdir("/Users/nagydomonkos/Desktop/neuroscience/4/eeg_project")

wordlist = pd.read_csv('word_dataset.csv', sep=';')
wordlist.columns = wordlist.columns.str.strip()
wordlist['condition'] = pd.to_numeric(wordlist['condition'], errors='coerce')


def dis_txt(text_to_display):
    mes = visual.TextStim(win, text_to_display, color="white")
    mes.draw(win)
    win.flip()


def send_trigger(code):
    """Send a trigger code and immediately schedule a reset to 0 on the next flip."""
    setParallelData(code)


def experiment(wordlist_df):
    # --- 1. Setup ---
    results = []
    trigger_log = []  # NEW: Track all triggers with timestamps

    condition_labels = {
        1: "Includes 'A'?",
        2: "Living?"
    }

    experiment_timer = core.CountdownTimer(15 * 60)
    used_indices = set()
    
    # Master clock for absolute timestamps
    master_clock = core.Clock()

    # --- 2. The Main Loop ---
    while experiment_timer.getTime() > 0:

        # ── A. Randomly choose Condition ──────────────────────────────────────
        condition = random.choice([1, 2])
        task_text = condition_labels[condition]

        # ── B. TRIGGER 2/3 — Condition label onset ───────────────────────────
        cond_trigger = TRIG_COND1_LABEL if condition == 1 else TRIG_COND2_LABEL
        cond_stim = visual.TextStim(win, task_text, color="white")
        cond_stim.draw()
        win.callOnFlip(setParallelData, cond_trigger)
        win.flip()
        
        # Log the trigger
        trigger_log.append({
            'trigger_code': cond_trigger,
            'trigger_name': f'COND{condition}_LABEL',
            'onset_time': master_clock.getTime(),
            'trial_number': len(results) + 1,
            'condition': condition,
            'word': '',  # not shown yet
            'response': '',
            'rt': ''
        })
        
        core.wait(0.001)
        setParallelData(0)
        core.wait(1.499)

        # ── C. Filter wordlist ────────────────────────────────────────────────
        sub_list = wordlist_df[
            (wordlist_df['condition'] == condition) &
            (~wordlist_df.index.isin(used_indices))
        ]

        if sub_list.empty:
            print(f"No unused words left for condition {condition}")
            continue

        random_row = sub_list.sample(n=1).iloc[0]
        current_word = random_row['word']
        used_indices.add(random_row.name)

        # ── D. TRIGGER 4/5 — Stimulus word onset ──────────────────────────────
        word_trigger = TRIG_COND1_WORD if condition == 1 else TRIG_COND2_WORD
        word_stim = visual.TextStim(win, current_word, color="white")
        word_stim.draw()
        win.callOnFlip(setParallelData, word_trigger)
        win.callOnFlip(stopwatch.reset)   # start RT clock exactly at word flip
        win.flip()
        
        # Log the trigger
        word_onset_time = master_clock.getTime()
        trigger_log.append({
            'trigger_code': word_trigger,
            'trigger_name': f'COND{condition}_WORD',
            'onset_time': word_onset_time,
            'trial_number': len(results) + 1,
            'condition': condition,
            'word': current_word,
            'response': '',  # not pressed yet
            'rt': ''
        })
        
        core.wait(0.001)
        setParallelData(0)

        # ── E. Wait for response ──────────────────────────────────────────────
        keys = event.waitKeys(keyList=["y", "n", "escape"])
        rt = stopwatch.getTime()

        if not keys:
            continue

        pressed_key = keys[0]

        # Emergency exit
        if pressed_key == 'escape':
            print("Experiment quit by user.")
            break

        # ── TRIGGER 4/5 — Button press (Y or N) ──────────────────────────────
        if pressed_key == "y":
            resp_trigger = TRIG_RESP_Y
            setParallelData(resp_trigger)
        elif pressed_key == "n":
            resp_trigger = TRIG_RESP_N
            setParallelData(resp_trigger)
        
        # Log the trigger
        trigger_log.append({
            'trigger_code': resp_trigger,
            'trigger_name': f'RESP_{pressed_key.upper()}',
            'onset_time': master_clock.getTime(),
            'trial_number': len(results) + 1,
            'condition': condition,
            'word': current_word,
            'response': pressed_key,
            'rt': rt
        })
        
        core.wait(0.001)
        setParallelData(0)

        # ── F. TRIGGER 1 — Fixation cross onset ──────────────────────────────
        stim_fix.draw()
        win.callOnFlip(setParallelData, TRIG_FIXATION)
        win.flip()
        
        # Log the trigger
        trigger_log.append({
            'trigger_code': TRIG_FIXATION,
            'trigger_name': 'FIXATION',
            'onset_time': master_clock.getTime(),
            'trial_number': len(results) + 1,
            'condition': condition,
            'word': current_word,
            'response': pressed_key,
            'rt': rt
        })
        
        core.wait(0.001)
        setParallelData(0)
        core.wait(2.999)          # remainder of the 3 s fixation period

        # ── G. Record Data ────────────────────────────────────────────────────
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

    # --- 3. Wrap Up ---
    if results:
        df_experiment = pd.DataFrame(results)
        df_triggers = pd.DataFrame(trigger_log)
        print(f"Experiment Complete. {len(df_experiment)} trials recorded.")
        print(f"Total triggers logged: {len(df_triggers)}")
        return df_experiment, df_triggers
    else:
        print("No data collected.")
        return pd.DataFrame(), pd.DataFrame()


# ── Intro / consent screens ───────────────────────────────────────────────────
intro_stim = visual.TextStim(win, text="", color="white", height=0.6, wrapWidth=30)


def show_intro(text_list):
    formatted_text = "\n\n".join(text_list)
    intro_stim.text = formatted_text
    intro_stim.draw()
    win.flip()
    event.waitKeys(keyList=['t'])


consent_txt = [
    u'Welcome to the experiment! :)',
    u'The data will be used for a Cognitive Science exam project.',
    u'Your data will be anonymized and by continuing you accept that your data will be used.',
    u'It will not be used for any other purpose.',
    u'By pressing "T" you agree to the conditions mentioned above and continue.'
]

introText1 = [
    u'The experiment contains 2 conditions:',
    u'1. Includes "A": Press "Y" if the word contains A, "N" if not.',
    u'2. Living?: Press "Y" if it is a living thing, "N" if not.',
    u'Press "T" to begin. The experiment starts 5 seconds after.'
]

show_intro(consent_txt)
show_intro(introText1)

# 5-second countdown before first trial
stim_fix.draw()
win.flip()
core.wait(5.0)

setParallelData(0)  # make sure trigger line starts clean

# ── Run ───────────────────────────────────────────────────────────────────────
final_data, trigger_data = experiment(wordlist)

# ── Save ──────────────────────────────────────────────────────────────────────
if not final_data.empty:
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)
    
    # Save trial-by-trial behavioral data
    filename = f"data_p{V['ID']}.csv"
    full_path = os.path.join(SAVE_FOLDER, filename)
    final_data.to_csv(full_path, index=False)
    print(f"Behavioral data saved to: {full_path}")
    
    # Save trigger log
    trigger_filename = f"triggers_p{V['ID']}.csv"
    trigger_path = os.path.join(SAVE_FOLDER, trigger_filename)
    trigger_data.to_csv(trigger_path, index=False)
    print(f"Trigger log saved to: {trigger_path}")

win.close()
core.quit()