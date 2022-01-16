from __future__ import annotations
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from unify import Unifier as _Unifier
from typing import Any, ClassVar, Literal, Optional

BuiltinTypedTerm = str | tuple[Any, ...]
#BuiltinTypedTerm = str | tuple[BuiltinTypedTerm, ...]

class Term(ABC):
	"""A term in a combinator calculus.

	>>> str(App(PrimComb.S, App(PrimComb.K, PrimComb.S)))
	'S(KS)'
	>>> str(App(App(PrimComb.S, PrimComb.K), PrimComb.K))
	'SKK'
	>>> str(App(Var("x"), Var("x'")))
	"x<x'>"
	"""

@dataclass
class Var(Term):
	"""A variable in a combinator calculus."""
	name: str

	def __str__(self):
		return self.name if len(self.name) == 1 else f'<{self.name}>'

@dataclass
class PrimComb(Term):
	"""A primitive combinator in a combinator calculus."""
	S: ClassVar[PrimComb] 
	K: ClassVar[PrimComb]
	name: str

	def __str__(self):
		return self.name

PrimComb.S = PrimComb('S')
PrimComb.K = PrimComb('K')

@dataclass
class App(Term):
	"""The application of one term to another in a combinator calculus."""
	left: Term
	right: Term

	def __str__(self):
		right_str = str(self.right)

		if isinstance(self.right, App):
			right_str = f'({right_str})'

		return f'{self.left}{right_str}'

def parse_term(src: str, i0: int) -> tuple[Term, int]:
	i: int = i0
	acc: Optional[Term] = None

	def acc_append(acc, t):
		return t if acc is None else App(acc, t)

	while i < len(src):
		char = src[i]

		if char in 'SK':
			acc = acc_append(acc, PrimComb(char))
			i += 1
		elif char == '(':
			term, i = parse_term(src, i + 1)
			acc = acc_append(acc, term)
		elif char == ')':
			i += 1
			break
		else:
			raise ValueError(f'invalid character at index {i}')

	else: # if we terminate by reaching the end of the string rather than
		  # hitting a closing bracket

		if i0 != 0:
			raise ValueError(f'opening bracket at index {i0 - 1} not closed')

	if acc is None:
		raise ValueError(f'the empty string cannot be parsed as a term')

	return acc, i

def parse(src: str) -> Term:
	"""
	>>> parse('SKK')
	App(left=App(left=PrimComb(name='S'), right=PrimComb(name='K')), right=PrimComb(name='K'))
	"""
	term, i = parse_term(src, 0)

	if i != len(src):
		raise ValueError(f'extraneous closing bracket at index {i - 1}')

	return term

def reduce1(term: Term) -> Optional[Term]:
	if isinstance(term, (Var, PrimComb)):
		return term

	# sadly mypy does not yet support the match statement so we have to make do
	# with this monstrosity
	if isinstance(term, App):
		if isinstance(term.left, App):
			if isinstance(term.left.left, App):
				if term.left.left.left == PrimComb.S:
					return App(
						App(term.left.left.right, term.right),
						App(term.left.right, term.right)
					)
			
			if term.left.left == PrimComb.K:
				return term.left.right

		left_reduced = reduce1(term.left)

		if left_reduced is None:
			right_reduced = reduce1(term.right)

			if right_reduced is None:
				return None

			return App(term.left, right_reduced)

		return App(left_reduced, term.right)

	raise ValueError(f'{term} is not a term')

def reduce(term: Term) -> Term:
	while True:
		reduced = reduce1(term)

		if reduced is None:
			return term

		term = reduced

class FunSym(Enum):
	S = PrimComb.S
	K = PrimComb.K
	App = App

class Unifier(_Unifier[FunSym, Var, App]):
	@classmethod
	def apply(cls, f, args):
		if isinstance(f, PrimComb):
			return f

		if f == App and len(args) == 2:
			return App(*args)

		raise ValueError(f'cannot apply {f} to {args}')

	@classmethod
	def is_var(cls, term):
		return isinstance(term, Var)

	@classmethod
	def fun_sym(cls, term):
		if isinstance(term, PrimComb):
			return term

		if isinstance(term, App):
			return App

		raise ValueError(f'{term} is not an application')

	@classmethod
	def args(cls, term):
		if isinstance(term, PrimComb):
			return ()

		if isinstance(term, App):
			return (term.left, term.right)

		raise ValueError(f'{term} is not an application')

unify = Unifier.unify
unify2 = Unifier.unify2

if __name__ == '__main__':
	import doctest
	doctest.testmod()