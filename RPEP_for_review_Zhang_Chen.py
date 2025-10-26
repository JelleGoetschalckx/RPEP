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
def star_shape_maker(size, n_points=5) -> list:
    """
    Calculates all points of a star-shape
    :param size: Size of the star
    :param n_points: Amount of points the star has (default 5 for classic star)
    :return: list of points (in clockwise rotational order)
    """
    points = []
    for i in range(2 * n_points):
        r = size if i % 2 == 0 else size / (((1 + math.sqrt(5)) / 2) ** 2)
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
        f"{'Stimulus':20s} | {trial['color'].capitalize()} {trial['shape_name'].capitalize()}\n"
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


# _____ EXPERIMENT _____ #
class RPEP:
    def __init__(self, stim_size, save_directory, devstats):
        # Settings
        self.devstats = devstats
        self.part_nr, self.gender, self.age = info_GUI()
        self.congruent_first = not int(self.part_nr) % 2  # If even participant number: congruent block first
        self.blocks = ["congruent", "incongruent"] if self.congruent_first else ["incongruent", "congruent"]

        # Init hardware
        self.win = visual.Window(units="norm", fullscr=not self.devstats) # Fullscreen for real experiment, in-window when testing
        self.timer = core.Clock()
        self.mouse = event.Mouse(win=self.win, visible=False)

        # Stimuli
        self.all_shapes = ["triangle", "circle", "diamond", "star"]
        self.all_colors = ["purple", "blue", "yellow", "pink"]
        random.shuffle(self.all_shapes)
        random.shuffle(self.all_colors)

        self.shapes = {
            "triangle": visual.Polygon(self.win, edges=3, color="black", units="pix", size=stim_size),
            "circle": visual.Circle(self.win, color="black", units="pix", size=stim_size),
            "diamond": visual.Rect(self.win, ori=45, color="black", units="pix", size=math.sqrt((stim_size ** 2) / 2)),
            "star": visual.ShapeStim(self.win, vertices=star_shape_maker(size=stim_size / 2), units="pix")
        }
        self.fix_cross = visual.TextStim(self.win, text="+", color="black", height=0.2)
        self.message = visual.TextStim(self.win, color="white", height=0.075)
        self.feedback = visual.TextStim(self.win, height=0.2)

        # Exp handler
        self.exp_handler = data.ExperimentHandler(
            dataFileName=save_directory + ("Developer_mode" if self.devstats else "") + self.part_nr
        )

        # Questionnaire
        self.buttons = {
            "Je greep het": visual.Rect(self.win, size=(0.7, 0.15), fillColor="lightblue", lineColor="black",
                                        pos=(-0.4, 0)),
            "Je gooide het weg": visual.Rect(self.win, size=(0.7, 0.15), fillColor="lightblue", lineColor="black",
                                             pos=(0.4, 0)),
            "Je liet het liggen": visual.Rect(self.win, size=(0.7, 0.15), fillColor="lightblue", lineColor="black",
                                              pos=(-0.4, -0.3)),
            "Je vermeed het": visual.Rect(self.win, size=(0.7, 0.15), fillColor="lightblue", lineColor="black",
                                          pos=(0.4, -0.3))
        }
        self.button_message = visual.TextStim(self.win, height=0.1, color="black")

    def communication(self, text_key: str, pos: tuple = (0, 0), wait_resp=True) -> None:
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
            "early_quit": "[FORCE QUIT]\n\nPress space to continue."
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
        # All shapes and colors were randomized, get popped from list so it only gets used in one block
        go_shape_name, no_go_shape_name = self.all_shapes.pop(), self.all_shapes.pop()
        reward_color, punishment_color = self.all_colors.pop(), self.all_colors.pop()

        # Make trials
        trial_list = []
        for incentive in ["reward", "punishment"]:
            for correct_response in ["Go", "NoGo"]:
                trial_list.append(
                    {
                        "block_type": block_type,
                        "shape_name": go_shape_name if correct_response == "Go" else no_go_shape_name,
                        "correct_response": correct_response,
                        "color": reward_color if incentive == "reward" else punishment_color,
                        "incentive": incentive,
                    }
                )
        trial_list *= int(n_trials / 4)  # fewer calculations than another for-loop
        # Give every trial a random fixation cross duration (only add now, otherwise it wouldn't be fully random (see previous line))
        for trial in trial_list:
            trial["fix_cross_time"] = random.randint(fix_cross_duration[0], fix_cross_duration[1]) / 1000

        # Add to TrialHandler and ExperimentHandler
        trials = data.TrialHandler(trial_list, nReps=1, method="random")
        self.exp_handler.addLoop(trials)

        if self.devstats:
            trial_maker_devstats(trials, trial_list)

        return trials

    def trial_runner(self, trials, feedback_duration: float, response_deadline: float) -> None:
        """
        Show created trials, wait for (optional) response and store data in file
        :param trials: Trials created using self.trial_maker()
        :param feedback_duration: Time (s) during which feedback is displayed
        :param response_deadline: Time (s) to give response or to wait if inhibiting response
        :return: None
        """
        for i_trials, trial in enumerate(trials):
            # ___ STIMULI ___
            # Make stimulus (shape and color)
            shape = self.shapes[trial["shape_name"]]
            shape.color = trial["color"]

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

            # Stop experiment if "escape" was pressed (check if response is not None first)
            if response and response[0] == "escape":
                self.communication("early_quit")
                core.quit()

            # ___ FEEDBACK ___
            # Example: if correct answer and reward trial: 80% chance to get the reward, 20% to get nothing
            # Example 2: if correct answer and punishment trial: 80% chance to avoid punishment, 20% to get punishment nonetheless
            feedback_options = ["↑", "-"] if trial["incentive"] == "reward" else ["-", "↓"]
            accuracy = (response and trial["correct_response"] == "Go") or (
                        not response and trial["correct_response"] == "NoGo")
            # Correct response = 80% chance best outcome (↑ or -), wrong response = 80% chance worst outcome (- or ↓)
            distribution = [0.8, 0.2] if accuracy else [0.2, 0.8]
            feedback = numpy.random.choice(feedback_options, 1, p=distribution)

            # Display feedback for 1 second
            self.feedback.text = feedback[0]
            self.feedback.color = "green" if feedback == "↑" else "red" if feedback == "↓" else "black"
            self.feedback.draw()
            self.win.flip()
            core.wait(feedback_duration)

            # Add data to datafile
            trials.addData("incentive", trial["incentive"])  # reward/punishment
            trials.addData("block_type", trial["block_type"])  # congruent/incongruent
            trials.addData("given_response", "Go" if response else "NoGo")  # Go/NoGo
            trials.addData("accuracy", accuracy)  # 0/1
            trials.addData("given_feedback", feedback[0])  # ↑ / - / ↓
            trials.addData("correct_feedback",
                           "↑" if accuracy and trial["incentive"] == "reward" else
                           "↓" if not accuracy and trial["incentive"] == "punishment" else
                           "-")  # ↑ / - / ↓
            trials.addData("response_time", response_time if response_time <= response_deadline else None)  # float

            # General information
            trials.addData("participant_nr", self.part_nr)
            trials.addData("participant_gender", self.gender)
            trials.addData("participant_age", self.age)

            # Do a questionnaire after the last trial to check if participant understood the task
            trials.addData("valid_data", True if i_trials != len(trials.trialList) - 1 else self.questionnaire(trial["block_type"]))  # bool
                # -> entire column should be True for valid data
            self.exp_handler.nextEntry()

            # Optional: print details if devstats == True
            if self.devstats:
                trial_runner_devstats(trial, feedback, accuracy, response, feedback_options, distribution, response_time)

    def questionnaire(self, block_type) -> bool:
        """
        Starts questionnaire with 4 clickable options to check if participant understood the task
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

            self.communication("questionnaire", pos=(0, 0.4), wait_resp=False)

            # Register mouse click
            response = self.mouse_handler()
            if response:
                # Hide mouse again
                self.mouse.visible = False
                return block_type == "congruent" and response == "Je greep het" or block_type == "incongruent" and response == "Je gooide het weg"

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

    def main(self, n_trials: int, fix_cross_duration: list, feedback_duration: float, response_deadline: float) -> None:
        """
        Runs experiment
        :param n_trials: Total amount of trials (both blocks combined)
        :param fix_cross_duration: Min and Max time (ms) during which the fixation cross is displayed
        :param feedback_duration: Time during which the feedback is displayed
        :param response_deadline: Max time to give a response
        :return: None
        """
        # Divide total amount of trials by amount of blocks
        n_trials = int(n_trials / len(self.blocks))

        # Say hello
        self.communication("intro")

        # Iterate over blocks
        for i, block in enumerate(self.blocks):
            self.communication(block)
            self.communication("extra_first" if i == 0 else "extra_repeated")

            # Make trials and run through them
            trials_this_block = self.trial_maker(n_trials, fix_cross_duration, block_type=block)
            self.trial_runner(trials_this_block, feedback_duration, response_deadline)

            # Give break (except after the final block)
            if i != len(self.blocks) - 1:
                self.communication("break")
        self.communication("quit")


if __name__ == "__main__":
    RPEP(
        stim_size=300,
        save_directory=os.path.join(os.getcwd(), "RPEP_data", f"data_"),
        devstats=True # Shows statistics and saves data separately
    ).main(
        n_trials=360,  # Must be divisible by 8 (2 blocks of 4 stimuli minimum)
        fix_cross_duration=[250, 2000],  # in milliseconds, [min duration, max duration]
        feedback_duration=1,  # in seconds
        response_deadline=1  # in seconds
    )
