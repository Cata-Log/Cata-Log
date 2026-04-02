..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

FAQ
===

This is a list of frequently asked questions with their answers
and quick solutions to common problems.

If you have run into a problem running Cata-Log, check out the :doc:`troubleshooting page <troubleshooting>`.

What's the point of this application?
-------------------------------------

If you prefer to shop things that are on sale, you likely skim the shops catalog or flyer.

Some proprietary shopping list apps (not to be named here) have a feature to read the current flyers in-app.
This is something that is missing in all the open-source shopping list apps and servers.

One of the reasons for this is that the API of the various providers are obscure and vary strongly.
This makes it hard for developers of the apps to incorporate the catalog and flyer data.

That is exactly where Cata-Log comes in!
It gathers all the catalog data from the various providers and offers them to third-parties via a unified and consistent API interface.
That way an app can check and fetch
- the catalog providers the user is interested in and has configured in Cata-Log
- the catalogs these providers currently offers
- the pages of these catalogs for display in their app interface

Developers of the third-parties now only have to design one logic for connecting to the Cata-Log API.

Cata-Log also provides libraries for this purpose for even more ease on the side of app developers.


I am new to self-hosting, how can I set up an instance the easiest?
-------------------------------------------------------------------

Setting up a Cata-Log server is quick and straightforward.
The simplest way to spin Cata-Log up for the first time is described on :doc:`the quickstart page <quickstart>`.
For a complete install check out :doc:`the installation guide <installation>`.


Do I need special hard- or software to run Cata-Log?
-------------------------------------------------------

One goal of this project is to be easily available across many platforms.
Essentially, everything that can run containers is viable to deploy Cata-Log.
That includes every modern Linux, Windows, MacOS, FreeBSD, etc.
It also doesn't require or consume a lot of resources,
so even low-spec and old devices should do fine.


Do I need a license to use this application?
--------------------------------------------

This project is licensed under the :doc:`AGPLv3 license <license>`.
That means that everyone can freely use this software.

There is only a restriction if you want to alter and publish the source code.
In that case your version of the program has to be released under the same license,
so the project remains free software.


I have found a problem with the application, what should I do?
--------------------------------------------------------------

You can check whether :doc:`the troubleshooting page <troubleshooting>` includes the problem.

If not, please try to figure out whether the problem may be specific for your setup first.
If it is not, please file an issue in one of the online repositories.

In case the problem is not related to the source code itself,
there is unfortunately not much we can do about it.
Please try to debug it with other users and admins over stack-overflow, reddit or other platforms.

If the problem is security-related please contact one of the developers privately instead.


Will there be translations to other languages beside english?
-------------------------------------------------------------

No, as this is mainly intended to serve as an api interface,
there are no plans to implement localization and translation.
The providers are described in the language of their region anyway,
so you should not have trouble finding and adding the ones you actually need.
If you still have trouble with the language,
many browsers have an autotranslation feature that may help you.


How can I contribute to this project?
-------------------------------------

Everyone is welcome to help with the development of Cata-Log!

To get you off to a good start please check out the quickstart and how-to guidelines.
You can find them alongside the source code documentation in the :doc:`developers section <developers>`.
