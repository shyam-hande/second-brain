# Python Tips I Keep Forgetting

## List comprehensions are faster than loops
Use `[x*2 for x in range(10)]` instead of a for loop when building lists.

## Virtual environments
Always use `python -m venv venv` not `virtualenv` for consistency.

## f-strings are the best
Use f-strings: `f"Hello {name}"` instead of `.format()`.

## Walrus operator
The `:=` operator assigns and returns a value in one step.
Example: `if n := len(data): print(n)`