..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

How To Add A New Provider
=========================

To add a new provider you need to implement a new provider class.

There is a template in :doc:`the *docs/template-provider.py* file <template-provider>`. It also contains a lot of explanations.

Here we give a quick rundown of what you need to do, while implementing an example provider.

Implementation Details and Example
----------------------------------

1. Add a file <your-provider>.py to src/cata_log_hub/providers (or copy the template there).
2. In that file define a class <YourProvider> that inherits from the Provider baseclass

.. code-block:: python

    from .base import Provider

    class ExampleProvider(Provider):

3. Now metadata needs to be added to the class. That data can either be obvious (e.g. the provider's region) or can depend on the way you intend to scrape the provider's api.
    The following datapoints must be added as class variables to your provider class:

    - uid: A unique identifier for this provider class. Ideally consists of unique combination of attributes of the class (e.g. name + regioncode).
    - name: The user-facing name of the provider.
    - description: A description of the provider and the flyer that makes it possible for users to identify it.
    - url: A URL to the provider's digital flyer webpage.
    - region: The region the flyer is distributed in. If the region is missing, adding it is very straightforward. Just check out and follow :doc:`the how-to-add-regions guide <how-to-add-region>`.


    All other datapoints must only be added if they differ from the defaults:

    - first_page_number (``1``): The number of the first page of a flyer in the provider's publicly accessible data.
    - schedule (``0 4 * * *``): A crontab string defining the caching schedule. For more details on the crontab syntax, see `the wikipedia page <https://en.wikipedia.org/wiki/Cron>`_.
    - jitter (``3600``): The maximum number of seconds that the caching schedule is randomly delayed. This is relevant to reduce load on the provider's server infrastructure.

    For our example provider this could be

    .. code-block:: python

        from .regions import Germany

        class ExampleProvider(Provider):
            uid = "example-de"
            name= "Example-Provider"
            description = "An example provider for the purpose of the documentation."
            url = "https://example-provider.de/catalog"
            region = Germany
            first_page_number = 0
            schedule = "30 2 * * *" # fetch at 2:30am every day

4. Define the configuration required for the provider.
    Some providers offer different flyers based on local branch, region, etc.
    That is information the user must supply in order to identify the correct version of the flyer for them.

    In our example there is flyer for every store of the provider company.
    We need the internal ID of the store. The user can find it in a cookie that is set by the online catalog.

    The configuration is defined via a nested class that inherits from the default provider configuration.

    For every piece of information to be given by the user, we define a variable of that class.
    Please provide a description so the user knows how to figure out the value he needs to set.

    .. code-block:: python

        from pydantic import Field

        ...

        class ExampleProvider(Provider):
            ...

            class Configuration(Provider.Configuration):
                store_id: str = Field(description="""
                    The ID of the store.
                    Open the example provider's webpage and select your store.
                    Open the browser's webinspector and search the cookie with name 'store-id'.
                    The value of this cookie is the store_id.
                    """
                )

    You can set a default if there is a reasonable fallback in case the user doesn't provide a value.

    Skip this step if you don't need information from the user in order to cache your provider's online flyer.

5. The Provider baseclass is abstract, meaning you must implement at least four of its methods.
    To make this as easy as possible, the base class provides a couple of variables and wraps the code you write.

    - self._client: A HTTP client instance that you should use to make requests to the provider's servers.
    - self._relevant_datetime: The datetime identifying the flyer.
    - self._configuration: An instance of the configuration class with the values given by the user.

    **You do not have to worry about handling errors. The base class will take care of that.**
    You only need to catch and handle expected errors, you will see what that means as we continue with the example.

    The methods you must implement are:

    - _get_catalog_data:
        This allows you to get data from the provider which is needed to access the pages of the flyer.

        For example, our providers offer an endpoint to download a json file with the URLs to all currently available flyers and their pages.
        This file's URL contains the store_id that the user needs to set in the configuration and the current year.

        The json data can then be retrieved and stored in an instance variable to access it in the _get_page method.

        .. code-block:: python

            from typing import override
            ...
                @override
                def _get_catalog_data(self):
                    url = "https://example-provider.com/{year}/{store_id}/where-are-all-the-pages".format(
                        year=self._relevant_datetime.year,
                        store_id=self._configuration.store_id,
                    )
                    self.pages_json = self._client.get(url).json()

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

            from cata_log_hub.exceptions import PagesExhausted
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
        Typically that will be 0am in the provider region's timezone of the start-day labeled on the flyer.
        There is no need to consider store opening hours.

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

        Some providers include the flyer validity timestamps in the data fetched with _get_catalog_data.
        Of course it is recommended to use these if available.
        Be careful when working with naive datetimes. If _get_valid_since returns a naive datetime, the provider regional timezone is set to make it aware.
        If that is not correct, you need to handle the timezone yourself.
        Make sure to use replace(tzinfo=...) and not astimezone, as the latter will perform a conversion from the machines local timezone, which is almost always incorrect.

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

        This timestamp can also be retrieved in _get_catalog_data, see the remarks on _get_valid_since.

6. Depending on your implementation you may use additional methods.

    - _cleanup:
        If you have instantiated classes in other methods that need to be closed when everything is done.
        This is the place to do it.

7. If the provider's catalog is a preview, you can include the Preview mixin to manage the time shift between the datetimes.

    Typically, digital preview flyers follow the same or similar logic as their current catalogs analogs.
    By using the mixin you only change the datetimes to match the timeframe of the preview and preserve the other behaviour.

    In many cases, the digital flyer URLs contain the year and calendar-week number of the week in which the flyer is valid.
    For example: *https://other_provider.com/catalogs/2026_week41/pages/1.jpg*

    To be able to format this string to get the preview flyer, _relevant_datetime needs to be shifted.
    E.g. if you want to implement a flyer preview of a flyer with a weekly schedule, you need the relevant datetime to be in the next week, not the current one.

    .. code-block:: python
        from .base import Preview
        ...

        class ExampleProvider(Preview, Provider):
            ...

    Note the order of inheritance, the mixin must come first.

    You can then manage the time difference between the timeframe of the current and preview catalog
    using the ``_get_preview_timedelta`` method.

    .. code-block:: python
        class ExampleProvider(Preview, Provider):

            @override
            def _get_preview_timedelta(self):
                return


We are now done implementing our example provider class.

Complete Example
^^^^^^^^^^^^^^^^

Putting all the pieces of the example together we get

.. code-block:: python

    from calendar import Day
    from datetime import datetime, time, timedelta
    from pydantic import Field
    from urllib.parse import urljoin
    from typing import override

    from cata_log_hub.exceptions import PagesExhausted

    from .base import Provider, Preview
    from .regions import Germany


    class ExampleProvider(Provider):
        region = Germany
        name= "example"
        description = "An example provider for the purpose of the documentation"
        url = "https://example-provider.com/catalog"
        first_page_number = 0
        schedule = "30 2 * * *" # fetch at 2:30am every day

        class Configuration(Provider.Configuration):
            store_id: str = Field(description="The ID of the store. Open the example provider's webpage and select your store. Open the browser's webinspector and search the cookie with name 'store-id'. The value of this cookie is the store_id.")

        @override
        def _get_catalog_data(self):
            url = "https://example-provider.com/{year}/{store_id}/where-are-all-the-pages".format(
                year=self._relevant_datetime.year,
                store_id=self._configuration.store_id,
            )
            self.pages_json = self._client.get(url).json()

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

        @override
        def get_preview_timedelta(self):
           return timedelta(days=7)


Further Reading
^^^^^^^^^^^^^^^

For more exemplary implementations, you can check the source code of existing and stable provider classes.

- *norma.py* implements provider classes that don't need to get any catalog data.
- *lidl.py* gets the valdiity timestamps from the catalog data json.
- *penny.py* extracts the flyer pages from the flyer pdf download as the provider API is too obscure.
- The provider classes in *aldi_sued.py* look a lot like what we coded as an example.

Next Steps
----------

Now to check your code into the main repository, a few more steps have to be taken.

1. Lint the code you created, please run
    .. code-block:: console

        ruff check --config=tools/ruff.toml

    This will fix small obvious code quality problems and give you a list of other remaining issues.
    All linting rules are `fully documented <https://astral.sh/ruff/rules/>`_.
    If there's something you are not sure how to fix, just leave it as is.
    It can be taken care of in the process of reviewing the merge request.

2. Test your provider implementation. This will check if there are any grave mistakes in the way you defined the class and its attributes.
    .. code-block:: console

        pytest test/cata_log_hub/providers

3. Test the provider manually. Install the cata_log_hub package from your local source with the new provider class
    .. code-block:: console

        uv pip install -e .

    and start it

    .. code-block:: console

        python3 -m cata_log_hub --password=passwd

    Now you can test your provider class in action by adding a provider with its class_uid and running the caching task.

4. Commit and make a merge request using the *New Provider* template. Done!
