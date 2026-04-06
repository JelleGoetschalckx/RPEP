"""
--------------------------

Python script accompanying

    "Reversing Pavlovian Bias: Can (In)Action-Valence Associations be Modified Through Framing in a Go/NoGo Task?",

for the course Research Project Experimental Psychology at Ghent University (1st masters).

--------------------------
@author: Jelle Goetschalckx; supervisor: Prof. dr. Senne Braem
Special thanks to Dr. Zhang Chen for reviewing this code and providing me very useful feedback

Note: works (best) in the Psychopy application or in Python 3.8 or lower
"""
import pandas
import math
import random
import os
from psychopy import visual, data, gui, core, event

# _____ FUNCTIONS _____ #
def star_shape_maker(size, n_points=5, inner_circle=2.0) -> list:
    """
    Calculates all points of a star-shape
    :param inner_circle: Ratio of inner circle
    :param size: Size of the star (diagonal)
    :param n_points: Amount of points the star has (default 5 for classic star)
    :return: list of points (in clockwise rotational order)
    """
    points = []
    for i in range(2 * n_points):
        r = size/2 if i % 2 == 0 else size / (((1 + math.sqrt(5))/inner_circle) ** 2)/2
        angle = math.pi / 2 + i * (math.pi / n_points)
        points.append((r * math.cos(angle), r * math.sin(angle)))
    return points


def info_GUI() -> tuple:
    """
    Asks number, gender and age of participant
    :return: tuple of participant number, gender and age
    """

    info = {'Participant number': 0, 'Age': 0, 'Gender': ['Male', 'Female', 'X', "Prefer not to say"], 'How many hours did you sleep last night?': 0,
            'Handedness': ['Right-handed', 'Left-handed', 'Both-handed'], 'Are you color blind?': ['No', 'Yes'],
            'Do you have normal/corrected to normal vision?': ['Yes', 'No'],
            'Do you have a learning disability?': ['No', 'Yes', 'Prefer not to say']}

    # Show dialogue box
    box = gui.DlgFromDict(dictionary=info, title="Experiment", order = ['Participant number', 'Age', 'Handedness', 'Are you color blind?',
             'Do you hav normal/corrected to normal vision?', 'Do you have a learning disability?',
             'How many hours did you sleep last night?'])
    if not box.OK:
        core.quit()

    return (info["Participant number"], info["Age"], info["Gender"], info["How many hours did you sleep last night?"], info["Handedness"],
            info["Are you color blind?"], info["Do you have normal/corrected to normal vision?"], info['Do you have a learning disability?'], info)


# For testing/debugging
def trial_runner_devstats(trial, feedback, accuracy, response, response_time):
    print(
        f"{'Stimulus':20s} | {trial['color']} {trial['shape_name'].capitalize()}\n"
        f"{'Given Response':20s} | {'Go' if response else 'NoGo'}\n"
        f"{'Correct Response':20s} | {trial['correct_response']}\n",
        f"{'-> Accuracy':20s} = {int(accuracy)} (Time: {response_time if response_time <= 1 else '/'})\n\n",
        f"Given feedback: '{feedback[0]}'",
        f"\n",
        f"Interpretation:\n",
        f"\t {'Feedback should be':20s}| {trial['incentive'].capitalize()} {('received' if accuracy else 'missed') if trial['incentive'] == 'reward' else ('avoided' if accuracy else 'received')}\n",
        f"\t {'Given feedback':20s}| {trial['incentive'].capitalize()} {('received' if feedback == '↑' else 'missed') if trial['incentive'] == 'reward' else ('avoided' if feedback == '-' else 'received')}\n",
        f"{'_' * 50}\n",
        sep="")


# For testing/debugging
def trial_maker_devstats(trials, trial_list):
    data_frame = pandas.DataFrame.from_dict(trials.trialList)
    print(
        f"{'_' * 20}\n"
        f"TABLE OF CREATED TRIALS\n\n",
        pandas.crosstab(data_frame["incentive"], data_frame["correct_response"]),
        f"\n{'_' * 20}\n"
    )
    print(f"LIST OF CREATED TRIALS\n")
    for trial_i, trial in enumerate(trial_list):
        print(trial_i + 1, trial, "\n")
        if not (trial_i + 1) % 8:
            print("__________________\n")
    print(f"{'_' * 30}\n")


def check_correct(answers, correct_answers) -> bool:
    """
    Checks if given answers correspond to correct answers
    :param answers: Given answers (by mouse click)
    :param correct_answers: Correct answers (random every experiment)
    :return:
    """
    color_translation = {
        "Paars": "purple",
        "Geel": "yellow",
        "Roze": "pink",
        "Blauw": "blue"
    }
    check1 = color_translation[answers[0]] == correct_answers[0]
    check2 = answers[1].lower() == correct_answers[1]
    check3 = (answers[2] == "Je neemt de soep mee" and correct_answers[2] == "congruent" or
              answers[2] == "Je gooit de soep weg" and correct_answers[2] == "incongruent")
    return check1 and check2 and check3


class Questionnaire:
    def __init__(self, window, main_exp):
        """
        Asks questions to participant to check whether they read the instructions
        :param window:
        :param main_exp:
        """
        self.win = window
        self.main_exp = main_exp

        self.positions = [(-0.475, 0), (0.475, 0), (-0.475, -0.3), (0.475, -0.3)]
        self.buttons = {
            "1": visual.Rect(self.win, size=(0.85, 0.175), fillColor="lightblue", lineColor="black"),
            "2": visual.Rect(self.win, size=(0.85, 0.175), fillColor="lightblue", lineColor="black"),
            "3": visual.Rect(self.win, size=(0.85, 0.175), fillColor="lightblue", lineColor="black"),
            "4": visual.Rect(self.win, size=(0.85, 0.175), fillColor="lightblue", lineColor="black")
        }
        self.answers = [
            ["Roze", "Geel", "Paars", "Blauw"], ["Driehoeken", "Vierkanten", "Cirkels" ,"Sterren"],
            ["Je krijgt een beloning", "Je gooit de soep weg", "Je neemt de soep mee", "Je laat de soep staan"]
        ]

        self.button_message = visual.TextStim(self.win, height=0.1, color="black")
        self.mouse = event.Mouse(win=self.win, visible=False)

    def ask(self, correct_answers, block_type, repeat_intro=False, ) -> bool:
        """
        Starts 3 questionnaires with 4 clickable options each to check if participant understood the task
        :return: True if correct, else False
        """
        if repeat_intro:
            self.main_exp.communication("questionnaire_intro")
        answers = []
        for i in range(len(self.answers)):
            self.mouse.visible = True
            response = None
            while not response:
                # Draw 4 buttons
                for pos, button, answer in zip(self.positions, self.buttons.values(), self.answers[i]):
                    button.pos = pos
                    button.draw()
                    self.button_message.text = answer
                    self.button_message.pos = pos
                    self.button_message.draw()
                self.main_exp.communication(f"question{i + 1}", pos=(0, 0.4), wait_resp=False, size=0.1, block_type = block_type)

                # Register mouse click
                response = self.mouse_handler()

            answers.append(self.answers[i][int(response) - 1])
            if i != len(self.answers) - 1:
                self.win.flip()
                core.wait(1)
            else:
                self.mouse.visible = False
        return check_correct(answers, correct_answers)

    def mouse_handler(self) -> str:
        """
        Returns name of pressed button during the questionnaires
        :return: Name of pressed button
        """
        # Check if any button is being hovered by the mouse
        for name, button in self.buttons.items():
            while button.contains(self.mouse):
                # Change appearance of mouse to indicate button is clickable
                self.win.winHandle.set_mouse_cursor(self.win.winHandle.get_system_mouse_cursor("hand"))
                # If hovering and pressed: return name of clicked button
                if self.mouse.getPressed()[0]:
                    self.win.winHandle.set_mouse_cursor()
                    return name
                self.main_exp.escape_check()
            # Reset mouse appearance if not hovering any button
            self.win.winHandle.set_mouse_cursor()
        self.main_exp.escape_check()


# _____ EXPERIMENT _____ #
class RPEP_J:
    def __init__(self, bowl_size, save_directory, devstats, info):
        """
        Runs experiment and collects data
        :param bowl_size: Size of stimuli in proportion to screen height
        :param save_directory: Where to store acquired datafile
        :param devstats: Displays more information to developer if True; requires to be False for data collection
        """
        # Settings
        self.devstats = devstats
        self.part_nr, self.gender, self.age, self.color_blind = info
        # If even participant number: congruent block first
        self.blocks = ["congruent", "incongruent"] if not int(self.part_nr) % 2 else ["incongruent", "congruent"]

        # Hardware and timer
        self.win = visual.Window(units="norm", fullscr=not self.devstats) # Fullscreen for real experiment, in-window when testing
        self.win.winHandle.set_mouse_cursor()
        self.timer = core.Clock()

        # Formating
        self.win_height = self.win.size[1]
        self.bowl_size = self.win_height * bowl_size
        # ___ Stimuli ___
        if os.path.exists(os.getcwd() + "/bowl.png"):
            self.bowl = visual.ImageStim(self.win, image=os.getcwd() + "/bowl.png", size=self.bowl_size, units="pix")
        else:
            self.bowl = visual.Circle(self.win, color="white", size=self.bowl_size, units="pix")
        self.bowl_go_visualisation = visual.Circle(self.win, color="black", size=self.bowl_size + 20, units="pix") # 10 pixel edge indication "Go"
        self.soup = visual.Circle(self.win, fillColor="black", size=self.bowl_size * 0.8, units="pix")

        # Shapes
        self.all_colors = ["purple", "blue", "yellow", "pink"]
        random.shuffle(self.all_colors)

        self.shapes = {
            "sterren": visual.ShapeStim(
                    self.win, vertices=star_shape_maker(n_points=5, size=self.bowl_size/7, inner_circle=2),
                    fillColor="black", lineColor="black", units="pix"
                ),
            "driehoeken":
                visual.Polygon(
                    self.win, edges=3, size=self.bowl_size/7,
                    color="black", units="pix",
                ),
            "cirkels":
                visual.Circle(
                    self.win, size=self.bowl_size/7,
                    color="black", units="pix",
                ),
            "vierkanten":
                visual.Rect(
                    self.win, size=math.sqrt((self.bowl_size ** 2) / 2)/7,
                    color="black", units="pix",
                ),
        }

        self.shape_names = [item for item in self.shapes.keys()]  # Easier randomization
        random.shuffle(self.shape_names)

        self.garnish_pos = [(0, 0), (-90, 10), (-40, 120), (100, -100), (20, -80), (-100, -100), (60, 80)]
        if self.win_height != 1080:
            self.garnish_pos = [(x / 1080 * self.win_height, y / 1080 * self.win_height) for x, y in self.garnish_pos]
        self.garnish_ori = [0, 40, 60, 10, 75, 50, 5]

        # Text
        self.message = visual.TextStim(self.win, color="white", height=0.075, wrapWidth=self.win_height/800)

        # ___ Exp handler and score keeping ___
        self.exp_handler = data.ExperimentHandler(
            dataFileName=save_directory + ("Developer_mode" if self.devstats else "") + str(self.part_nr)
        )
        self.total_score = 0
        self.n_correct_trials = 0

    def communication(self, text_key: str, n_block: int=-1, shapes: tuple=None, colors: tuple=None, pos: tuple=(0, 0),
                      wait_resp=True, color="white", size=0.075, flip=True, block_type="", n_trials=-1, wait_time=0.0) -> None:
        """
        Displays text messages on screen and waits for keyboard response
        :param block_type: Congruent or incongruent
        :param colors: Extra info: colors this trial
        :param shapes: Extra info: shapes this trial
        :param n_block: Extra info: block number (0 based)
        :param size: Size of the text
        :param color: Color of the text
        :param text_key: Keyword leading to long text in options-dictionary
        :param pos: Position of text on the screen
        :param wait_resp: Waits for response if True (default)
        :param flip: Flip window if true
        :param n_trials: Amount of trials in entire experiment
        :param wait_time: Duration to pause the game (only if wait_resp=False)
        :return: None
        """
        if colors:
            color_translation = {
                "yellow": "gele",
                "purple": "paarse",
                "blue": "blauwe",
                "pink": "roze"
            }
            reward_color, punish_color = color_translation[colors[0]], color_translation[colors[1]]
        else:
            reward_color = punish_color = ""
        if shapes:
            go_shape, nogo_shape = shapes[0], shapes[1]
        else:
            go_shape = nogo_shape = "NULL"

        options = {
            "intro": f"Welkom!\nIn dit experiment ben je de manager van een restaurant dat gespecialiseerd "
                     f"is in soep met abstracte figuren. Het is vandaag erg druk dus je helpt je collega's met opdienen.\n\n"
                     f"Als klanten het juiste bord soep krijgen, zijn ze bereid meer te betalen. Het is uiteraard je taak "
                     f"om zoveel mogelijk winst te maken.\n\n"
                     f"Druk op spatie voor meer uitleg.",
            "general": f"{'NIEUWE INSTRUCTIES! ' if n_block else ''}Zodra krijg je{' opnieuw ' if n_block else ' '}verschillende borden met soep achter elkaar "
                       f"gepresenteerd{', maar vandaag serveren we andere soep.' if n_block else '.'}\n\n"
                       f"Omdat {punish_color} soep erg duur is om te maken, maak je hier altijd verlies op. "
                       f"{reward_color.capitalize()} soep is zeer goedkoop, dus hierop maak je altijd winst.\n\n"
                       f"Wanneer je de soep te zien krijgt, is hij nog niet helemaal afgewerkt. Je moet eerst even wachten "
                       f"tot er figuren op de soep gestrooid worden, dan pas is hij klaar om geserveerd te worden.\n\n"
                       f"Door telkens een juiste keuze te maken, kan je je winst maximaliseren en je verliezen beperken.\n\n"
                       f"Druk op spatie voor meer informatie.",
            "congruent": f"Vandaag is het jouw taak om de mensen te bedienen die soep met {go_shape} hebben besteld, de soep met "
                         f"{nogo_shape} moet je laten staan voor je collega's. Als je de soep wilt meenemen, moet je zo "
                         f"snel mogelijk reageren, voor één van je collega's het meeneemt naar de foute tafel.\n\nJe neemt de soep met {go_shape} mee "
                         f"door op spatie te drukken en je laat hem staan door niets te doen.\n\n"
                         f"Druk op spatie voor een korte samenvatting.",
            "incongruent": f"Vandaag bestelden je klanten alleen maar soep met {nogo_shape}! Helaas is de verantwoordelijke "
                           f"voor de figuren vandaag een jobstudent, die per ongeluk vaak toch {go_shape} op de soep doet.\n\n"
                           f"Omdat niemand anders voor deze taak opgeleid is, heb je besloten dat je gewoon elk bord soep waar "
                           f"{go_shape} in belanden, zo snel mogelijk in de vuilnisbak zal werpen. De soep met {nogo_shape} "
                           f"moet je laten staan, je collega's zullen deze serveren. Je gooit de soep weg door op de spatiebalk "
                           f"te duwen en je laat hem staan door niets te doen.\n\n"
                           f"Druk op spatie voor een korte samenvatting.",
            "overview": f"Kortom:\n\n\n"
                        f"{reward_color.upper()} soep → altijd WINST, maar meer als correct\n\n"
                        f"{punish_color.upper()} soep → altijd VERLIES, maar meer als fout\n\n"
                        f"-----------------\n\n"
                        f"Vanaf er figuren in de soep liggen, moet je een keuze maken:\n\n"
                        f"{go_shape.upper()} in de soep → Deze moet je SNEL {'MEENEMEN' if block_type == 'congruent' else 'WEGGOOIEN'} (spatie)\n\n"
                        f"{nogo_shape.upper()} in de soep → Deze moet je LATEN STAAN (niets doen)\n\n\n"
                        f"Druk op spatie om verder te gaan.",
            "questionnaire_intro": "Voor de taak begint, krijg je eerst drie korte vragen (zonder tijdslimiet) om te checken of "
                                   "je de taak goed begrepen hebt.\n\n"
                                   "Druk op spatie om naar de eerste vraag te gaan.",
            "question1": "Op welke kleur soep maak je altijd verlies?\n(Klik op het juiste antwoord)",
            "question2": f"Welke soep moet jij {'meenemen' if block_type == 'congruent' else 'weggooien'}?\n(Klik op het juiste antwoord)",
            "question3": f"Welke actie voer je uit wanneer je op spatie drukt?\n(Klik op het juiste antwoord)",
            "question_wrong": "Niet al je antwoorden waren correct.\n\nDruk op spatie om terug te keren naar de instructies.",
            "start_trials": f"Zeer goed! Je krijgt {'nu' if not n_block else 'net zoals daarnet'} de soepborden één voor "
                            f"één gepresenteerd. Denk er aan dat je maar weinig tijd hebt om een keuze te maken, maak dus snel een keuze!\n\n"
                            f"Druk op spatie als je klaar bent om te beginnen.",
            "break": "Tijd voor een pauze. Wanneer je klaar bent om verder te gaan, druk je op spatie voor meer instructies.",
            "end": f"Je hebt het einde van dit experiment bereikt, bedankt om deel te nemen!\n\n"
                    f"Je maakte in totaal {self.n_correct_trials} van de {n_trials} keer een juiste keuze ({self.n_correct_trials/n_trials*100}%). Daarmee maakte je restaurant in totaal €{abs(self.total_score)} {'winst' if self.total_score >=0 else 'verlies'}!\n\n"
                    f"Druk op spatie om af te sluiten.",
            "early_quit": "Experiment werd afgesloten met escape.",
            "grabbed": f"Je nam de soep mee",
            "thrown away": f"Je gooide de soep weg",
            "did nothing": f"Je liet de soep staan",
            "+10": "+10",
            "+1": "+1",
            "-1": "-1",
            "-10": "-10",
        }
        self.message.text = options[text_key]
        if pos:
            self.message.pos = pos
        if text_key in ("+10", "+1"):
            self.message.color = "green"
        elif text_key in ("-10", "-1"):
            self.message.color = "red"
        elif text_key == "0":
            self.message.color = "black"
        else:
            self.message.color = color
        self.message.size = size

        self.message.draw()
        if flip:
            self.win.flip()

        if wait_resp:
            response = event.waitKeys(keyList=["space", "escape"])[0]
            if response == "escape":
                self.communication("early_quit")
                core.quit()
        else:
            core.wait(wait_time)
            if text_key != "early_quit":
                self.escape_check()

    def escape_check(self, response=""):
        if not response:
            escape = event.getKeys(keyList="escape")
        else:
            escape = response
        if "escape" in escape:
            self.communication("early_quit", wait_resp=False, wait_time=1)
            core.quit()
        return 0

    def trial_maker(self, n_trials: int, fix_cross_duration: list, block_type: str) -> tuple:
        """
        Creates n_trials amount of trials
        :param fix_cross_duration: Duration of display of the fixation cross (list of min/max)
        :param block_type: Are trials congruent or incongruent to Pavlovian bias?
        :param n_trials: Total amount of trials in 1 block
        :return: TrialHandler with generated trials
        """
        # Pop shapes and colors from stim lists (will not be reused across blocks)
        shapes_this_block = {
            "Go": self.shape_names.pop(),
            "NoGo": self.shape_names.pop()
        }
        colors_this_block = {
            "reward": self.all_colors.pop(),
            "punishment": self.all_colors.pop()
        }

        # Make trials
        trial_list = []
        counter = 1
        for i in range(int(n_trials/8)):
            new_part = []
            for _ in range(2):
                for response, incentive in zip(["Go", "NoGo"]*2, ["reward", "punishment", "punishment", "reward"]):
                    new_part.append(
                        {
                            "block_type": block_type,
                            "shape_name": shapes_this_block[response],
                            "correct_response": response,
                            "color": colors_this_block[incentive],
                            "incentive": incentive,
                            "fix_cross_time": random.randint(fix_cross_duration[0], fix_cross_duration[1]) / 1000,
                            "order_per_8": counter%8 + 1 # Keep track of original order (before randomization, per 8)
                        }
                    )
                    counter += 1
            random.shuffle(new_part)
            trial_list += new_part

        # Add to TrialHandler and ExperimentHandler
        trials = data.TrialHandler(trial_list, nReps=1, method="sequential")
        self.exp_handler.addLoop(trials)

        if self.devstats:
            trial_maker_devstats(trials, trial_list)

        return (shapes_this_block["Go"], shapes_this_block["NoGo"]), (colors_this_block["reward"], colors_this_block["punishment"]), trials


    def trial_runner(self, trials, feedback_duration: float, response_deadline: float, intertrial_interval: float, times_instructions_read) -> None:
        """
        Show created trials, wait for (optional) response and store data in file
        :param times_instructions_read: Amount of times participants read instructions
        :param intertrial_interval: Time between feedback and next fixation cross appearing
        :param trials: Trials created using self.trial_maker()
        :param response_deadline: Time (s) to give response or to wait if inhibiting response
        :param feedback_duration: Time (s) during which feedback and result of action is displayed
        :return: None
        """
        for i, trial in enumerate(trials):
            # ___ TRIAL ___
            # Intertrial interval
            self.win.flip()
            core.wait(intertrial_interval)
            # Draw bowl with soup
            self.soup.color = trial["color"]
            self.draw_stimuli(trial)
            core.wait(trial["fix_cross_time"])

            # Put garnish shapes on top
            self.timer.reset()
            self.escape_check()

            self.draw_stimuli(trial, garnish=True)

            # ___ RESPONSE ___
            self.timer.reset()

            response = event.waitKeys(keyList=["space", "escape"], maxWait=response_deadline)

            response_time = self.timer.getTime()
            self.escape_check(response)
            if response:
                self.draw_stimuli(trial, garnish=True, bowl_action=True)

            # If Go before response_deadline: keep displaying stimulus for remaining time (skips if crossed deadline (negative value))
            core.wait(response_deadline - self.timer.getTime())

            # ___ FEEDBACK AND DATA ___
            accuracy, feedback_points, feedback_text = self.outcome_handler(trial, response, response_time)
            self.communication(feedback_points, wait_resp=False, size=0.2, flip=False)
            self.communication(feedback_text, wait_resp=False, pos=(0, -0.2,), wait_time=feedback_duration)
            self.escape_check()

            # Add data to datafile
            trials.addData("incentive", trial["incentive"])  # reward/punishment
            trials.addData("block_type", trial["block_type"])  # congruent/incongruent
            trials.addData("given_response", "Go" if response else "NoGo")  # Go/NoGo
            trials.addData("accuracy", int(accuracy))  # 0/1
            trials.addData("feedback", feedback_points)  # +10/0/-10
            trials.addData("response_time", response_time if response_time <= response_deadline else None)  # float

            # General information
            trials.addData("participant_nr", self.part_nr)
            trials.addData("participant_gender", self.gender)
            trials.addData("participant_age", self.age)
            trials.addData("colorblind", 1 if self.color_blind == "Yes" else 0)
            trials.addData("times_instructions_read", times_instructions_read)
            self.exp_handler.nextEntry()

    def draw_stimuli(self, trial, garnish=False, bowl_action=False):
        if bowl_action: self.bowl_go_visualisation.draw()
        self.bowl.draw()
        self.soup.draw()
        if garnish:
            shape = self.shapes[trial["shape_name"]]
            for pos, ori in zip(self.garnish_pos, self.garnish_ori):
                shape.pos = pos
                shape.ori = ori
                shape.draw(self.win)
        self.win.flip()

    def outcome_handler(self, trial, response, response_time) -> tuple:
        """
        Calculates outcome of trial, based on response
        :param trial: trial within TrialHandler object
        :param response: pressed key (Space or None)
        :param response_time: If Go: time elapsed between stimulus presentation and button press, None if NoGo
        :return: accuracy (0 or 1) and given feedback (of which 80% is correct)
        """
        # Example: if correct answer and reward trial: 80% chance to get the reward, 20% to get nothing
        # Example 2: if correct answer and punishment trial: 80% chance to avoid punishment, 20% to get punishment nonetheless
        accuracy = (
            (response and trial["correct_response"] == "Go") or
            (not response and trial["correct_response"] == "NoGo")
        )

        if trial["incentive"] == "reward":
            if accuracy:
                feedback_points = "+10"
                self.n_correct_trials += 1
            else:
                feedback_points = "+1"
        else:
            if accuracy:
                feedback_points = "-1"
                self.n_correct_trials += 1
            else:
                feedback_points = "-10"
        self.total_score += int(feedback_points)

        feedback_text = ("grabbed" if trial["block_type"] == "congruent" else "thrown away") if response else "did nothing"

        # Optional: print details if devstats == True
        if self.devstats:
            trial_runner_devstats(trial, feedback_points, accuracy, response, response_time)

        return accuracy, feedback_points, feedback_text


    def main(self, n_trials_per_block: int, fix_cross_duration: list, feedback_duration: float, response_deadline: float,
             intertrial_interval: float) -> None:
        """
        Runs experiment
        :param intertrial_interval: Time between feedback and next fixation cross appearing
        :param n_trials_per_block: Total amount of trials per block
        :param fix_cross_duration: Min and Max time (ms) during which the fixation cross is displayed
        :param feedback_duration: Time during which the feedback is displayed
        :param response_deadline: Max time to give a response
        :return: None
        """
        self.communication("intro")

        for i, block_type in enumerate(self.blocks):
            # Create trials
            shapes, colors, trials_this_block = self.trial_maker(n_trials_per_block, fix_cross_duration, block_type=block_type)

            # Instructions and questionnaire until all questions correctly answered
            all_correct = False
            times_instructions_read = 1
            while not all_correct:
                self.communication(text_key="general", n_block=i, colors=colors)
                self.communication(text_key=block_type, shapes=shapes, colors=colors, n_block=i)
                self.communication("overview", shapes=shapes, colors=colors, block_type=block_type)

                # Questionnaire itself
                all_correct = Questionnaire(self.win, main_exp=self).ask(correct_answers=[colors[1], shapes[0], block_type], repeat_intro=not times_instructions_read - 1, block_type=block_type)
                if not all_correct:
                    self.communication("question_wrong")
                    times_instructions_read += 1
                else:
                    self.communication("start_trials", n_block=i)
            # Run trials
            self.trial_runner(trials_this_block, feedback_duration, response_deadline, intertrial_interval, times_instructions_read)

            # Give break (except after the final block)
            if i != len(self.blocks) - 1:
                self.communication("break")
        self.communication("end", n_trials=n_trials_per_block*len(self.blocks))
        self.win.close()


def LeeCode(part_numb, info):
    ### Python Code for Research Project Experimental Psychology ###
    ### From Evelien Janssens (student number 02200251)          ###
    ### Based on code of Brent Vernaillen                        ###
    ### Supervised by Prof. Louisa Bogaerts                      ###

    ##   Import the required modules   ##
    from psychopy import visual, event, core
    import numpy, random, itertools, time
    import pandas as pd
    from pathlib import Path


    ## file handling ##

    # create directory in C:/documents/ drive
    directory_to_write_to = os.path.join(os.getcwd(), "EJ_RPEP_Singleton_Experiment_Data")
    directory_to_write_to = Path.home() / "Documents" / "EJ_RPEP_Singleton_Experiment_Data"
    directory_to_write_to.mkdir(parents=True, exist_ok=True)

    # use participant number to create unique file name
    filename = f"EJ_RPEP_Subject_{part_numb}_Data.csv"
    file_path = directory_to_write_to / filename

    # check if file with subj number exists, add suffix if yes
    if file_path.exists():
        suffix = 1
        while True:
            candidate = directory_to_write_to / f"EJ_RPEP_Subject_{part_numb}_Data_{suffix}.csv"
            if not candidate.exists():
                file_path = candidate
                break
            suffix += 1

    ##   Experiment Parameters   ##

    # Experiment structure
    nBlocks = 3
    nTrials = 200
    yes_HPDL = 0.65  # percentage of the trial
    yes_distractor = 0.5  # percentage of trails that contain a distractor
    explicit_test_trials = (
    20, 40, 60, 80, 100, 120, 140, 160, 180, 200)  # after which trial numbers location+confidence test

    # assign to CONTROL or EXPERIMENT group based on participant number
    # '0' if participant number is even, else '1' (uneven participant number)
    # '0' is control group, '1' is experiment group
    control_or_experiment = part_numb % 2

    # HPDL + their ORDER based on participant number
    # this absolutely needs to be saved
    hpdl_locs = [0, 2, 4]  # per block a HPDL, check to see how many blocks!
    hpdl_locs_seq = list(itertools.permutations(hpdl_locs))  # generate all possible sequences of the HPDLocations
    index = (part_numb - 1) % len(hpdl_locs_seq)  # via moula assign to a specific order
    hpdl_list = hpdl_locs_seq[index]

    # Timing
    interTrialInterval = 0.100  # seconds
    responseDeadline = 3  # Seconds

    # Display settings to run on 6pc lab monitors
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080

    def norm_to_pix_pos(pos):
        return pos[0] * (SCREEN_WIDTH / 2), pos[1] * (SCREEN_HEIGHT / 2)

    def norm_to_pix_size(size):
        return size[0] * (SCREEN_WIDTH / 2), size[1] * (SCREEN_HEIGHT / 2)

    def norm_to_pix_y(value):
        return value * (SCREEN_HEIGHT / 2)

    # Stimuli sizes (converted from norm units to pixels)
    circleRadius = norm_to_pix_y(0.05 * 2)  # 5% of the screen size (2) is 0.1
    diamondSize = norm_to_pix_y(0.08 * 2)  # 8% of the screen size (2) is 0.16
    targetSize = norm_to_pix_y(0.04 * 2)  # 4% of the screen size (2) is 0.08
    textSize = norm_to_pix_y(0.07)  # The height of text elements

    # Colors
    lineColor = (-1, -1, -1)  # Black
    stimulus_colors = [(1.0000, -0.5000, -0.5000), (-0.0667, 0.6549, -0.7412)]  # [red, green]
    backgroundColor = (0.75, 0.75, 0.75)  # A light grey
    textColor = (-1, -1, -1)  # Black

    # Responding
    # The participant should only press these keyboard clicks
    validKeys = ['up', 'left']  # during search task
    location_keys = ['1', '2', '3', '4', '5', '6']  # during location test

    # locations
    posList = [
        norm_to_pix_pos((0.0, 0.75)),  # 12 uur, shape 1
        norm_to_pix_pos((0.40, 0.35)),  # 2 uur, shape 2
        norm_to_pix_pos((0.40, -0.35)),  # 4 uur, shape 3
        norm_to_pix_pos((0.0, -0.75)),  # 6 uur, shape 4
        norm_to_pix_pos((-0.40, -0.35)),  # 8 uur, shape 5
        norm_to_pix_pos((-0.40, 0.35))  # 10 uur, shape 6
    ]

    # all shape 'IDs'
    posIndices = [i for i in range(6)]

    # Half of the shapes will get a horizontal line (45), and half will get a vertical line (-45)
    lineOris = [-45,
                -45,
                -45,
                45,
                45,
                45]

    ##   Experiment Components   ##

    # Window
    win = visual.Window(fullscr=True,
                        size=(SCREEN_WIDTH, SCREEN_HEIGHT),  # hardcoded for the monitors in the lab
                        units="pix",
                        color=backgroundColor)  # Correct background colour

    # Response clock (used for measuring the reaction time each trial)
    responseTimer = core.Clock()

    # Define the typical cirlce shape
    CircleStim = visual.Circle(win,
                               radius=circleRadius,
                               edges='circle',
                               lineColor=(-1, -1, -1),  # Placeholder, will be updated later
                               fillColor=(-1, -1, -1),  # Placeholder, will be updated later
                               pos=(0, 0))  # Placeholder, will be updated later

    # Define the diamond (target) shape
    DiamondStim = visual.Rect(win,
                              width=diamondSize,
                              height=diamondSize,
                              lineColor=(-1, -1, -1),  # Placeholder, will be updated later
                              fillColor=(-1, -1, -1),  # Placeholder, will be updated later
                              ori=45,
                              pos=(0, 0))  # Placeholder, will be updated later

    # make list to randomly allocate the shapes
    stimulus_shapes = [CircleStim, DiamondStim]

    # Define the actual target (line)
    TargetStim = visual.Line(win,
                             size=targetSize,
                             lineColor=lineColor,  # !
                             pos=(0, 0),  # Placeholder, will be updated later
                             ori=0,  # Placeholder, will be updated later
                             lineWidth=5)  # In pixels!

    # Define the fixation cross
    FixCross = visual.TextStim(win,
                               text='+',
                               height=textSize,
                               color='Black',
                               pos=(0, 0))

    # responding functions (to make it possible to press escape at anytime)
    def check_for_escape():
        if 'escape' in event.getKeys(keyList=['escape']):
            win.close()
            core.quit()

    def wait_for_keys(key_list, max_wait=None):
        event.clearEvents()
        key_list = list(key_list) + ['escape']
        if max_wait is None:
            keys = event.waitKeys(keyList=key_list)
        else:
            keys = event.waitKeys(maxWait=max_wait, keyList=key_list)
        if keys and 'escape' in keys:
            win.close()
            core.quit()
        return keys

    ## DATA MATRIX for storing the data
    ExperimentalGroup = numpy.repeat(control_or_experiment, nBlocks * nTrials)
    BlockNr = numpy.repeat(-1, nBlocks * nTrials)
    TrialNr = numpy.repeat(-1, nBlocks * nTrials)
    HPDL_block = numpy.repeat(-1, nBlocks * nTrials)
    TargLoc = numpy.repeat(-1, nBlocks * nTrials)
    TargetShape = numpy.repeat('Shrubbery', nBlocks * nTrials)
    TargetColor = numpy.repeat('Shrubbery', nBlocks * nTrials)
    DistractorPresence = numpy.repeat(-1, nBlocks * nTrials)
    Distractor_on_HPDL = numpy.repeat(-1, nBlocks * nTrials)
    DistrLoc = numpy.repeat(-1, nBlocks * nTrials)
    TargetLineOri = numpy.repeat('Shrubbery', nBlocks * nTrials)
    Response = numpy.repeat('Shrubbery', nBlocks * nTrials)
    Accuracy = numpy.repeat(-1, nBlocks * nTrials)
    ReactionTime = numpy.repeat(-1, nBlocks * nTrials)
    LocTestTarget = numpy.repeat(numpy.nan, nBlocks * nTrials)
    ConfTestTarget = numpy.repeat(numpy.nan, nBlocks * nTrials)
    LocTestDistractor = numpy.repeat(numpy.nan, nBlocks * nTrials)
    ConfTestDistractor = numpy.repeat(numpy.nan, nBlocks * nTrials)

    dataMatrix = numpy.column_stack([ExperimentalGroup,
                                     BlockNr,
                                     TrialNr,
                                     HPDL_block,
                                     TargLoc,
                                     TargetShape,
                                     TargetColor,
                                     DistractorPresence,
                                     Distractor_on_HPDL,
                                     DistrLoc,
                                     TargetLineOri,
                                     Response,
                                     Accuracy,
                                     ReactionTime,
                                     LocTestTarget,
                                     ConfTestTarget,
                                     LocTestDistractor,
                                     ConfTestDistractor])

    # Text stim
    textElement = visual.TextStim(win,
                                  'Shrubbery',
                                  color=textColor,
                                  height=textSize,
                                  wrapWidth=norm_to_pix_size((1.8, 0))[0])

    feedbackText = visual.TextStim(win,
                                   'Shrubbery',
                                   color=textColor,
                                   height=textSize)
    proceedText = visual.TextStim(win,
                                  'Press space to proceed',
                                  color=textColor,
                                  height=textSize,
                                  pos=norm_to_pix_pos((0, -0.8)))

    uncertainty_labels = ['Completely\nuncertain', 'Moderately\nuncertain', 'Slightly\nuncertain',
                          'Neutral', 'Slightly\ncertain', 'Moderately\ncertain', 'Completely\ncertain']

    confidenceText = 'How certain are you of this choice?\ndrag the red dot and release to answer.'
    locationText_target = 'Where do you think the unique SHAPE will appear next?\n Answer by typing the number (on KEYBOARD) of the location you want to choose'
    locationText_distractor = 'Where do you think the unique COLOR will appear next?\n Answer by typing the number (on KEYBOARD) of the location you want to choose'

    # rating scale confidence test
    Rating = visual.Slider(
        win,
        units="pix",
        ticks=(1, 2, 3, 4, 5, 6, 7),
        labels=uncertainty_labels,
        pos=norm_to_pix_pos((0, -0.2)),
        size=norm_to_pix_size((1.2, 0.04)),
        style="rating",
        granularity=1,
        color='Black',
        lineColor='Black',
        markerColor='DarkRed',
        labelHeight=norm_to_pix_y(0.025),
        startValue=4,
        font='Open Sans'
    )

    # visual task instructions
    # pixels of the png files (to de-morph)
    h1 = (932 / 2300)
    h2 = (778 / 1962)

    # upload visual images of task instructions + location test visualizer
    instruc_text_left = visual.ImageStim(
        win,
        size=norm_to_pix_size((1, h2)),
        image="instructions_left.jpg",
        pos=norm_to_pix_pos((0.0, -0.15))
    )
    instruc_text_up = visual.ImageStim(
        win,
        size=norm_to_pix_size((1, h1)),
        image="instructions_up.jpg",
        pos=norm_to_pix_pos((0.0, -0.55))
    )
    instruc_text_handplacement = visual.ImageStim(
        win,
        image="instructions_handplacement.jpg",
        pos=norm_to_pix_pos((0, -0.25)),
        size=norm_to_pix_size((1, 1))
    )
    image_locationtest = visual.ImageStim(
        win,
        image="locationtest_visual.jpg",
        pos=norm_to_pix_pos((0, -0.25)),
        size=norm_to_pix_size((1.2, 1.2))
    )

    ##   THE ACTUAL EXPERIMENT   ##

    # Welcome the participant (only first name, capitalized)
    textElement.text = f"Welcome to this experiment!"
    textElement.draw()
    proceedText.draw()
    win.flip()
    wait_for_keys(['space'])

    # Present instructions SCREEN 1
    textElement.text = "Instructions 1/2 \n You will see a screen with several shapes. \n In each trial, one shape will have a different shape than all the others (for example, one circle among squares, or one square among circles). \n \nEach shape contains a line. Your task is to find the shape with the unique shape and report the orientation of the line inside it: \n Horizontal line (—) → press 'Left' arrow on keyboard \n Vertical line (|) → press 'Up' arrow on keyboard"
    textElement.pos = norm_to_pix_pos((0.0, 0.55))
    textElement.draw()
    proceedText.draw()
    instruc_text_left.draw(win)
    instruc_text_up.draw(win)
    win.flip()
    wait_for_keys(['space'])

    # Present instructions SCREEN 2
    textElement.text = "Instructions 2/2\nThe shapes can have different colors, you can ignore this. \n Always respond based on unique shape, not color. \n\n Keep index finger and middle finger on the two keys for fast responses.\nYou can put the keyboard in a comfortable position. \nPlease respond as quickly and accurately as possible."
    textElement.pos = norm_to_pix_pos((0.0, 0.6))
    textElement.draw()
    proceedText.draw()
    instruc_text_handplacement.draw(win)
    win.flip()
    wait_for_keys(['space'])

    ##   Block Loop   ##

    for block in range(nBlocks):

        HPDL = hpdl_list[block]  # choose High probability Distractor Location out personalized order
        textElement.text = f"Block {block + 1}/{nBlocks} will start now"  # announce block start
        textElement.draw()
        proceedText.draw()
        win.flip()
        wait_for_keys(['space'])  # Wait for key press

        # make list to indicate of the distractor will be on the HPDL (65% of the trials)

        n_DistractorTrials = round(
            nTrials * yes_distractor)  # how much trials in absolute numbers will contain a distractor
        nHPDL = round(
            n_DistractorTrials * yes_HPDL)  # how many of those are on the HPDL & how many are somewhere else? (absolute numbers)
        nNonHPDL = n_DistractorTrials - nHPDL
        yesVSno_hpdl = [1] * nHPDL + [0] * nNonHPDL  # make a list of '1' and '0' with these respective absolute numbers
        random.shuffle(yesVSno_hpdl)
        distractor_counter = 0  # we need a counter to remember how much distractor containing trials have passed

        # make list to indicate if there will be a distractor in this trail (50% of the trials)

        yesVSno_distractor = [1] * round(nTrials * yes_distractor) + [0] * round(nTrials * (1 - yes_distractor))
        random.shuffle(yesVSno_distractor)

        ##   Trial Loop   ##
        for trial in range(nTrials):

            ## inter trial interval ##
            ITI = random.uniform(0.500, 0.750)  # gives a random nuber between these two
            FixCross.draw()
            win.flip()
            time.sleep(ITI)

            ##   One trial   ###

            # decide if this trial contains a distractor or not
            if yesVSno_distractor[trial]:  # there is a distractor

                # decide if it's a yes-HPDL trial or no-HPDL trial
                # we need to select from our specific list for yes-distractor trials
                # is_hpdl_trial now contains a '0' or a 1' for this specific trial
                is_hpdl_trial = yesVSno_hpdl[distractor_counter]
                # do the counter + 1 so we select the next element in the following distractor containing trial
                distractor_counter += 1

                if is_hpdl_trial:  # if its 1 the distractor should appear on this blocks' HPDL
                    # Distractor is on the HPDL
                    distractorLocation = HPDL

                else:
                    # Distractor appears on random location that is not the HPDL but on a random other location
                    no_hpdl_Locs = posIndices.copy()
                    no_hpdl_Locs.remove(HPDL)
                    distractorLocation = numpy.random.choice(no_hpdl_Locs)

                # Remove distractor location from location list
                neutralLocs = posIndices.copy()
                neutralLocs.remove(distractorLocation)

                # Select random target location
                targetLocation = numpy.random.choice(neutralLocs)
                # Select random target and distractor color
                targetColor, distractorColor = random.sample(stimulus_colors, 2)
                # to save in datamatrix
                if targetColor == (1.0000, -0.5000, -0.5000):
                    color_of_target = 'red'
                else:
                    color_of_target = 'green'

                # Select random target and distractor shape
                targetShape, distractorShape = random.sample(stimulus_shapes, 2)
                # to save in datamatrix
                if targetShape == CircleStim:
                    shape_of_target = 'circle'
                else:
                    shape_of_target = 'diamond'

                # Next we define the neutral locations (no distractor or target)
                neutralLocs = posIndices.copy()
                neutralLocs.remove(targetLocation)
                neutralLocs.remove(distractorLocation)

                # With both the target and distractor location chosen, we proceed to draw everything
                # First, we draw the non-distractor circles

                for loc in neutralLocs:  # neutrals have the same shape as the distractor
                    distractorShape.pos = posList[loc]
                    distractorShape.color = targetColor
                    distractorShape.draw()

                # Second, we draw the target

                targetShape.pos = posList[targetLocation]
                targetShape.lineColor = targetColor
                targetShape.fillColor = targetColor
                targetShape.draw()

                # Third, we draw the distractor shape

                distractorShape.pos = posList[distractorLocation]
                distractorShape.color = distractorColor
                distractorShape.draw()

            else:  # there is NO distractor

                # select random target location
                neutralLocs = posIndices.copy()
                targetLocation = numpy.random.choice(neutralLocs)

                # select random target color only (all stimuli will have the same color)
                targetColor = random.choice(stimulus_colors)
                # to save in datamatrix
                if targetColor == (1.0000, -0.5000, -0.5000):
                    color_of_target = 'red'
                else:
                    color_of_target = 'green'

                # Select random target and distractor shape
                targetShape, neutralShape = random.sample(stimulus_shapes, 2)
                # to save in datamatrix
                if targetShape == CircleStim:
                    shape_of_target = 'circle'
                else:
                    shape_of_target = 'diamond'

                # Next we define the neutral locations (no target)
                neutralLocs.remove(targetLocation)

                # With the target location chosen, we proceed to draw the neutral locations (no distractor)

                for loc in neutralLocs:  # neutrals have the same shape as the distractor
                    neutralShape.pos = posList[loc]
                    neutralShape.color = targetColor
                    neutralShape.draw()

                # Second, we draw the target

                targetShape.pos = posList[targetLocation]
                targetShape.lineColor = targetColor
                targetShape.fillColor = targetColor
                targetShape.draw()

                # we need to save in the data matrix that
                # the distractor will not be on the HPDL bc there is no distractor
                # and that the distractor location is equal to 9 (aka not exists)
                is_hpdl_trial = 9
                # no distractor
                distractorLocation = 9

            # FROM HERE IT'S THE SAME FOR BOTH SCENARIOS
            # Fourth, we shuffle and draw the lines

            numpy.random.shuffle(lineOris)

            # for each of the lines, we set simultaneously the orientation and the position

            for orientation, position in zip(lineOris, posList):
                TargetStim.ori, TargetStim.pos = orientation, position

                TargetStim.draw()

            # Finally we add the fixation cross

            FixCross.draw()

            # Present everything on the screen and flip screen

            win.flip()

            responseTimer.reset()  # Correct time to reset timer!

            # Wait for a response for a maximum of 1 seconds

            keys = wait_for_keys(validKeys, max_wait=responseDeadline)

            RT = responseTimer.getTime()

            # In case no key was pressed, manually make the variable keys a list containing the string 'No response'

            if not keys:
                keys = ['No response']

            # Determine correct response

            if lineOris[targetLocation] == 45:  # If the orientation of the target line was 45 (i.e., horizontal)
                target_line_ori = 'horizontal'
                correctResponse = 'left'

            else:
                target_line_ori = 'vertical'
                correctResponse = 'up'

            # SAVE DATA OF TRIAL

            dataMatrix[trial + block * nTrials, 1] = block + 1  # BlockNr, (computers tellen vanaf 0)

            dataMatrix[trial + block * nTrials, 2] = trial + 1  # TrialNr, (computers tellen vanaf 0)

            dataMatrix[trial + block * nTrials, 3] = HPDL  # HPDL of this block

            dataMatrix[trial + block * nTrials, 4] = targetLocation  # This trial target loc

            dataMatrix[trial + block * nTrials, 5] = shape_of_target  # string 'circle' or 'diamond'

            dataMatrix[trial + block * nTrials, 6] = color_of_target  # string 'red' or 'green'

            dataMatrix[trial + block * nTrials, 7] = yesVSno_distractor[trial]  # is there a distractor present?

            dataMatrix[trial + block * nTrials, 8] = is_hpdl_trial  # is the distractor on HPDL (9 for when not present)

            dataMatrix[trial + block * nTrials, 9] = distractorLocation  # This trial distractor loc

            dataMatrix[trial + block * nTrials, 10] = target_line_ori  # string 'horizontal' or 'vertical'

            dataMatrix[trial + block * nTrials, 11] = keys[0]  # This trial key pressed

            dataMatrix[trial + block * nTrials, 12] = int(keys[0] == correctResponse)  # This trial corResp

            dataMatrix[trial + block * nTrials, 13] = round(RT * 1000)  # This trial RT

            # LOCATION + CONFIDENCE TEST (only for experiment group and specific trials (see experiment settings))
            if control_or_experiment == 1 and (trial + 1) in explicit_test_trials:

                row = trial + block * nTrials  # for datamatrix

                ## first target ##
                # location test target
                textElement.text = locationText_target  # where do you think the unique SHAPE will appear next?
                textElement.draw()
                image_locationtest.draw(win)
                win.flip()
                keys = wait_for_keys(
                    location_keys)  # keys = chosen location + 1 (humans count from 1, computers from zero)
                target_location_test = str(int(keys[0]) - 1)  # to do subtraction must be a number

                # store in datamatrix
                dataMatrix[row, 14] = float(target_location_test)

                # confidence test target
                Rating.reset()

                while Rating.getRating() is None:
                    check_for_escape()
                    textElement.text = confidenceText  # how certain are you?
                    textElement.draw()
                    Rating.draw()
                    win.flip()

                target_confidence_test = Rating.getRating()
                target_confidence_test = str(target_confidence_test)

                # store in datamatrix
                dataMatrix[row, 15] = float(target_confidence_test)

                ## second distractor ##
                # location test distractor
                textElement.text = locationText_distractor  # where do you think the unique COLOR will appear next?
                textElement.draw()
                image_locationtest.draw(win)
                win.flip()
                keys = wait_for_keys(
                    location_keys)  # keys = chosen location + 1 (humans count from 1, computers from zero)
                distractor_location_test = str(int(keys[0]) - 1)  # to do subtraction must be a number

                # store in datamatrix
                dataMatrix[row, 16] = float(distractor_location_test)

                # confidence test distractor
                Rating.reset()

                while Rating.getRating() is None:
                    check_for_escape()
                    textElement.text = confidenceText  # how certain are you?
                    textElement.draw()
                    Rating.draw()
                    win.flip()

                distractor_confidence_test = Rating.getRating()
                distractor_confidence_test = str(distractor_confidence_test)

                # store in datamatrix
                dataMatrix[row, 17] = float(distractor_confidence_test)

            ## END OF TRIAL - START NEXT TRIAL
            # Finally, remove all but the fixation cross and present ITI

            FixCross.draw()

            win.flip()

            core.wait(0.1)

        # If it is not the last block, present a break

        if block != nBlocks - 1:

            textElement.text = "This is a break"

            proceedText.draw()



        # Else announce the end

        else:

            textElement.text = "This is the end of the experiment. Thank you for participating!\n\n\nPress space to end this session."

        textElement.draw()

        win.flip()

        wait_for_keys(['space'])

    ## write data away in a csv file ##

    # def to make all the text in the csv file safe for handling in R
    def safe_col_name(name):
        # R-friendly: lowercase and only letters, numbers, underscores
        cleaned = ''.join(ch if ch.isalnum() else '_' for ch in str(name))
        return cleaned.strip('_').lower()

    # make a header for the data
    Header = ['experimental_group', 'BlockNr', 'TrialNr', 'HPDL_block', 'TargLoc', 'TargetShape', 'TargetColor',
              'DistractorPresence', 'Distractor_on_HPDL', 'DistrLoc', 'TargetLineOri',
              'Response', 'Accuracy', 'ReactionTime', 'LocTestTarget', 'ConfTestTarget',
              'LocTestDistractor', 'ConfTestDistractor']

    Header_safe = [safe_col_name(col) for col in Header]
    info_safe = {safe_col_name(key): value for key, value in info.items()}

    dataframe = pd.DataFrame(dataMatrix, columns=Header_safe)

    # Add GUI metadata as columns (repeated for each trial row)
    for key in reversed(list(info_safe.keys())):
        dataframe.insert(0, key, info_safe[key])

    # write away
    dataframe.to_csv(file_path, index=False)
    win.close()


if __name__ == "__main__":
    participant_nr, age, gender, sleep, handedness, colorblind, correct_vision, learning_dis, all_info = info_GUI()
    if (participant_nr + 1) // 2 % 2:
        RPEP_J(
            bowl_size=0.5,  # Proportional to height of screen
            save_directory=os.path.join(os.getcwd(), "RPEP_data_J", f"data_"),
            devstats=False,  # Shows statistics and saves data separately; False for data collection
            info=[participant_nr, gender, age, colorblind]
        ).main(
            fix_cross_duration=[750, 1250],  # in milliseconds, [min duration, max duration]
            feedback_duration=1.5,  # in seconds
            response_deadline=1,  # in seconds
            intertrial_interval=0.5,  # in seconds
            n_trials_per_block=160,  # Must be divisible by 8
        )
        win_between = visual.Window(fullscr=True)
        text_between = visual.TextStim(win=win_between,
                                       text="Je hebt het eerste deel afgewerkt.\nDruk op spatie om verder te gaan.\n\nYou finished the first part.\nPress space to continue.")
        text_between.draw(win=win_between)
        win_between.flip()
        event.waitKeys(keyList="space")
        win_between.close()
        LeeCode(participant_nr, all_info)
    else:
        LeeCode(participant_nr, all_info)
        win_between = visual.Window(fullscr=True)
        text_between = visual.TextStim(win=win_between, text="Je hebt het eerste deel afgewerkt.\nDruk op spatie om verder te gaan.\n\nYou finished the first part.\nPress space to continue.")
        text_between.draw(win=win_between)
        win_between.flip()
        event.waitKeys(keyList="space")
        win_between.close()
        RPEP_J(
            bowl_size=0.5,  # Proportional to height of screen
            save_directory=os.path.join(os.getcwd(), "RPEP_data_J", f"data_"),
            devstats=False,  # Shows statistics and saves data separately; False for data collection
            info=[participant_nr, gender, age, colorblind]
        ).main(
            fix_cross_duration=[750, 1250],  # in milliseconds, [min duration, max duration]
            feedback_duration=1.5,  # in seconds
            response_deadline=1,  # in seconds
            intertrial_interval=0.5,  # in seconds
            n_trials_per_block=160,  # Must be divisible by 8
        )


