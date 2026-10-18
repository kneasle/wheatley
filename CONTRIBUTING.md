# Contributing

**First**: if you're unsure or afraid of _anything_, just ask or submit the issue or pull request
anyway.  You won't be yelled at for giving it your best effort.  The worst that can happen is that
you'll be politely asked to change something.  We appreciate any sort of contributions, and don't
want a wall of rules to get in the way of that.

If you're new to the code, a high-level description of Wheatley's internal architecture can be found
in [ARCHITECTURE.md](https://github.com/kneasle/wheatley/blob/main/ARCHITECTURE.md).

## Getting Started

- Download [uv](https://docs.astral.sh/uv/getting-started/installation/) to manage the project
  dependencies.
- Fork the [kneasle/wheatley](https://github.com/kneasle/wheatley/pull/) repository and use `git
  clone` to create a local 'cloned' copy on your machine.
- Do your magic and make the changes you want to your local code.

## Running Your Modified Code

To run Wheatley **from source code**, `cd` to the repository root and run:

```bash
uv run ./run-wheatley [ARGS]
```

## Formatting

In order to enforce styling consistency, all code is formatted with the
[Black](https://black.readthedocs.io/en/stable/) autoformatter (and this is checked for incoming
PRs).  I would strongly recommend enabling format-on-save in your editor of choice
because that way you'll never have to worry about formatting again - Black has some help
[here](https://github.com/psf/black/blob/main/docs/editor_integration.md).  Alternatively, running
`uvx black .` in the project root before a PR will reformat everything and satisfy the PR checks.

## PR checks

In order to make the code more reliable, all incoming PRs are passed through several checks which
automatically look out for and catch mistakes.  All of these can be run with the following:

```bash
uv run ./run-checks.py
```

### Typechecker

These checks require that, on all incoming PRs, the entire codebase has
[type annotations](https://docs.python.org/3/library/typing.html), and that these type annotations
are consistent (e.g. you're not passing an `int` into a function that expects a `str`).  Therefore,
any new or modified code has to continue satisfying the type checker in order for a PR to be merged.
The typechecker can be run locally with the following command and will produce reasonably good error
messages if anything is wrong:

```bash
uv run ./run-checks.py --type-check
```

### Linting

All PRs are also checked by the linter `pylint`, which checks the code automatically for small
issues.  It can be run locally with:

```bash
uv run ./run-checks.py --lint
```

### Unit Tests, Doctests and Fuzzing

These last checks are tests that are built into the source code, and fall into three categories:

1. **Unit Tests**: Small functions which test individual 'units' of the code, e.g. parsing CLI
   arguments.  These make sure that these components do what is expected, and that this behaviour
   doesn't subsequently change.
2. **Doctests**: Doctests are short for 'documentation tests'.  In this case, the documentation in
   question are the examples in the `README`, and this runs all the examples and asserts that they
   all enter `Bot`'s mainloop correctly.  This forces us to keep the examples up to date with any
   changes to the code.
3. **Fuzzing**: Fuzzing is the process of providing some function with large amounts of random input
   and asserting that it doesn't behave unexpectedly.  In our case, we fuzz the CLI arg parsing code
   to make sure that Wheatley will produce pleasant error messages regardless of the user enters.

All three of these can be run with:

```bash
uv run ./run-checks.py --unit-tests
uv run ./run-checks.py --doc-tests
uv run ./run-checks.py --fuzz
```
