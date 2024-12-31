.. _programming-skills:

**Programming Skills**
----------------------

A solid grasp of programming concepts and tools is crucial for contributing to the development and validation of **FlowCyPy**.
Below, we highlight the essential skills and resources to enhance your proficiency.

.. _python-programming:

Python Programming
~~~~~~~~~~~~~~~~~~

Python is the backbone of **FlowCyPy**. It is essential to understand its key concepts, features, and best practices to effectively contribute to the project.

Key areas of focus include:

- **Object-Oriented Programming (OOP)**:

  - Writing and understanding functions and classes.
  - Classes in Python should always start with an uppercase letter (e.g., ``class Detector``).
  - All other objects are fully lowercase (e.g., ``object``, ``function``).

- **Popular Libraries**:

  - ``numpy`` for numerical operations.
  - ``matplotlib`` for creating visualizations.
  - ``pandas`` for efficient data manipulation and analysis.

- **Debugging and Troubleshooting**:

  - Use tools like `pdb`, `ipdb`, or IDE-based debuggers (e.g., in VS Code or PyCharm).

Additional Python Essentials
****************************

- **What is pip?**

  - ``pip`` is the Python package manager used to install, update, and manage libraries in Python projects.
  - Example: ``pip install numpy``

- **What is conda?**

  - ``conda`` is an environment and package manager that supports Python and other languages.
  - It is useful for managing dependencies and creating isolated environments.
  - Example: ``conda create --name flowcypy-env python=3.10``

- **PEP Standards**:

  - Python Enhancement Proposals (PEPs) define Python's design and best practices.
  - Follow `PEP 8 <https://peps.python.org/pep-0008/>`_ for consistent and clean coding style.

  - Example:

    - Indentations should be 4 spaces.
    - Use snake_case for variable and method names.

- **Interactive Python**:

  - Use Jupyter notebooks or Python's interactive shell for rapid testing and prototyping.

*Suggested Practice*: Enhance your skills with hands-on exercises available on `CodeChef Practice <https://www.codechef.com/practice>`_.

.. _git-and-version-control:

Git and Version Control
~~~~~~~~~~~~~~~~~~~~~~~

Version control is essential for collaborative software development. You will use Git to manage the **FlowCyPy** codebase effectively.
Familiarity with the following Git commands is expected:

- ``git clone``: Clone repositories to your local machine for development.
- ``git pull``: Fetch and merge changes from the remote repository.
- ``git commit``: Save changes locally with descriptive commit messages.
- ``git push``: Upload your changes to the remote repository.
- ``git branch``: Create and manage branches for new features or experimental changes.
- ``git merge``: Integrate updates from different branches.
- ``git stash``: Temporarily save changes without committing them.

Best Practices for Git
**********************

- Commit frequently with clear and concise commit messages.
- Always pull the latest changes before starting new work to avoid conflicts.
- Use branches to isolate different tasks or features.

.. note::

   **Mini Objective**:
   Try creating a new branch, making a change, committing it, and merging it back into the main branch.

*Recommended Resource*: Master Git workflows through the `Pro Git Book <https://git-scm.com/book/en/v2>`_.
