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
    info = {
        "Nummer": "",
        "Leeftijd": "",
    }
    while not (info["Nummer"].isnumeric() and info["Leeftijd"].isnumeric()):
        # Only add gender and colorblindness here, otherwise the dropdown menu disappears when reiterating
        info["Gender"] = ["Man", "Vrouw", "X/andere", "Zeg ik liever niet"]
        info["Leidt u aan kleurenblindheid?"] = ["Ja", "Nee"]

        # Show dialogue box
        box = gui.DlgFromDict(dictionary=info, title="Experiment")
        if not box.OK:
            core.quit()

    return info["Nummer"], info["Gender"], info["Leeftijd"], info["Leidt u aan kleurenblindheid?"]


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
            # Reset mouse appearance if not hovering any button
            self.win.winHandle.set_mouse_cursor()


# _____ EXPERIMENT _____ #
class Exp:
    def __init__(self, bowl_size, save_directory, devstats):
        """
        Runs experiment and collects data
        :param bowl_size: Size of stimuli in proportion to screen height
        :param save_directory: Where to store acquired datafile
        :param devstats: Displays more information to developer if True; requires to be False for data collection
        """
        # Settings
        self.devstats = devstats
        self.part_nr, self.gender, self.age, self.color_blind = info_GUI()
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
        self.bowl_go_visualisation = visual.Circle(self.win, color="black", size=self.bowl_size + 20, units="pix")
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
            dataFileName=save_directory + ("Developer_mode" if self.devstats else "") + self.part_nr
        )
        self.total_score = 0
        self.n_correct_trials = 0

    def communication(self, text_key: str, n_block: int=-1, shapes: tuple=None, colors: tuple=None, extra_info=None, pos: tuple=(0, 0),
                      wait_resp=True, color="white", size=0.075, flip=True, block_type="", n_trials=-1) -> None:
        """
        Displays text messages on screen and waits for keyboard response
        :param n_trials:
        :param block_type: Congruent or incongruent
        :param extra_info: Extra info to add to text
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
            go_shape = nogo_shape = "d"


        options = {
            "intro": f"Welkom!\nIn dit experiment werk je in een restaurant dat gespecialiseerd "
                     f"is in abstracte soep. Je manager kijkt nauwlettend toe en geeft je bonussen of boetes afhankelijk "
                     f"van je prestaties.\n\n"
                     f"Druk op spatie voor meer uitleg.",
            "general": f"Zodra krijg je{' opnieuw ' if n_block else ' '}verschillende borden met soep achter elkaar "
                       f"gepresenteerd{', maar vandaag serveren we andere kleuren soep.' if n_block else '.'}\n\n"
                       f"Omdat {punish_color} soep erg duur is om te maken, zal de manager je bij deze soep standaard bestraffen, maar zwaarder als je een fout maakt "
                       f"(-€1 als je correct handelt, of -€10 als je een fout maakt).\n\n{reward_color.capitalize()} soep "
                       f"is veel goedkoper, dus hij zal je hierbij altijd belonen, maar meer als je juist handelt (+€10 als je correct handelt, of +€1 als je een fout maakt).\n\n"
                       f"Wanneer je de soep te zien krijgt, is hij nog niet helemaal afgewerkt. Je moet eerst even wachten "
                       f"tot er figuren op de soep gestrooid worden, dan pas is hij klaar om geserveerd te worden.\n\n"
                       f"Druk op spatie voor meer informatie.",
            "congruent": f"Het is jouw taak om de mensen te bedienen die soep met {go_shape} hebben besteld, de soep met "
                         f"{nogo_shape} moet je laten staan voor je collega's. Als je de soep wilt meenemen, moet je zo "
                         f"snel mogelijk reageren, voor één van je collega's er mee weg is.\n\nJe neemt de soep met {go_shape} mee "
                         f"door op spatie te drukken en je laat hem staan door niets te doen.\n\n"
                         f"Druk op spatie voor een korte samenvatting.",
            "incongruent": f"Vandaag bestelden de gasten alleen maar soep met {nogo_shape}! Helaas is de verantwoordelijke "
                           f"voor de figuren vandaag een jobstudent, die vaak per ongeluk toch {go_shape} op de soep doet.\n\n"
                           f"Daarom heeft de manager je de taak gegeven om elke keer dat de jobstudent {go_shape} in de "
                           f"soep doet, de soep zo snel mogelijk in de vuilnisbak te werpen. De soep met {nogo_shape} wordt geserveerd "
                           f"door je collega's, deze moet je dus laten staan. Je gooit de soep weg door op de spatiebalk "
                           f"te duwen en je laat hem staan door niets te doen.\n\n"
                           f"Druk op spatie voor een korte samenvatting.",
            "overview": f"Kortom:\n\n\n"
                        f"{reward_color.upper()} soep → Manager BELOONT je, +10 als correct, +1 als fout\n\n"
                        f"{punish_color.upper()} soep → Manager STRAFT je, -1 als correct, -10 als fout\n\n"
                        f"-----------------\n\n"
                        f"{go_shape.upper()} in de soep → Deze moet je SNEL {'MEENEMEN' if block_type == 'congruent' else 'WEGGOOIEN'} (spatie)\n\n"
                        f"{nogo_shape.upper()} in de soep → Deze moet je LATEN STAAN (niets doen)\n\n\nJe dagloon (in dit experiment) is afhankelijk van je prestatie, je begint op 0.\n"
                        f"Druk op spatie om verder te gaan.",
            "questionnaire_intro": "Voor de taak begint, krijg je eerst drie korte vragen (zonder tijdslimiet) om te checken of "
                                   "je de taak goed begrepen hebt.\n\n"
                                   "Druk op spatie om naar de eerste vraag te gaan.",
            "question1": "Bij welke soep zal je baas je straffen als je een fout maakt?\n(Klik op het juiste antwoord)",
            "question2": f"Welke soep moet jij {'meenemen' if block_type == 'congruent' else 'weggooien'}?\n(Klik op het juiste antwoord)",
            "question3": f"Wat zal er gebeuren als je reageert (door op spatie te drukken)?\n(Klik op het juiste antwoord)",
            "question_wrong": "Niet al je antwoorden waren correct.\n\nDruk op spatie om terug te keren naar de instructies.",
            "start_trials": f"Zeer goed! Je krijgt {'nu' if not n_block else 'net zoals daarnet'} de soepborden één voor "
                            f"één gepresenteerd. Denk er aan dat je maar weinig tijd hebt om een keuze te maken, wees dus zo snel mogelijk als je op spatie wilt duwen!\n\n"
                            f"Druk op spatie als je klaar bent om te beginnen.",
            "break": "Tijd voor een pauze. Wanneer je klaar bent om verder te gaan, druk je op spatie voor meer instructies.",
            "end": f"Je hebt het einde van dit experiment bereikt, bedankt om deel te nemen!\n\n"
                    f"Je maakte in totaal {self.n_correct_trials} van de {n_trials} keer een juiste keuze ({self.n_correct_trials/n_trials*100}%). Daar behaal je een eindeloon mee van €{self.total_score}!\n\n"
                    f"Druk op spatie om af te sluiten.",
            "early_quit": "Experiment werd afgesloten met escape.",
            "grabbed": f"{extra_info}\nJe nam de soep mee",
            "thrown away": f"{extra_info}\nJe gooide de soep weg",
            "did nothing": f"{extra_info}\nJe liet de soep staan",
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
            self.draw_stimuli(trial, garnish=True)

            # ___ RESPONSE ___
            self.timer.reset()

            response = event.waitKeys(keyList=["space", "escape"], maxWait=response_deadline)

            response_time = self.timer.getTime()
            if response:
                # Stop experiment if "escape" was pressed (check if response is not None first)
                if response[0] == "escape":
                    self.communication("early_quit")
                    core.quit()
                self.draw_stimuli(trial, garnish=True, bowl_action=True)

            # If Go before response_deadline: keep displaying stimulus for remaining time (skips if crossed deadline (negative value))
            core.wait(response_deadline - self.timer.getTime())

            # ___ FEEDBACK AND DATA ___
            accuracy, feedback_points, feedback_text = self.outcome_handler(trial, response, response_time)
            self.communication(feedback_points, wait_resp=False, size=0.5, flip=False)
            self.communication(feedback_text, extra_info="Correct!" if accuracy else "Fout!", wait_resp=False, pos=(0, -0.5,))
            core.wait(feedback_duration)

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
            trials.addData("colorblind", 1 if self.color_blind == "Ja" else 0)
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
                self.communication(text_key=block_type, shapes=shapes, colors=colors)
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

if __name__ == "__main__":
    Exp(
        bowl_size=0.5,  # Proportional to height of screen
        save_directory=os.path.join(os.getcwd(), "RPEP_data", f"data_"),
        devstats=False  # Shows statistics and saves data separately; False for data collection
    ).main(
        fix_cross_duration=[750, 1250],  # in milliseconds, [min duration, max duration]
        feedback_duration=1.5,  # in seconds
        response_deadline=1,  # in seconds
        intertrial_interval=0.5,  # in seconds
        n_trials_per_block=160,  # Must be divisible by 8
    )
