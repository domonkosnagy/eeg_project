

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
os.chdir(r"C:\Users\asger\OneDrive\Dokumenter\GitHub\eeg_project\EEG_data")

wordlist = pd.read_csv('word_dataset.csv', sep=';')
wordlist.columns = wordlist.columns.str.strip()
wordlist['condition'] = pd.to_numeric(wordlist['condition'], errors='coerce')

output_file = pd.read_csv(f'data_p{V["ID"]}.csv')
used_words = set(output_file['Word'].dropna())
all_words = set(wordlist['word'].dropna())

amount_to_draw = len(used_words)//2 #rounds down to the closest integer

remaining_words = list(all_words - used_words)
final_words = random.sample(remaining_words, amount_to_draw)
random.shuffle(final_words)

def dis_txt(text_to_display):
    mes = visual.TextStim(win, text_to_display, color="white")
    mes.draw(win)
    win.flip()


def experiment():
    results = []
    
    # --- 2. The Main Loop ---
    # This loop runs until final_list is empty
    while len(final_list) > 0:
        
        # .pop() takes the last word out of the list and assigns it to current_word
        current_word = final_list.pop() 

        # ── A. Display Stimulus Word ──────────────────────────────────────
        word_stim = visual.TextStim(win, text=current_word, color="white", height=0.1)
        word_stim.draw()
        
        # Reset timer exactly when the word hits the screen
        win.callOnFlip(stopwatch.reset)
        win.flip()

        # ── B. Wait for Response (y/n) ────────────────────────────────────
        # This pauses the script until a key is pressed
        keys = event.waitKeys(keyList=["y", "n", "escape"])
        rt = stopwatch.getTime()

        if not keys:
            continue
        
        pressed_key = keys[0]

        # Emergency exit
        if pressed_key == 'escape':
            print("Experiment quit by user.")
            break

        # ── C. Record Data ────────────────────────────────────────────────
        results.append({
            "ID": V['ID'],
            "Word": current_word,
            "Response": pressed_key,
            "RT": rt
        })

    # --- 3. Wrap Up ---
    if results:
        df_experiment = pd.DataFrame(results)
        print(f"Experiment Complete. {len(df_experiment)} trials recorded.")
        return df_experiment
    else:
        print("No data collected.")
        return pd.DataFrame()


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
    u'This is a memory test designed to test how well you',
    u'recall the words shown in the experiment',
    u'Press "Y" if you believe you saw the word',
    u'Press "N" if you dont recall having seen the word',
    u'Now press "T" to continue'
]

show_intro(consent_txt)
show_intro(introText1)

# 5-second countdown before first trial
stim_fix.draw()
win.flip()
core.wait(5.0)

# ── Run ───────────────────────────────────────────────────────────────────────
final_data = experiment(wordlist)

# ── Save ──────────────────────────────────────────────────────────────────────
if not final_data.empty:
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)
    filename = f"data_p{V['ID']}_memory.csv"
    full_path = os.path.join(SAVE_FOLDER, filename)
    final_data.to_csv(full_path, index=False)
    print(f"Data saved to: {full_path}")

win.close()
core.quit()
