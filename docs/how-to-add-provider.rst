..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

How To Add A New Provider
=========================

To add a new provider you need to implement a new provider class.

There is a template in :doc:`the *docs/template-provider.py* file <template-provider>`. It also contains a lot of explanations.

Here we give a quick rundown of what you need to do, while implementing an example provider.

1. Add a file <your-provider>.py to src/cata_log/providers (or copy the template there).
2. In that file define a class <YourProvider> that inherits from the Provider baseclass

.. code-block:: python

    from .base import Provider

    class ExampleProvider(Provider):

3. Now metadata needs to be added to the class. That data can either be obvious (e.g. the provider's region) or can depend on the way you intend to scrape the provider's api.
The following datapoints must be added as class variables to your provider class:

- uid: A unique identifier for this provider class. Ideally consists of unique combination of attributes of the class (e.g. name + regioncode).
- name: The Name of the provider. This is used to create a unique identifier together with the regions local name.
- description: A description of the provider and the flyer that makes it possible for users to identify it.
- url: A URL to the provider's digital flyer webpage.
- region: The region the flyer is distributed in. If the region is missing, adding it is very straightforward. Just check out and follow :doc:`the guide <how-to-add-region>`.

All other datapoints must only be added if they differ from the defaults:

- first_page_number (``1``): The number of the first page of a flyer in the provider's publicly accessible data.
- configuration (``()``): A tuple of configuration values for accessing the digital flyer data.
- schedule (``0 4 * * *``): A crontab string defining the caching schedule. For more details on the crontab syntax, see `the wikipedia page <https://en.wikipedia.org/wiki/Cron>`_.

For our example provider this could be

.. code-block:: python

    from .regions import Germany
    from .configuration import Configuration

    class ExampleProvider(Provider):
       uid = "example-de"
       name= "Example-Provider"
       description = "An example provider for the purpose of the documentation."
       url = "https://example-provider.de/catalog"
       region = Germany
       first_page_number = 0
       configuration = (
           Configuration(name="argument", helptext="An argument introduced here for example purposes. You can set any value."),
           Configuration(name="optional_argument", helptext="An optional argument. If it is omitted, the default will be used.", default ="Default value"),
           Configuration(name="parsed_argument", helptext="An argument that must represent a certain datatype like an integer.", parse_as=int),
       )
       schedule = "30 2 * * *" # fetch at 2:30am every day

4. The Provider baseclass is abstract, meaning you must implement at least four of its methods.
    To make this as easy as possible, the base class provides a couple of variables and wraps the code you write.

    - self._client: A HTTP client instance that you should use to make requests to the provider's website.
    - self._relevant_datetime: The datetime identifying the flyer.

    **You do not have to worry about handling errors. The base class will take care of that.**
    You only need to catch and handle expected errors, you will see what that means when we continue with the example.

    The methods you must implement are:

    - _get_catalog_data:

        This allows you to get data from the provider which is needed to access the pages of the flyer.

        For example, some providers offer an endpoint to download a json file with the URLs to all currently available flyers and their pages.
        That data can be retrieved and stored in an instance variable to access it in the _get_page method.

        .. code-block:: python

            from typing import override
            ...
                @override
                def _get_catalog_data(self):
                    self.pages_json = self._client.get("https://example-provider.com/api/v5/where-are-all-the-pages").json()

        If this method is not needed, just set ``pass`` as its body. That way a call to it will do exactly nothing.

    - _get_page:

        In this function you fetch the image data for a single page of the flyer.
        The page to be fetched is defined by the page_number argument.

        Of course it is not clear that the requested page number exists in the flyer.
        That's where error handling comes into play.
        If the page number does not exist in the json data we got in _get_catalog_data, then that needs to be addressed.
        The rule is simple: If the page to the page_number argument does not exist, you raise a ``PagesExhausted`` exception.

        There are some fallbacks to make this even more simple:
        If you make a HTTP request for page data and that page doesn't exist, the provider's server will most likely respond with status 404.
        You do not need to handle this yourself. If a status 404 error occurs in _get_page,
        is is assumed that the page doesn't exist as long as the number of the page is not the first page number as defined earlier.

        .. code-block:: python

            from cata_log.exceptions import PagesExhausted
            from urllib.parse import urljoin
            ...
                @override
                def _get_page(self, page_number):
                    try:
                        page_relative_url = self.pages_json["current_catalogs"]["pages"][int(page_number)]["url"]
                    except IndexError as index_error:
                        raise PagesExhausted from index_error
                    return self._client.get(urljoin("https://example-provider.com/catalog/pages/", page_relative_url)).content

    - _get_valid_since:

        This function returns the datetime of the moment that the flyer became valid, in the sense that the offers in it became active.
        Typically that will be 0am of the start-day labeled on the flyer. There is no need to consider store opening hours.

        Let's say our flyer always becomes active on wednesday.
        Then we need to calculate back to the past wednesday to get the start-datetime of the currently active flyer.

        We need to think about this for a bit:
        If we get the flyer on a Friday, then the last wednesday will be 2 days prior.
        If we get it on a Monday, the last wednesday will be 5 days in the past.
        So if we take the weekday number of the current date
        and subtract the weekday number of wednesday we get the difference of days to the wednesday within the same week.
        Negative values mean the wednesday of the week is coming up, so we need to add 7 to that difference to turn it into the difference to the previous wednesday.
        One way to do this concisely is to use the `modulus <https://wikipedia.com/en/modulus>`_, also known as division rest.

        .. code-block:: python

            from calendar import Day
            from datetime import datetime, time, timedelta
            ...
                @override
                def _get_valid_since(self):
                    return datetime.combine( # this function combines a date, a time and a timezone into a single datetime object
                        self._relevant_datetime - timedelta(days=(self._relevant_datetime.weekday() - Day.WEDNESDAY ) % 7), # subtract the difference to the previous wednesday from the current date
                        time.min, # set the earliest time of day (0.00am)
                        self._relevant_datetime.tzinfo, # set the timezone of the relevant datetime
                    )

    - _get_valid_until:

        This function returns the datetime of the moment after the flyer became invalid, in the sense that the offers in it became inactive.
        Typically that will be 0am of the day after the end-day labeled on the flyer. There is no need to consider store opening hours.

        If the flyer has a fixed ryhthm, like being valid for an entire week, the implementation of this method is really simple.
        We just add an entire week to the valid_since datetime.

        In our example the flyer always becomes valid on a wednesday so the offers also end on the next wednesday.

        .. code-block:: python

            @override
            def _get_valid_until(self):
                return self._get_valid_since() + timedelta(days=7)

5. If necessary, you may want to override other methods as well.

    - get_relevant_datetime:

        This method returns the datetime that is relevant to identify the provider's flyer.

        In many cases, the digital flyer URLs contain the year and calendar-week number of the week in which the flyer is valid.
        For example: *https://other_provider.com/catalogs/2026_week41/pages/1.jpg*

        To be able to format this string, a datetime within the flyer's activity timeframe is required.
        That is what the _relevant_datetime variable is set up for.

        The standard implementation returns just the current datetime in the provider region's timezone.
        With that datetime, the currently active flyer can be retrieved.

        If you want to implement a flyer preview of a flyer with a weekly schedule, you need the relevant datetime to be in the next week, not the current one.
        You can achieve this by overriding the get_relevant_datetime method and adding a week to the default implementation.

        .. code-block:: python

            @override
            def get_relevant_datetime(self):
                return super().get_relevant_datetime() + timedelta(days=7)

        In many cases, digital preview flyers follow the same or similar logic as current catalogs.

        For these cases, a preview provider class can inherit from the current provider class and override just this method.
        To make this even simpler, a mixin is provided that does exactly that.

        .. code-block:: python

            from .base import Preview
            ...

            class ExamplePreviewProvider(Preview, ExampleProvider):
                ...
                preview_timedelta = timedelta(days=7)

        Note the order of inheritance, the mixin must come first.


We are now done implementing our example provider class.

Putting it all together we get

.. code-block:: python

    from calendar import Day
    from datetime import datetime, time, timedelta
    from urllib.parse import urljoin
    from typing import override

    from cata_log.exceptions import PagesExhausted

    from .base import Provider, Preview
    from .configuration import Configuration
    from .regions import Germany


    class ExampleProvider(Provider):
        region = Germany
        name= "example"
        description = "An example provider for the purpose of the documentation"
        url = "https://example-provider.com/catalog"
        first_page_number = 0
        configuration = (
            Configuration(name="argument", helptext="An argument introduced here for example purposes. You can set any value."),
            Configuration(name="optional_argument", helptext="An optional argument. If it is omitted, the default will be used.", default ="Default value"),
            Configuration(name="parsed_argument", helptext="An argument that must represent a certain datatype like an integer.", parse_as=int),
        )
        schedule = "30 2 * * *" # fetch at 2:30am every day

        @override
        def _get_catalog_data(self):
            self.pages_json = self._client.get("https://example-provider.com/api/v5/where-are-all-the-pages").json()

        @override
        def _get_page(self, page_number):
            page_relative_url = self.pages_json["current_catalogs"]["pages"].get(int(page_number))
            if not page_relative_url:
                raise PagesExhausted
            return self._client.get(urljoin("https://example-provider.com/catalog/pages/", page_relative_url)).content

        @override
        def _get_valid_since(self):
            return datetime.combine( # this function combines a date, a time and a timezone into a single datetime object
                self._relevant_datetime - timedelta(days=self._relevant_datetime.weekday() - Day.WEDNESDAY), #
                time.min, # set the earliest time possible (0.00am)
                self._relevant_datetime.tzinfo, # set the timezone of the relevant datetime
            )

        @override
        def _get_valid_until(self):
            return self._get_valid_since() + timedelta(days=7)


    class ExamplePreviewProvider(Preview, ExampleProvider):
        uid = "example-de-preview"
        name = "example-preview"
        description = "An example preview provider"
        preview_timedelta = timedelta(days=7)



For more exemplary implementations, you can check the source code of existing and stable provider classes.


- *norma.py* implements provider classes that don't need to get any catalog data.
- The provider classes in *aldi.py* look a lot like what we coded as an example.


Now to check your code into the main repository, a few more steps have to be taken.

1. Test your provider implementation. This will check if there are any grave mistakes in the way you defined the class and its attributes.

    .. code-block:: console

        pytest test

2. Test the provider manually by using it as a plugin.
To turn your provider file into a viable plugin, replace all imports from . into imports from cata_log.providers

    .. code-block:: python

        from .base import Provider
        vvvvvvvvvvvvvvvvvvvvvvvvvv
        from cata_log.providers.base import Provider

With that file follow :doc:`the guide for plugins <plugins>` to run it in a Cata-Log instance.

After you're done testing, restore the original import paths.

3. Lint the code you created, please run

    .. code-block:: console

        ruff check --config=tools/ruff.toml

    This will fix small obvious code quality problems and give you a list of other remaining issues.
    All linting rules are `fully documented <https://astral.sh/ruff/rules/>`_.
    If there's something you are not sure how to fix, just leave it as is.
    It can be taken care of in reviewing the merge request.

4. Commit and make a merge request using the *New Provider* template. Done!
