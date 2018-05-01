Sequel
======

Sequel is a command line tool to find integer sequences:

::

  $ sequel search 2 3 5 7 11
      0] p
      2 3 5 7 11 13 17 19 23 29 ...

  $ sequel search 2 3 5 7 13 17
      0] m_exp
      2 3 5 7 13 17 19 31 61 89 ...

The ``search`` subcommand accepts an arbitrary number of integer values and returns a list of matching sequences:

::

  $ sequel search 2 3 5 7
      0] p
      2 3 5 7 11 13 17 19 23 29 ...
      1] m_exp
      2 3 5 7 13 17 19 31 61 89 ...

Sequel can also find complex sequences:

::

  $ sequel search 10 15 25 35 71 97 101 191 419 625
      0] -3 * p + 8 * m_exp
      10 15 25 35 71 97 101 191 419 625 ...

The ``doc`` command shows documentation about known sequences. Without arguments all known sequences are shown.

::

    $ sequel doc m_exp p
    m_exp : f(n) := the n-th Mersenne exponent
        2 3 5 7 13 17 19 31 61 89 ...
    
    p : f(n) := the n-th prime number
        2 3 5 7 11 13 17 19 23 29 ...

The ``test`` subcommand can be used to create a sequence and search its items:

::

  $ sequel test 'p * zero_one'
  ### compiling p * zero_one ...
  p * zero_one
      0 3 0 7 0 13 0 19 0 29 ...
  ### searching 0 3 0 7 0 13 0 19 0 29 ...
      0] [*] zero_one * p
  sequence p * zero_one: found

  $ sequel test 'p - 7 * fib01'
  ### compiling p - 7 * fib01 ...
  p - 7 * fib01
      2 -4 -2 -7 -10 -22 -39 -72 -124 -209 ...
  ### searching 2 -4 -2 -7 -10 -22 -39 -72 -124 -209 ...
      0] [*] -7 * fib01 + p
  sequence p - 7 * fib01: found

  $ sequel test 'm_exp -5 * p+ fib01'
  ### compiling m_exp -5 * p+ fib01 ...
  m_exp - 5 * p + fib01
      -8 -11 -19 -26 -39 -43 -58 -51 -33 -22 ...
  ### searching -8 -11 -19 -26 -39 -43 -58 -51 -33 -22 ...
      0] [*] fib01 + -5 * p + m_exp
  sequence m_exp - 5 * p + fib01: found

Requirements
------------

Sequel requires

 * ``python>=3.5``
 * ``gmpy2``
 * ``sympy``
 * ``astor``
 * ``termcolor``
