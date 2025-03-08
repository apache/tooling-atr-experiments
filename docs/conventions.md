# Project conventions

## Python functions

### Name functions in a collation friendly way

Functions should be named hierarchically, with the most general category first, followed by increasingly specific details. This makes related functions group together naturally when sorted alphabetically, making code navigation and discovery easier.

**Example**:

Instead of scattered, hard to find related functions:

```python
def get_user_from_db():
def insert_new_record():
def query_user_settings():
def update_db_record():
```

Use hierarchical naming that groups related functionality:

```python
def db_user_get():
def db_record_insert():
def db_user_settings_query():
def db_record_update():
```

**Example**:

Another example with license files, the wrong way:

```python
def check_root_license_file():      # Lost among other "check_" functions
def validate_package_license():     # Separated from other license functions
def verify_license_files():         # Yet another scattered license function
```

The right way:

```python
def license_root_file_check():      # All license-related functions
def license_package_validate():     # will appear together when
def license_files_verify():         # sorted alphabetically
```

Note how verbs tend to come last, so that function names now read in an object oriented style, with a module, object, and action.

While this approach can lead to slightly longer function names, the benefits of improved code organisation and discoverability outweigh the verbosity.

### Give helper functions the same prefix as their parent function

This makes it easier to find all the functions related to a specific task.

**Example**:

Instead of:

```python
def verify_archive_integrity():
def do_something_in_verify_archive_integrity():
```

Use the same prefix:

```python
def verify_archive_integrity():
def verify_archive_integrity_do_something():
```

This makes it easier to find all the functions related to a specific task, and means that they sort together.

### Keep cyclomatic complexity below 10

We limit function complexity to a score of 10. If the linter complains, your function is doing too much.

Cyclomatic complexity counts the number of independent paths through code: more if/else branches, loops, and exception handlers means higher complexity. Complex code is harder to test, maintain, and understand. The easiest way to fix high complexity is usually to refactor a chunk of related logic into a separate helper function.

### Use parentheses to group subexpressions in boolean expressions always

Instead of this:

```python
a or b and c == d or e
```

Do:

```python
(a or b) and (c == d) or e
```

## HTML

### Use sentence case for headings

We write headings like "This is a heading", and not "This is a Heading" or "This Is A Heading". This follows the [Wikipedia style for headings](https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style#Section_headings). The same goes for button texts.
