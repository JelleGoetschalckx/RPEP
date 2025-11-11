"""
--------------------------

Python script accompanying

    "Reversing Pavlovian Bias: Can (In)Action-Valence Associations be Modified Through Framing in a Go/NoGo Task?",

for the course Research Project Experimental Psychology at Ghent University (1st masters).

--------------------------
@author: Jelle Goetschalckx; supervisor: Prof. dr. Senne Braem

Note: works (best) in the Psychopy application or in Python 3.8 or lower
"""
import numpy
import pandas
import math
import random
import os
from psychopy import visual, data, gui, core, event
from psychopy.data import TrialHandler


# _____ FUNCTIONS _____ #
def star_shape_maker(size, n_points=5, inner_circle=2.0) -> list:
    """
    Calculates all points of a star-shape
    :param inner_circle: Ratio of inner circle
    :param size: Size of the star
    :param n_points: Amount of points the star has (default 5 for classic star)
    :return: list of points (in clockwise rotational order)
    """
    points = []
    for i in range(2 * n_points):
        r = size if i % 2 == 0 else size / (((1 + math.sqrt(5))/inner_circle) ** 2)
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
        "Leeftijd": ""
    }
    while not (info["Nummer"].isnumeric() and info["Leeftijd"].isnumeric()):
        # Only add gender here, otherwise the dropdown menu disappears when reiterating
        info["Gender"] = ["Man", "Vrouw", "X/andere"]

        # Show dialogue box
        box = gui.DlgFromDict(dictionary=info)
        if not box.OK:
            core.quit()

    return info["Nummer"], info["Gender"], info["Leeftijd"]


# For testing/debugging
def trial_runner_devstats(trial, feedback, accuracy, response, possible_feedback, distribution, response_time):
    print(
        f"{'Stimulus':20s} | {trial['color']} {trial['shape_name'].capitalize()}\n"
        f"{'Given Response':20s} | {'Go' if response else 'NoGo'}\n"
        f"{'Correct Response':20s} | {trial['correct_response']}\n",
        f"{'-> Accuracy':20s} = {int(accuracy)} (Time: {response_time if response_time <= 1 else '/'})\n\n",
        f"Given feedback: '{feedback[0]}', from options: {possible_feedback} | (Distribution: {distribution})\n",
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
    print(f"{'_' * 30}\n")


class Questionnaire:
    def __init__(self, window, main_exp):
        self.win = window
        self.main_exp = main_exp
        self.buttons = {
            "Je greep het": visual.Rect(self.win, size=(0.7, 0.15), fillColor="lightblue", lineColor=Colors.black,
                                        pos=(-0.4, 0)),
            "Je gooide het weg": visual.Rect(self.win, size=(0.7, 0.15), fillColor="lightblue", lineColor=Colors.black,
                                             pos=(0.4, 0)),
            "Je liet het liggen": visual.Rect(self.win, size=(0.7, 0.15), fillColor="lightblue", lineColor=Colors.black,
                                              pos=(-0.4, -0.3)),
            "Je vermeed het": visual.Rect(self.win, size=(0.7, 0.15), fillColor="lightblue", lineColor=Colors.black,
                                          pos=(0.4, -0.3))
        }
        self.button_message = visual.TextStim(self.win, height=0.1, color=Colors.black)
        self.mouse = event.Mouse(win=self.win, visible=False)

    def ask(self, trials, block_type) -> None:
        """
        Starts questionnaire with 4 clickable options to check if participant understood the task
        :param trials: TrialHandler type containing trials; adds True or False to "valid_data" column
        :param block_type: Congruent or incongruent to Pavlovian bias
        :return: True if correct, else False
        """
        # Show mouse
        self.mouse.visible = True

        response = None
        while not response:
            # Draw 4 buttons
            for text, button in self.buttons.items():
                button.draw()
                self.button_message.text = text
                self.button_message.pos = button.pos
                self.button_message.draw()

            self.main_exp.communication("questionnaire", pos=(0, 0.4), wait_resp=False)

            # Register mouse click
            response = self.mouse_handler()

        # Hide mouse again and add data to file
        self.mouse.visible = False
        trials.addData("valid_data", block_type == "congruent" and response == "Je greep het" or block_type == "incongruent" and response == "Je gooide het weg")

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
                    return name
            # Reset mouse appearance if not hovering any button
            self.win.winHandle.set_mouse_cursor()


class Feedback:
    def __init__(self, window, stim_size, devstats):
        """
        Feedback class calculates and shows feedback per trial
        :param window: Window to draw feedback in
        :param stim_size: Size of stimuli (and feedback) in pix
        :param devstats: Displays more information to developer if True; requires to be False for data collection
        """
        self.devstats = devstats
        self.win = window

        arrow_vertices = (
            (0, stim_size / 2),  # top
            (stim_size / 3, stim_size / 16),  # right sharp
            (stim_size / 8, stim_size / 16),  # right 90°
            (stim_size / 8, -stim_size / 2),  # right bottom
            (-stim_size / 8, -stim_size / 2),  # left bottom
            (-stim_size / 8, stim_size / 16),  # left 90°
            (-stim_size / 3, stim_size / 16)  # left 90°
        )
        self.feedback_visuals = {
            "↑": visual.ShapeStim(self.win, vertices=arrow_vertices, fillColor=Colors.green, units="pix"),
            "↓": visual.ShapeStim(self.win, vertices=arrow_vertices, fillColor=Colors.red, units="pix", ori=180),
            "-": visual.Rect(self.win, size=(0.2, 0.05), fillColor=Colors.black)
        }

    def outcome_handler(self, trial, response, response_time) -> tuple:
        """
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
        correct_feedback = (
            "↑" if accuracy and trial["incentive"] == "reward" else
            "↓" if not accuracy and trial["incentive"] == "punishment" else
            "-"
        )
        # Correct response = 80% chance best outcome (↑ or -), wrong response = 80% chance worst outcome (- or ↓)
        distribution = [0.8, 0.2] if accuracy else [0.2, 0.8]
        feedback_options = ["↑", "-"] if trial["incentive"] == "reward" else ["-", "↓"]
        given_feedback = numpy.random.choice(feedback_options, 1, p=distribution)

        # Optional: print details if devstats == True
        if self.devstats:
            trial_runner_devstats(trial, given_feedback, accuracy, response, feedback_options, distribution, response_time)

        return accuracy, correct_feedback, given_feedback

    def show(self, main_exp, trial, response, feedback, result_duration, feedback_duration):
        action_meaning = ("gegrepen" if response else "afgebleven") if trial["block_type"] == "congruent" else ("weggegooid" if response else "laten liggen")
        for time in (result_duration, feedback_duration):
            if time != result_duration:
                self.feedback_visuals[feedback[0]].draw()
            main_exp.communication(action_meaning, pos=(0, -0.5), wait_resp=False)
            core.wait(time)


# _____ EXPERIMENT _____ #
class Exp:
    def __init__(self, stim_size, save_directory, devstats):
        """
        Runs experiment and collects data
        :param stim_size: Size of stimuli in pix
        :param save_directory: Where to store acquired datafile
        :param devstats: Displays more information to developer if True; requires to be False for data collection
        """
        # Settings
        self.devstats = devstats
        self.part_nr, self.gender, self.age = info_GUI()
        # If even participant number: congruent block first
        self.blocks = ["congruent", "incongruent"] if not int(self.part_nr) % 2 else ["incongruent", "congruent"]

        # Hardware and timer
        self.win = visual.Window(units="norm", fullscr=not self.devstats) # Fullscreen for real experiment, in-window when testing
        self.timer = core.Clock()

        # Stimuli
        self.all_colors = [Colors.purple, Colors.blue, Colors.yellow, Colors.pink]
        random.shuffle(self.all_colors)

        self.shapes = {
            "4_star": visual.ShapeStim(
                self.win, vertices=star_shape_maker(n_points=4, size=stim_size / 2, inner_circle=2),
                fillColor="white", units="pix"
            ),
            "semi_circle":
                visual.Pie(
                    self.win, size=stim_size, start=-90, end=90, pos=(0, -stim_size / 2 / 2),
                    fillColor="white", units="pix",
                ),
            "rhombus":
                visual.ShapeStim(
                    self.win,
                    vertices=((0, stim_size / 2), (stim_size / 4, 0), (0, -stim_size / 2), (-stim_size / 4, 0)),
                    fillColor="white", units="pix"
                ),
            "triangle":
                visual.Polygon(
                    self.win, edges=3, size=stim_size,
                    fillColor="white", units="pix",
                ),
            "circle":
                visual.Circle(
                    self.win, size=stim_size,
                    fillColor="white", units="pix",
                ),
            "square":
                visual.Rect(
                    self.win, size=math.sqrt((stim_size ** 2) / 2),
                    fillColor="white", units="pix",
                ),
            "5_star":
                visual.ShapeStim(
                    self.win, vertices=star_shape_maker(n_points=5, size=stim_size / 2),
                    fillColor="white", units="pix",
                ),
            "3_star":
                visual.ShapeStim(
                    self.win, vertices=star_shape_maker(n_points=3, size=stim_size / 2, inner_circle=1.5), ori=180,
                    fillColor="white", units="pix",
                ),
        }
        self.shape_names = [item for item in self.shapes.keys()]  # Easier randomization
        random.shuffle(self.shape_names)

        # Text elements
        self.fix_cross = visual.TextStim(self.win, text="+", color="white", height=0.2)
        self.message = visual.TextStim(self.win, color="white", height=0.075)

        # Exp handler
        self.exp_handler = data.ExperimentHandler(
            dataFileName=save_directory + ("Developer_mode" if self.devstats else "") + self.part_nr
        )

        # Questionnaire
        self.questionnaire = Questionnaire(self.win, main_exp=self)
        self.feedback = Feedback(self.win, stim_size, devstats)

    def communication(self, text_key: str, pos: tuple=(0, 0), wait_resp=True) -> None:
        """
        Displays text messages on screen and waits for keyboard response
        :param text_key: Keyword leading to long text in options-dictionary
        :param pos: Position of text on the screen
        :param wait_resp: Waits for response if True (default)
        :return: None
        """
        options = {
            "intro": "[INTRO]",
            "congruent": "[INSTRUCTIONS ON CONGRUENT BLOCK]\n\nPress space to continue.",
            "incongruent": "[INSTRUCTIONS ON INCONGRUENT BLOCK]\n\nPress space to continue.",
            "extra_first": "[EXTRA INSTRUCTIONS BEFORE FIRST BLOCK]\n\nPress space to continue.",
            "extra_repeated": "[EXTRA INSTRUCTIONS BEFORE SECOND BLOCK]\n\nPress space to continue.",
            "break": "[BREAK]\n\nPress space to continue.",
            "questionnaire": "[QUESTIONNAIRE]\n\nWhat happened when you pressed 'space'?",
            "quit": "[QUIT]\n\nPress space to continue.",
            "early_quit": "[FORCE QUIT]\n\nPress space to continue.",
            "gegrepen": "Je greep het",
            "afgebleven": "Je bleef er af",
            "weggegooid": "Je gooide het weg",
            "laten liggen": "Je liet het liggen"
        }
        self.message.text = options[text_key]
        if pos:
            self.message.pos = pos

        self.message.draw()
        self.win.flip()

        if wait_resp:
            response = event.waitKeys(keyList=["space", "escape"])[0]
            if response == "escape":
                self.communication("early_quit")
                core.quit()

    def trial_maker(self, n_trials: int, fix_cross_duration: list, block_type: str) -> TrialHandler:
        """
        Creates n_trials amount of trials
        :param fix_cross_duration: Duration of display of the fixation cross (list of min/max)
        :param block_type: Are trials congruent or incongruent to Pavlovian bias?
        :param n_trials: Total amount of trials in 1 block
        :return: TrialHandler with generated trials
        """
        # Pop shapes and colors from stim lists (will not be reused across blocks)
        shape_names_this_block = [self.shape_names.pop() for _ in range(4)] # 4 random shapes (randomized in __init__)
        reward_color, punishment_color = self.all_colors.pop(), self.all_colors.pop()

        # Make trials
        trial_list = []
        for i, (incentive, correct_response) in enumerate(zip(["reward", "punishment"]*2, ["Go", "NoGo", "NoGo", "Go"])):
            trial_list.append(
                {
                    "block_type": block_type,
                    "shape_name": shape_names_this_block[i],
                    "correct_response": correct_response,
                    "color": reward_color if incentive == "reward" else punishment_color,
                    "incentive": incentive,
                }
            )
        trial_list *= int(n_trials / 4)
        # Give every trial a random fixation cross duration (only add now, otherwise it wouldn't be fully random (see previous line))
        for trial in trial_list:
            trial["fix_cross_time"] = random.randint(fix_cross_duration[0], fix_cross_duration[1]) / 1000

        # Add to TrialHandler and ExperimentHandler
        trials = data.TrialHandler(trial_list, nReps=1, method="random")
        self.exp_handler.addLoop(trials)

        if self.devstats:
            trial_maker_devstats(trials, trial_list)

        return trials

    def trial_runner(self, trials, feedback_duration: float, response_deadline: float, intertrial_interval: float,
                     result_duration: float) -> None:
        """
        Show created trials, wait for (optional) response and store data in file
        :param intertrial_interval: Time between feedback and next fixation cross appearing
        :param trials: Trials created using self.trial_maker()
        :param response_deadline: Time (s) to give response or to wait if inhibiting response
        :param result_duration: Time (s) where result of action is displayed
        :param feedback_duration: Time (s) during which feedback and result of action is displayed
        :return: None
        """
        for i_trials, trial in enumerate(trials):
            # ___ TRIAL ___
            # Make stimulus (shape and color)
            shape = self.shapes[trial["shape_name"]]
            shape.color = trial["color"]

            # Empty screen (intertrial interval)
            self.win.flip()
            core.wait(intertrial_interval)

            # Show fixation cross + wait
            self.fix_cross.draw()
            self.win.flip()
            core.wait(trial["fix_cross_time"])

            # Show stimulus
            shape.draw()
            self.win.flip()

            # ___ RESPONSE ___
            self.timer.reset()

            response = event.waitKeys(keyList=["space", "escape"], maxWait=response_deadline)

            response_time = self.timer.getTime()
            if response:
                # Stop experiment if "escape" was pressed (check if response is not None first)
                if response[0] == "escape":
                    self.communication("early_quit")
                    core.quit()
                shape.lineColor = Colors.black
                shape.lineWidth += 2 # All different instances of shape, so -x not necessary to reset
                shape.draw()
                self.win.flip()

            # If Go before response_deadline: keep displaying stimulus for remaining time (skips if crossed deadline (negative value))
            core.wait(response_deadline - self.timer.getTime())

            # ___ FEEDBACK AND DATA ___
            accuracy, correct_feedback, given_feedback = self.feedback.outcome_handler(trial, response, response_time)
            self.feedback.show(self, trial, response, given_feedback, result_duration, feedback_duration)

            # Add data to datafile
            trials.addData("incentive", trial["incentive"])  # reward/punishment
            trials.addData("block_type", trial["block_type"])  # congruent/incongruent
            trials.addData("given_response", "Go" if response else "NoGo")  # Go/NoGo
            trials.addData("accuracy", int(accuracy))  # 0/1
            trials.addData("given_feedback", given_feedback[0])  # ↑ / - / ↓
            trials.addData("correct_feedback", correct_feedback[0])  # ↑ / - / ↓
            trials.addData("response_time", response_time if response_time <= response_deadline else None)  # float

            # General information
            trials.addData("participant_nr", self.part_nr)
            trials.addData("participant_gender", self.gender)
            trials.addData("participant_age", self.age)
            if i_trials:
                # Filler, only matters for questionnaire on first trial
                # -> entire column should be True for valid data
                trials.addData("valid_data", True)
            self.exp_handler.nextEntry()

    def main(self, n_trials_per_block: int, fix_cross_duration: list, feedback_duration: float, response_deadline: float,
             intertrial_interval: float, result_duration: float) -> None:
        """
        Runs experiment
        :param intertrial_interval: Time between feedback and next fixation cross appearing
        :param n_trials_per_block: Total amount of trials per block
        :param fix_cross_duration: Min and Max time (ms) during which the fixation cross is displayed
        :param feedback_duration: Time during which the feedback is displayed
        :param response_deadline: Max time to give a response
        :param result_duration: Time between stimulus and feedback
        :return: None
        """
        # Say hello
        self.communication("intro")

        # Iterate over blocks
        for i, block_type in enumerate(self.blocks):
            self.communication(block_type)
            self.communication("extra_first" if i == 0 else "extra_repeated")

            # Make trials, check if participant read instructions well and run through trials
            trials_this_block = self.trial_maker(n_trials_per_block, fix_cross_duration, block_type=block_type)
            self.questionnaire.ask(trials_this_block, block_type)
            self.trial_runner(trials_this_block, feedback_duration, response_deadline, intertrial_interval,
                              result_duration)

            # Give break (except after the final block)
            if i != len(self.blocks) - 1:
                self.communication("break")
        self.communication("quit")


class Colors:  # taken from https://www.psychopy.org/_modules/psychopy/colors.html
    black = (-1, -1, -1)
    red = (1, -1, -1)
    green = (-1, 0.00392156862745097, -1)
    purple = (0.00392156862745097, -1, 0.00392156862745097)
    blue = (-1, -1, 1)
    yellow = (1, 1, -1)
    pink = (1, -0.176470588235294, 0.411764705882353)


if __name__ == "__main__":
    Exp(
        stim_size=300,  # In pix
        save_directory=os.path.join(os.getcwd(), "RPEP_data", f"data_"),
        devstats=False  # Shows statistics and saves data separately; False for data collection
    ).main(
        n_trials_per_block=180,  # Must be divisible by 4
        fix_cross_duration=[750, 1250],  # in milliseconds, [min duration, max duration]
        feedback_duration=1.5,  # in seconds
        response_deadline=1,  # in seconds
        intertrial_interval=1,  # in seconds
        result_duration=0.5  # in seconds
    )

