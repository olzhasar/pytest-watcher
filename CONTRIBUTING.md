# Contributing

`pytest-watcher` is an open-source project and welcomes all kinds of contributions. Let's make the Python ecosystem better together!

## Local development setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python

### Setup

Clone the repository:

```sh
git clone https://github.com/olzhasar/pytest-watcher.git
```

Install project dependencies:

```sh
uv sync
```

Set up [pre-commit](https://pre-commit.com/) hooks:

```sh
uv run pre-commit install
```

## Changelog

Each PR needs to contain a changelog entry. The project uses [towncrier](https://towncrier.readthedocs.io/en/stable/tutorial.html) for managing the [CHANGELOG.md](./CHANGELOG.md) file.
A changelog entry is a markdown file that should be placed in the [changelog.d](./changelog.d) directory.

As per towncrier’s default configuration, changelog entries need to be one of the following types:

- feature: Signifying a new feature.
- bugfix: Signifying a bug fix.
- doc: Signifying a documentation improvement.
- removal: Signifying a deprecation or removal of public API.
- misc: An issue has been closed, but it is not of interest to users.

### Filename convention

Changelog entries should be named using the convention: `{issue_number}.{type}.md` or `+{unique_string}.{type}.md`

If your PR contains changes that are intended to close one of the open [issues](https://github.com/olzhasar/pytest-watcher/issues), use the first option, e.g. `34.bugfix.md`

For regular changes that won't necessarily result in closing any issues, use the second format `+<unique_string>.<type>.md` (*Note the `+` prefix*). Example: `add_new_section.doc.md`

### Creating entries

You can create entry files manually, or utilize towncrier's CLI:

```
towncrier create -c "Improve documentation" +clarity.doc.md
```

For more info, please check [towncrier's documentation](https://towncrier.readthedocs.io/en/stable/tutorial.html).
