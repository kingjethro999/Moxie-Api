# Contributing to Moxie API

First off, thank you for considering contributing to Moxie! It's people like you that make the open-source community such a great place to learn, inspire, and create.

## How Can I Contribute?

### Reporting Bugs
*   Check the [issue tracker](https://github.com/kingjethro999/Moxie-Api/issues) to see if the bug has already been reported.
*   If not, open a new issue with a clear title, description, and steps to reproduce.

### Suggesting Enhancements
*   Open an issue to discuss your idea before implementing it.
*   Clearly describe the problem you're trying to solve and how the enhancement will help.

### Pull Requests
1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/my-new-feature`).
3.  Make your changes.
4.  Run tests: `pytest`.
5.  Commit your changes (`git commit -am 'Add some feature'`).
6.  Push to the branch (`git push origin feature/my-new-feature`).
7.  Open a Pull Request.

## Development Setup

1.  Clone the repository:
    ```bash
    git clone https://github.com/kingjethro999/Moxie-Api.git
    cd Moxie-Api
    ```
2.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install dependencies in editable mode:
    ```bash
    pip install -e ".[dev]"
    ```

## Style Guide
*   We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.
*   Please ensure your code passes `ruff check .`.

## License
By contributing to Moxie, you agree that your contributions will be licensed under its MIT License.
