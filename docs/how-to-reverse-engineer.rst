..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

How To Reverse Engineer A Provider
==================================

This is a quickstart into figuring out how a providers online flyer works.

The main tool for this task is your browser.
The instructions given here will work for firefox and all chromium-based browsers.

All modern browsers have a development panel that allows introspecting the inner workings of a webpage.
You can find that panel by rightclicking the page and selecting *Inspect*.

Central for reverse-engineering a digital flyer webpage is the incoming traffic.
The page must load the pictures of the flyer pages from somewhere.
You can see all network traffic caused by the current page in the *Network* tab of the dev-panel.
Reload the page to recapture all traffic.

Scan and filter that data for images.
Try to find the ones that are part of the digital flyer presentation.

Is there a pattern to the URLs that they were loaded from?

If yes, you now just need to figure out how to construct these URLs yourself.
Most commonly, these types of URLs contain some form of the current date like the year and the calendar week number.
Short identifiers for the flyer type are also common.

If no, then the image URLs are most likely read from another document, typically a json file.
That file must also be loaded from a server, so check the traffic again.

In the worst case scenario, if you don't find a feasible way to retrieve the pages with a few http requests, you can fallback to requesting the entire flyer page and parse the page image urls from the html.
