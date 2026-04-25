from celery.schedules import crontab
from typing import override

from cata_log.exceptions import PagesExhausted, CalendarUnavailableWarning

from .base import Provider, Preview
from .configuration import Configuration
from .regions import

# Import some useful helpers. Remove what you don't need.
import calendar
from datetime import datetime, time, timedelta
from urllib.parse import urljoin
from cata_log.utils.dates import get_calendar_week_number


class TemplateProvider(Provider):
    # Mandatory
    uid = # A unique identifier for this provider. Ideally composed of a unique combination of provider attributes (e.g. name + regioncode).
    region =  # The region of the provider. You can add missing regions if needed.
    name=  # Name for the provider. This is used to create a unique identifier together with the regions local name.
    description = # A short description of the provider.
    url = # The URL to the provider's digital flyer.
    # Optional
    first_page_number = 1 # The number of the first page in the provider's counting
    configuration = (
        Configuration(
            name=, # A descriptive and concise name for the configuration value",
            helptext=, # A text describing the configuration and how to figure out what value to set.
            default=, # Only set this if the configuration value is optional
            parse_as=, # What datatype the value should be parseable as, defaults to string
        ),
        # Add more Configurations if required
    )
    schedule = crontab(minute=0, hour=4) # The crontab schedule on which the provider data is cached
    page_file_extension = ".jpg" # The file extension of the page image files

    # The following methods must be implemented.
    # These instance variables are always available:
    #  - _client: A HTTP client you should use to make requests to the provider's server. It raises an error if a status code starting with 4 or 5 is received.
    #  - _relevant_datetime: A datetime at which the provider's flyer is valid. The current datetime by default. Can be used if the URLs of the provider's digital flyer contain date parts.
    # You don't need to care about error handling, the base class deals with this.
    # The only case in which you need to take errors is if they are expected, for example if a page number has no page to it.

    @override
    def _get_catalog_data(self):
        # Get any data required to access the page's data in this function.
        # You can store that data in instance variables, the function returns nothing.
        #
        # Raise CalendarUnavailableWarning if the provider's flyer is not available.
        # Only raise this if the unavailability is not an indication for a larger issue with the provider,
        # for example if a preview or retrospect is not yet or no longer online.

    @override
    def _get_page(self, page_number):
        # Get and return the image data of the page with number defined by the page_number argument.
        #
        # page_number is an instance of the PageNumber class.
        # It can be converted to a DoublePageNumber that helps in iterating data that is organized in the double page format.
        # See aldi.py for an example for this behaviour.
        # If you need the number of the page as an integer, use int(page_number).
        #
        # Raise PagesExhausted if there is no page corresponding to page_number.
        # You don't need to do this if the missing page leads to a 404 HTTP status error. That case is handled by the base class.
        # Cases where you need to raise PagesExhausted yourself are,
        # for example, if the page url is extracted from a dictionary first and that extraction raises an Index- or KeyError.
        # See aldi.py for an example where you need to raise manually.
        # See norma.py for an example where you don't need to raise.
        #
        # In the same scenarios as in _get_catalog_data, you can raise CalendarUnavailableWarning.

    @override
    def _get_valid_since(self):
        # Calculate and return the datetime of the point in time that the provider's flyer becomes valid.
        # Typically the _relevant_datetime is used as a starting point.
        # With some providers, the date is contained in data fetched by _get_catalog_data.
        # You can then use the datetime and calendar utilities to get the needed datetime.
        # See aldi.py for an example of a provider with well-known ryhthm.
        # See kaufland.py for an example of a provider with validity timestamps in the catalog data.

    @override
    def _get_valid_until(self):
        # Calculate and return the datetime of the point in time that the provider's flyer becomes valid.
        # If the provider's flyers follow a specific ryhthm (e.g. weekly),
        # you can use the value returned by _get_valid_since as starting point.
        # See aldi.py for an example of a provider with well-known ryhthm.
        # See kaufland.py for an example of a provider with validity timestamps in the catalog data.

    @override
    def get_relevant_datetime(self):
        # Override this only if the provider's flyer is not valid in the moment the flyer is intended to be cached.
        # Mostly relevant for preview and retrospect flyers.



# If the provider offers more digital flyers like previews, that use the same logic as the current flyer,
# you can simply inherit from the current flyer's provider class and override just what needs to be adapted.

class TemplatePreviewProvider(Preview, TemplateProvider):
    # Override the methods that are different for the preview flyer.
    #
    # See netto.py for an example of a provider with both preview and retrospect provider classes.
    uid = # Set a uid for the preview
    name = # A proper name for the preview
    description = # A description for the preview provider
    preview_timedelta = timedelta( # the timedelta that the preview is ahead of the regular flyer release schedule
