# Contributing to Translations

Thank you for your interest in contributing to this translation project! This repository manages localization files for various projects using TOML format with Python CLI tools for editing, validating, and deploying language resources.

## Getting Started

### Prerequisites
- Python 3.7 or higher
- Basic understanding of TOML format
- Git

### Setting Up Your Environment
1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/translations.git
   cd translations
   ```

## Project Structure

```
translations/
├── projects/               # Contains all translation projects
│   ├── project1/          # Example project directory
│   │   ├── welcome.toml          # Simple string file
│   │   ├── message_count.toml    # Plural file (separate!)
│   │   └── title.toml
│   └── project2/
├── allowed_locales.txt    # List of allowed locale codes
├── build.py               # CLI tool for managing translations
└── target/                # Output directory for built resources
```

**Important Structural Rule:** Simple strings and plural forms are **always stored in separate files**. A single `.toml` file must contain either:
- **Only** simple strings (using the `v` key), OR
- **Only** plural forms (using the `one`, `other`, etc. keys)

Mixing string types within the same file is not allowed and will cause build errors.

## Locale Organization

**The Fundamental Rule:** Locales in this repository **must be ordered by the total number of speakers (L1 + L2) worldwide**. The authoritative source for this order is the latest [**Ethnologue data**](https://en.wikipedia.org/wiki/List_of_languages_by_total_number_of_speakers#Ethnologue_(2025)).

This ordering ensures we prioritize translations for the most widely spoken languages first, maximizing global accessibility. The primary base locale for all projects is **`en_US`**.

### Speaker Count Ordering
When adding or editing translations, you **must** list locale keys in `.toml` files in descending order by total speaker count. For example, using our three primary example locales:

| Language | Locale Code | Total Speakers (Millions) | Correct Order |
| :--- | :--- | :--- | :--- |
| **English** | `en_US` | 1,528 | **First** |
| **Spanish** | `es_ES` | 558 | **Second** |
| **Russian** | `ru_RU` | 253 | **Third** |

**Important Note:** This ordering applies to **all** locales in the `allowed_locales.txt` file. English (`en_US`) always comes first, followed by other languages in strict descending order of their total speaker count as per the latest Ethnologue data.

## Adding Translations

### Understanding the TOML Format
Each `.toml` file represents **one translatable concept**. Files must contain either simple strings OR plurals, never both.

#### Example 1: Simple String File (`projects/2fa/settings_section_behavior_button_tap_to_reveal_primary.toml`)
```toml
# Simple string file (uses "v" key for value)
[en_US] # 1528 million speakers (First)
v = "Tap to reveal codes"

[es_ES] # 558 million speakers (Second)
v = "Tocar para mostrar códigos"

[ru_RU] # 253 million speakers (Third)
v = "Показать коды при нажатии"
```

#### Example 2: Plural String File (`projects/2fa/main_list_number_of_accounts.toml`)
```toml
# Plural file (uses "one", "other" keys) - SEPARATE FILE!
[en_US]
one = "Showing %d account"
other = "Showing %d accounts"

[es_ES]
one = "Mostrando %d cuenta"
other = "Mostrando %d cuenta"

[ru_RU]
one = "Показан %d аккаунт"
few = "Показано %d аккаунта"
many = "Показано %d аккаунтов"
other = "Показано %d аккаунта"
```

### Adding a New Locale
If you need to add a language not currently in `allowed_locales.txt`:
1.  **Verify its rank**: Check the total speaker count against the [authoritative source](https://en.wikipedia.org/wiki/List_of_languages_by_total_number_of_speakers).
2.  **Propose the addition**: Open an issue to request the new locale, citing its total speaker count and the position where it should be inserted in the ordered list.
3.  **Implement**: Once approved, add the locale to **both simple string files and plural files** in the project, in its correct numerical position.

## Using the Build Script (`build.py`)

The `build.py` script is the primary tool for validating and building translations.

### List Available Projects
```bash
python build.py --list
```

### Check Translation Completion
Get the percentage of completed translation files for a specific project or all projects.
```bash
# For a specific project
python build.py --check --project PROJECT_NAME

# For all projects
python build.py --check
```

### Find Missing Translations
List files that are missing translations for a specific locale.
```bash
# For a locale in a specific project
python build.py --missing LOCALE_CODE --project PROJECT_NAME

# For a locale across all projects
python build.py --missing LOCALE_CODE
```

### Build Android Resources
Compile `.toml` files into Android `strings.xml` resource files. The script automatically handles the separation of simple strings and plurals.
```bash
python build.py --project PROJECT_NAME --target android
```
The output will be generated in the `target/android/` directory.

## Quality Guidelines

### Translation Quality
- **Accuracy**: Faithfully convey the original meaning and intent.
- **Consistency**: Use the same terminology for the same concepts across all files.
- **Context**: Consider where the text will appear (button, label, error message).
- **Placeholders**: Never reorder or alter placeholders (e.g., `%d`, `%s`). Ensure they are correctly positioned for the target language's grammar.

### Technical Requirements
1.  **File Separation**: Simple strings and plurals must be in separate files.
2.  **Ordering**: Always maintain the speaker-count order in every file.
3.  **Completeness**: All files should ideally have entries for every locale in `allowed_locales.txt`. Use the `--check` and `--missing` commands to verify.
4.  **Encoding**: Files must be saved with UTF-8 encoding.
5.  **Plurals**: Always provide both `one` and `other` keys for countable items. Some languages may also require `few` or `many`.

## Making Changes & Submitting

### Workflow
1.  **Create a Branch**:
    ```bash
    git checkout -b feature/translation-for-xx
    ```
2.  **Make and Test Changes**:
    - Add or edit translation files.
    - **Ensure you haven't mixed simple strings and plurals.**
    - Run `python build.py --check --project YOUR_PROJECT` to validate completion.
    - Run `python build.py --missing LOCALE_CODE --project YOUR_PROJECT` to find gaps.
    - Manually verify locale ordering is correct.
3.  **Commit**:
    ```bash
    git add .
    git commit -m "Add [Language] translations for [Project]"
    ```
4.  **Push and Open a Pull Request (PR)** on GitHub.

### Pull Request Requirements
For a smooth review, please ensure your PR includes:
- A clear title describing the language and project.
- A description noting you have verified the changes with the build script.
- **Confirmation that all locale keys follow the official speaker-count order.**
- **Confirmation that simple strings and plurals remain in separate files.**
- If adding a new locale, justification with its speaker count and source.

## Adding a New Language

To formally propose adding a new language to the repository:
1.  Open an issue with the title "New Language Request: [Language Name]".
2.  In the description, provide:
    - The **standard locale code** you propose (e.g., `fr_FR` for French).
    - The **total number of speakers (L1+L2)** from the latest Ethnologue data.
    - The **exact position** it should occupy in the `allowed_locales.txt` list.
    - A brief explanation of its global relevance for software.

## Code of Conduct

By participating, you agree to maintain a respectful, collaborative, and inclusive environment. We welcome contributors from all backgrounds.

## Getting Help

- **Discord**: Join our [community on Discord](https://discord.com/invite/zxgXNzhYJu) for quick questions and discussion.
- **Bluesky**: Follow updates on [Bluesky](https://bsky.app/profile/979.st).
- **Issues**: Use the [GitHub issue tracker](https://github.com/979st/translations/issues) for bugs, problems, or formal language requests.
