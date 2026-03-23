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

# Duration in frames (at 60 Hz)
# One frame = 16.67 ms. Trigger pulse held for 1 frame (~16 ms) then reset on next flip.
# This is MORE reliable than core.wait(0.001) which is OS-dependent.
FRAMES_COND_LABEL = 90   # 90 frames = 1.5 s condition label display
FRAMES_FIXATION   = 180  # 180 frames = 3.0 s fixation period
FRAMES_COUNTDOWN  = 300  # 300 frames = 5.0 s pre-experiment countdown

# TRIGGER CODES
TRIG_COND1_LABEL = 2   # Condition 1 task label ("Includes A?") onset
TRIG_COND2_LABEL = 3   # Condition 2 task label ("Living?") onset
TRIG_COND1_WORD  = 4   # Stimulus word onset - condition 1
TRIG_COND2_WORD  = 5   # Stimulus word onset - condition 2
TRIG_RESP_Y      = 6   # Participant pressed "Y"
TRIG_RESP_N      = 7   # Participant pressed "N"

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
Clocks and stimuli
"""
stopwatch = core.Clock()
stim_fix = visual.TextStim(win, '+')

"""
Helper: hold a stimulus on screen for N frames.
On frame 0 the stimulus is already drawn and flipped by the caller.
On frame 1 we reset the trigger to 0 (one-frame pulse).
Remaining frames just re-draw and flip to keep the display stable.
"""
def hold_frames(stim, n_frames):
    """
    Re-draw stim for n_frames additional flips.
    On the very first of those flips, reset the parallel port to 0.
    This gives a clean one-frame trigger pulse without any core.wait().
    """
    for frame in range(n_frames):
        if frame == 0:
            # Schedule trigger reset on the upcoming flip
            win.callOnFlip(setParallelData, 0)
        stim.draw()
        win.flip()


"""
Stimuli section
"""
import os
os.chdir("/Users/nagydomonkos/Desktop/neuroscience/4/eeg_project")

wordlist = pd.read_csv('word_dataset.csv', sep=';')
wordlist.columns = wordlist.columns.str.strip()
wordlist['condition'] = pd.to_numeric(wordlist['condition'], errors='coerce')


def experiment(wordlist_df):
    # --- 1. Setup ---
    results = []
    trigger_log = []

    condition_labels = {
        1: "Includes 'A'?",
        2: "Living?"
    }

    experiment_timer = core.CountdownTimer(15 * 60)
    used_indices = set()

    # Master clock for absolute timestamps
    master_clock = core.Clock()

    # --- 2. Main Loop ---
    while experiment_timer.getTime() > 0:

        # A. Randomly choose condition
        condition = random.choice([1, 2])
        task_text = condition_labels[condition]

        # B. Condition label onset — send trigger on the flip, then hold for 90 frames
        cond_trigger = TRIG_COND1_LABEL if condition == 1 else TRIG_COND2_LABEL
        cond_stim = visual.TextStim(win, task_text, color="white")
        cond_stim.draw()
        win.callOnFlip(setParallelData, cond_trigger)
        win.flip()

        # Log immediately after flip (master_clock.getTime() is as close as we get
        # without hardware timestamping — the EEG trigger is the ground truth)
        trigger_log.append({
            'trigger_code': cond_trigger,
            'trigger_name': 'COND{}_LABEL'.format(condition),
            'onset_time': master_clock.getTime(),
            'trial_number': len(results) + 1,
            'condition': condition,
            'word': '',
            'response': '',
            'rt': ''
        })

        # Hold label for remaining frames (trigger reset happens on frame 0 inside hold_frames)
        # Word selection happens during these frames — no dead time
        sub_list = wordlist_df[
            (wordlist_df['condition'] == condition) &
            (~wordlist_df.index.isin(used_indices))
        ]

        if sub_list.empty:
            print("No unused words left for condition {}".format(condition))
            # Still need to burn the label display frames to keep timing consistent
            hold_frames(cond_stim, FRAMES_COND_LABEL)
            continue

        random_row = sub_list.sample(n=1).iloc[0]
        current_word = random_row['word']
        used_indices.add(random_row.name)

        # Burn remaining label frames (90 frames = 1.5 s total including the first flip)
        hold_frames(cond_stim, FRAMES_COND_LABEL)

        # C. Word onset — trigger + RT clock both scheduled on the flip
        word_trigger = TRIG_COND1_WORD if condition == 1 else TRIG_COND2_WORD
        word_stim = visual.TextStim(win, current_word, color="white")
        word_stim.draw()
        win.callOnFlip(setParallelData, word_trigger)
        win.callOnFlip(stopwatch.reset)  # RT clock starts exactly at word flip
        win.flip()

        trigger_log.append({
            'trigger_code': word_trigger,
            'trigger_name': 'COND{}_WORD'.format(condition),
            'onset_time': master_clock.getTime(),
            'trial_number': len(results) + 1,
            'condition': condition,
            'word': current_word,
            'response': '',
            'rt': ''
        })

        # Reset trigger on next flip, keep word visible while waiting for response.
        # We do a single extra flip to send the reset, then hand off to waitKeys.
        win.callOnFlip(setParallelData, 0)
        word_stim.draw()
        win.flip()

        # D. Wait for response (no time limit — participant must respond)
        keys = event.waitKeys(keyList=["y", "n", "escape"])
        rt = stopwatch.getTime()

        if not keys:
            continue

        pressed_key = keys[0]

        if pressed_key == 'escape':
            print("Experiment quit by user.")
            break

        # E. Response trigger — send immediately (not on a flip, because we
        # are between flips here). Reset on the upcoming fixation flip.
        resp_trigger = TRIG_RESP_Y if pressed_key == "y" else TRIG_RESP_N
        setParallelData(resp_trigger)

        trigger_log.append({
            'trigger_code': resp_trigger,
            'trigger_name': 'RESP_{}'.format(pressed_key.upper()),
            'onset_time': master_clock.getTime(),
            'trial_number': len(results) + 1,
            'condition': condition,
            'word': current_word,
            'response': pressed_key,
            'rt': rt
        })

        # F. Fixation onset — reset response trigger on the fixation flip
        stim_fix.draw()
        win.callOnFlip(setParallelData, 0)
        win.flip()

        # Hold fixation for 180 frames = 3.0 s (trigger reset on frame 0 of hold_frames)
        hold_frames(stim_fix, FRAMES_FIXATION)

        # G. Record trial data
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
        print("Experiment complete. {} trials recorded.".format(len(df_experiment)))
        print("Total triggers logged: {}".format(len(df_triggers)))
        return df_experiment, df_triggers
    else:
        print("No data collected.")
        return pd.DataFrame(), pd.DataFrame()


# --- Intro / consent screens ---
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

# 5-second countdown before first trial — frame loop, no core.wait
setParallelData(0)  # ensure trigger line is clean before we start
for frame in range(FRAMES_COUNTDOWN):
    stim_fix.draw()
    win.flip()

# Run
final_data, trigger_data = experiment(wordlist)

# Save
if not final_data.empty:
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    filename = "data_p{}.csv".format(V['ID'])
    full_path = os.path.join(SAVE_FOLDER, filename)
    final_data.to_csv(full_path, index=False)
    print("Behavioral data saved to: {}".format(full_path))

    trigger_filename = "triggers_p{}.csv".format(V['ID'])
    trigger_path = os.path.join(SAVE_FOLDER, trigger_filename)
    trigger_data.to_csv(trigger_path, index=False)
    print("Trigger log saved to: {}".format(trigger_path))

win.close()
core.quit()