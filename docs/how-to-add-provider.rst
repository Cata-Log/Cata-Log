..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

How To Add A New Provider
=========================

To add a new provider you need to implement a new provider class.

We give a quick rundown of what you need to do, while implementing an example provider.

1. Add a file <your-provider>.py to src/cata_log/providers.
2. In that file define a class <YourProvider> that inherits from the Provider baseclass

.. code-block:: python
    from .base import Provider

    class ExampleProvider(Provider):

3. Now metadata needs to be added to the class. That data can either be obvious (e.g. the provider's region) or can depend on the way you intend to scrape the provider's api.
The following datapoints must be added as class variables to your provider class:

- region
- name
- description
- url

All other datapoints must only be added if they differ from the defaults:

- first_page_number
- configuration
- schedule
- page_file_extension

For our example provider this could be

.. code-block:: python
    class ExampleProvider(Provider):
       region = Germany
       name= "example"
       description = "An example provider"
       url = "https://example.com/catalog"
       first_page_number = 0
       configuration = {"argument": "An argument introduced here for example purposes. You can set any value."}
       schedule = crontab(hour=2) # fetch at 2am every day
       page_file_extension = ".webp"

4. The Provider baseclass is abstract, meaning you must override at least four of its methods.

- get_catalog_data
- get_page
- get_valid_since
- get_valid_until

.. code-block:: python
    class ExampleProvider(Provider):
        ...
        def get_catalog_data(self):

        def get_page(self):

        def get_valid_since(self):

        def get_valid_until(self):

5. If necessary, you may want to override other methods as well.

- get_relevant_datetime

6. To test the provider implementation run the pytest suite.

.. code-block:: console
    pytest test

7. Commit and make a merge request. Done!
