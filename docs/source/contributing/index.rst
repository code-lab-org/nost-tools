Contributing
============

Thank you for your interest in contributing to the NOS Testbed (NOS-T). This guide will help you understand how to contribute effectively to this project.

Ways to Contribute
----------------

There are several ways you can contribute to NOS-T:

* Reporting bugs and issues
* Suggesting new features or enhancements
* Improving documentation
* Adding or enhancing examples
* Contributing code fixes or new functionality

Development Setup
---------------

To set up your development environment:

1. Fork the repository
2. Clone your fork: ``git clone https://github.com/your-username/nost-tools.git``
3. Set up a virtual environment: ``python -m venv venv``
4. Activate the environment: ``source venv/bin/activate`` (Linux/Mac) or ``venv\Scripts\activate`` (Windows)
5. Install development dependencies: ``pip install -e ".[dev]"``

Coding Standards
--------------

* Follow PEP 8 style guidelines
* Write docstrings in Google Docstring format
* Include unit tests for new functionality
* Maintain compatibility with Python 3.8+

Pull Request Process
------------------

1. Create a new branch for your feature or fix
2. Make your changes and commit them with descriptive messages
3. Push your branch to your fork
4. Submit a pull request to the main repository
5. Respond to any feedback from reviewers

Documentation Guidelines
----------------------

* Use reStructuredText format for all documentation
* Follow NASA documentation standards where applicable
* Include examples where helpful
* Keep API documentation up to date with code changes

.. toctree::
   :maxdepth: 1

   code_of_conduct
   development_workflow