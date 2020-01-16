"""
Quiz utils
"""

from .display import Printer
from .shell import SequelShell
from ..sequence import Sequence, compile_sequence, generate_sequences



class Quiz(object):
    def __init__(self, sequence, *, num_known_items=10, num_correct_guesses=3, printer=None):
        self.__num_known_items = num_known_items
        self.__num_correct_guesses = num_correct_guesses
        self.__sequence = Sequence.make_sequence(sequence)
        self.__items = list(self.__sequence.get_values(self.__num_known_items))
        self.__guessed_indices = set()
        if printer is None:
            printer = Printer()
        self._printer = printer

    def check_guess(self, item):
        items = self.__items
        index = len(items)
        ref_item = self.__sequence(index)
        if ref_item == item:
            items.append(ref_item)
            self.__num_known_items += 1
            self.__num_correct_guesses -= 1
            self.__guessed_indices.add(index)
            return True
        else:
            return False

    def new_item(self):
        items = self.__items
        self.__items.append(self.__sequence(len(items)))
        self.__num_known_items += 1

    def is_solution(self, sequence):
        ref = self.__sequence
        seq = Sequence.make_sequence(sequence)
        ref_items = [int(x) for x in self.__items]
        seq_items = [int(x) for x in seq.get_values(len(ref_items))]
        return seq_items == ref_items

    def is_exact_solution(self, sequence):
        ref = self.__sequence
        seq = Sequence.make_sequence(sequence)
        return seq.equals(ref)

    @property
    def items(self):
        return tuple(self.__items)

    @property
    def num_known_items(self):
        return self.__num_known_items

    @property
    def num_correct_guesses(self):
        return self.__num_correct_guesses

    @property
    def guessed_indices(self):
        return frozenset(self.__guessed_indices)


class QuizShell(SequelShell):
    def __init__(self, printer=None, num_known_items=10, num_correct_guesses=3, sequence_iterator=None, max_games=None):
        self.num_known_items = num_known_items
        self.num_correct_guesses = num_correct_guesses
        if sequence_iterator is None:
            sequence_iterator = generate_sequences()
        self.sequence_iterator = iter(sequence_iterator)
        self.quiz = None
        self.sequence = None
        self.max_games = max_games
        self.played_games = 0
        locals = {}
        locals['q'] = self.get_quiz
        locals['show'] = self.show
        locals['solve'] = self.solve
        locals['guess'] = self.guess
        locals['spoiler'] = self.spoiler
        locals['restart'] = self.restart
        locals['hint'] = self.hint
        super().__init__(locals=locals, printer=printer)
        self._restart()

    def banner(self):
        return """\
Sequel quiz
"""

    def get_quiz(self):
        return self.quiz

    def interact(self):
        self.run_commands(["show()"], echo=False)
        super().interact(banner="")

    def _restart(self):
        self.sequence = next(self.sequence_iterator)
        self.quiz = Quiz(self.sequence, num_known_items=self.num_known_items, num_correct_guesses=self.num_correct_guesses, printer=self.printer)
        self.played_games += 1

    def autorestart(self):
        if self.max_games is None or self.max_games > self.played_games:
            self.restart()

    def restart(self):
        self._restart()
        self.show()

    def hint(self):
        self.quiz.new_item()
        self.show()

    def spoiler(self):
        return self.sequence

    def show(self):
        printer = self.printer
        quiz = self.quiz
        items = quiz.items
        all_items = [printer.repr_item(item) for item in items]
        all_items.extend(printer.red("?") for _ in range(quiz.num_known_items + quiz.num_correct_guesses - len(items)))
        item_format = "    {index:4d}: {item:20s}"
        guessed_indices = quiz.guessed_indices
        printer("Find the hidden sequence producing these items:")
        for index, item in enumerate(all_items):
            if index in guessed_indices:
                item = printer.blue(item)
            else:
                item = printer.bold(item)
            printer(item_format.format(index=index, item=item))
        
    def guess(self, item):
        printer = self.printer
        quiz = self.quiz
        if quiz.check_guess(item):
            printer("Good, you correctly guessed a new sequence item")
            self.show()
            missing = quiz.num_correct_guesses
            if missing == 0:
                printer("You won! The sequence was {}".format(printer.bold(self.sequence)))
                self.autorestart()
            else:
                if missing == 1:
                    pl = ''
                else:
                    pl = 's'
                printer("Guess {} more item{} to win!".format(missing, pl))
        else:
            printer("Mmmh... {} is not the next sequence item".format(item))

    def solve(self, sequence):
        printer = self.printer
        quiz = self.quiz
        ref = self.sequence
        seq = Sequence.make_sequence(sequence)
        if quiz.is_solution(seq):
            if quiz.is_exact_solution(seq):
                printer("Wow! You found the exact solution {}".format(printer.bold(str(ref))))
            else:
                printer("Good! You found the solution {}; the exact solution was {}".format(printer.bold(str(seq)), printer.bold(str(ref))))
            self.autorestart()
        else:
            printer("No, {} is not the solution".format(printer.bold(str(seq))))
