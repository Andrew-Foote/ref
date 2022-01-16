from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, Optional, TypeVar, Union

class UnificationError(ValueError):
    pass

FunSymT = TypeVar('FunSymT')
VarT = TypeVar('VarT')
AppT = TypeVar('AppT')
TermT = Union[VarT, AppT] # should be able to write VarT | AppT, but there's a
                          # bug in mypy

class Unifier(ABC, Generic[FunSymT, VarT, AppT]):
    """An interface for the unification algorithm.

    An implementation of this interface is basically the same as that which is
    called a 'term algebra' in mathematics.

    Definitions:
    - A function symbol is a value of 'FunSymT'.
    - A variable is a value of 'VarT'.
    - A (formal) application is a value of 'AppT'.
    - A term is a value of 'TermT', i.e. a variable or an application.

    The following conditions should be satisfied for any implementation 'cls',
    but are not enforced:

    - For every function symbol f and every sequence s of terms, we have    
      cls.fun_sym(self.apply(f, s)) == f and cls.args(self.apply(f, s)) == s.

    - For any two applications t and u:
    
      - If cls.fun_sym(t) == cls.fun_sym(u), then
        len(cls.args(t)) == len(cls.args(u)).

      - t == u if and only if cls.fun_sym(t) == cls.fun_sym(u) and
        all(larg == rarg for larg, rarg in zip(cls.args(t), cls.args(u)).
    """
    @classmethod
    @abstractmethod
    def apply(cls, f: FunSymT, args: Sequence[TermT]) -> AppT:
        """Return the formal application of 'f' to 'args'."""

    @classmethod
    @abstractmethod
    def is_var(cls, term: TermT) -> bool:
        """Return whether 'term' is a variable."""
        # if there was a way to tell the type checker how to use this, we could
        # do away with VarT

    @classmethod
    @abstractmethod
    def fun_sym(cls, app: AppT) -> FunSymT:
        """Return the function symbol 'app' is an application of."""

    @classmethod
    @abstractmethod
    def args(cls, app: AppT) -> Sequence[TermT]:
        """Return the arguments 'app' is an application to."""

    @classmethod
    def occurs_in(cls, var: VarT, term: TermT) -> bool:
        """Return whether 'var' occurs in 'term'."""
        if cls.is_var(term):
            return var == term

        return any(cls.occurs_in(var, arg) for arg in cls.args(term))

    @classmethod
    def subst(cls, s: dict[VarT, TermT], term: TermT) -> TermT:
        """Return the image of 'term' under the substitution map induced by 's'.
        """
        if cls.is_var(term):
            return s.get(term, term)

        return cls.apply(
            cls.fun_sym(term),
            tuple(cls.subst(s, arg) for arg in cls.args(term))
        )

    @classmethod
    def unify(
        cls,
        equations: list[tuple[TermT, TermT]],
        subst: Optional[dict[VarT, TermT]]=None
    ) -> dict[VarT, TermT]:
        """Return the most general unifier of 'equations'.

        If 'subst' is not None, returns the most general unifier that
        specializes 'subst'.

        The equations should be encoded as 2-tuples."""
        if subst is None:
            subst = {}

        while equations:
            left, right = equations.pop()

            if left == right:
                continue

            if cls.is_var(left):
                if cls.occurs_in(left, right):
                    raise UnificationError(f'{left} occurs in {right}')

                new_subst = {left: right}

                for i, (l, r) in enumerate(equations):
                    equations[i] = (
                        cls.subst(new_subst, l),
                        cls.subst(new_subst, r)
                    )

                for var, term in subst.items():
                    subst[var] = cls.subst(new_subst, term)

                subst |= new_subst
                continue

            if cls.is_var(right):
                equations.append((right, left))
                continue

            f = cls.fun_sym(left)
            g = cls.fun_sym(right)
            
            if f != g:
                raise UnificationError(
                    f'cannot unify applications of {f} and {g}'
                )

            for larg, rarg in zip(cls.args(left), cls.args(right)):
                equations.append((larg, rarg))

        return subst

    @classmethod     
    def unify2(
        cls,
        left: TermT,
        right: TermT,
        subst: Optional[dict[VarT, TermT]]=None
    ) -> dict[VarT, TermT]:
        """Return the most general unifier of the equation 'left' = 'right'.

        For unifying multiple equations see 'cls.unify'.

        >>> unify2(('f', 'x', 'y'), ('f', 'y', 'x'))
        {'y': 'x'}
        >>> unify2(('f', 'x', ('g', 'y', 'z')), ('f', 'y', 'x'))
        Traceback (most recent call last):
          ...
        UnificationError: y occurs in ('g', 'y', 'z')
        >>> unify2(('f', 'x', ('g', 'y', 'z')), ('f', 'x', 'w'))
        {'w': ('g', 'y', 'z')}
        >>> unify2(('f', 'x', ('g', 'y', 'z')), ('f', 'x', ('h', 'w')))
        Traceback (most recent call last):
          ...
        UnificationError: cannot unify applications of g and h
        """
        return cls.unify([(left, right)], subst)

class GeneralUnifier(Unifier[FunSymT, VarT, tuple[FunSymT, ...]]):
    """A concrete unifier with convenient defaults.

    For this unifier, the application of a function symbol 'f' to arguments
    'args' is encoded as (f, *args), and anything which is not a tuple is
    treated as a variable at run-time (though you can still instantiate the
    VarT type parameter with whatever type you want).
    """
    @classmethod
    def apply(cls, f, args):
        return (f, *args)

    @classmethod
    def is_var(cls, term):
        return not isinstance(term, tuple)

    @classmethod
    def fun_sym(cls, term):
        return term[0]

    @classmethod
    def args(cls, term):
        return term[1:]

unify = GeneralUnifier.unify
unify2 = GeneralUnifier.unify2

if __name__ == '__main__':
    import doctest
    doctest.testmod()
