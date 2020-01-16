"""
Quiz utils
"""

import types

from .display import Printer
from .shell import SequelShell
from ..sequence import Sequence, compile_sequence, generate_sequences



class QuizGame(object):
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


class Cmd(object):
    def __init__(self, function):
        self.function = function

    # def __repr__(self):
    #     self()

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    @property
    def name(self):
        return self.function.__name__

    def doc(self):
        return self.function.__doc__


class Quiz(object):
    def __init__(self, printer=None, num_known_items=10, num_correct_guesses=3, sequence_iterator=None, max_games=None):
        if printer is None:
            printer = Printer()
        self.__printer = printer
        self.__num_known_items = num_known_items
        self.__num_correct_guesses = num_correct_guesses
        if sequence_iterator is None:
            sequence_iterator = generate_sequences()
        self.__sequence_iterator = iter(sequence_iterator)
        self.__game = None
        self.__sequence = None
        self.__sequence_shown = False
        self.__max_games = max_games
        self.__played_games = 0
        self.__docs = []
        for method in (self.help, self.show, self.solve, self.guess, self.hint, self.spoiler, self.new):
            method_name = method.__name__
            method_doc = method.__doc__
            if method_doc is None:
                method_doc = method_name
            self.__docs.append((method_name, method_doc))
        self.__restart()

    def __restart(self):
        self.__sequence = next(self.__sequence_iterator)
        self.__sequence_shown = False
        self.__game = QuizGame(self.__sequence, num_known_items=self.__num_known_items, num_correct_guesses=self.__num_correct_guesses, printer=self.__printer)
        self.__played_games += 1

    def __autorestart(self):
        if self.__max_games is None or self.__max_games > self.__played_games:
            self.new()

    def help(self):
        """show help"""
        printer(self.__help())

    def __help(self):
        printer = self.__printer
        lines = []
        lines.append("""\
Look at the items and try to find the hidden sequence.

If you guess the sequence, try to solve the game with the command q.solve(); for instance:

  >>> q.solve(lucas)

You can also try to guess the next item, for instance:

  >>> q.solve(11)
  >>> q.solve(p(5))

If you need to see more items, you can run the q.hint() command; a new item will be added.

If you cannot guess the sequence, you can start a new game:

  >>> q.new()

Available commands are:
""")
        for method_name, method_doc in self.__docs:
            lines.append("  {} {}".format(printer.bold("{:10s}".format(method_name)), method_doc))
        return '\n'.join(lines)

    def new(self):
        """Restart the game"""
        if self.__sequence is not None:
            printer = self.__printer
            printer("The sequence was {}".format(printer.bold(self.__sequence)))
        self.__restart()
        self.show()

    def hint(self):
        """Add a sequence item"""
        self.__game.new_item()
        self.show()

    def spoiler(self):
        """Show the hidden sequence"""
        return self.__sequence

    def show(self):
        """Show the sequence items"""
        printer = self.__printer
        if not self.__sequence_shown:
            printer("===============================================")
            printer("Find the hidden sequence producing these items:")
            printer("===============================================")
            self.__sequence_shown = True
        game = self.__game
        items = game.items
        all_items = [printer.repr_item(item) for item in items]
        all_items.extend(printer.red("?") for _ in range(game.num_known_items + game.num_correct_guesses - len(items)))
        item_format = "    {index:4d}: {item:20s}"
        guessed_indices = game.guessed_indices
        for index, item in enumerate(all_items):
            if index in guessed_indices:
                item = printer.blue(item)
            else:
                item = printer.bold(item)
            printer(item_format.format(index=index, item=item))
        
    def guess(self, item):
        """Try to guess the next sequence item"""
        printer = self.__printer
        game = self.__game
        if game.check_guess(item):
            printer("Good, you correctly guessed a new sequence item")
            self.show()
            missing = game.num_correct_guesses
            if missing == 0:
                printer("You won! The sequence was {}".format(printer.bold(self.__sequence)))
                self.__autorestart()
            elif missing > 0:
                if missing == 1:
                    pl = ''
                else:
                    pl = 's'
                printer("Guess {} more item{} to win!".format(missing, pl))
        else:
            printer("Mmmh... {} is not the next sequence item".format(item))

    def solve(self, sequence):
        """Try to solve the game by providing a matching sequence"""
        printer = self.__printer
        game = self.__game
        ref = self.__sequence
        seq = Sequence.make_sequence(sequence)
        if game.is_solution(seq):
            if game.is_exact_solution(seq):
                printer("Wow! You found the exact solution {}".format(printer.bold(str(ref))))
            else:
                printer("Good! You found the solution {}; the exact solution was {}".format(printer.bold(str(seq)), printer.bold(str(ref))))
            self.__autorestart()
        else:
            printer("No, {} is not the solution".format(printer.bold(str(seq))))

    def __call__(self):
        self.show()

    def __repr__(self):
        return self.__help()


class QuizShell(SequelShell):
    def __init__(self, printer=None, num_known_items=10, num_correct_guesses=3, sequence_iterator=None, max_games=None):
        if printer is None:
            printer = Printer()
        self.quiz = Quiz(printer=printer, num_known_items=num_known_items, num_correct_guesses=num_correct_guesses,
                         sequence_iterator=sequence_iterator, max_games=max_games)
        super().__init__(locals={'q': self.quiz}, printer=printer)

    def banner(self):
        return """\
Sequel quiz - try to find the hidden sequence.
The 'q' instance is the quiz; run 'q' for help.
"""

    def interact(self):
        self.run_commands(["q.show()"], echo=False)
        super().interact(banner="")

