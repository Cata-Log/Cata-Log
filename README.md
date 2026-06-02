# Cata-Log Hub

The central hub for grocery store catalogs.

If you can check at least two of the following, this project is for you:

- [] You like to shop items that are on offer.
- [] You like to check what's on offer before you go to the store.
- [] You care about privacy.
- [] You want to use open-source software.
- [] You use an open-source shopping list app.

## Mission

There exist proprietary shopping list apps (which shall not be named here)
that have a viewer for the current offers at various grocery store chains.

This is a feature that has so far not been available
in open-source shopping-list applications.

One main roadblock is the fact that all stores use different implementations
of their online flyers, creating a massive implementation and maintenance
workload for the developers of such apps, should they consider such a feature.

It is the mission of the Cata-Log project to change this status quo.

Cata-Log's main component is a server with interfaces for a multitude of
digital flyer implementations.
It regularly retrieves and caches the online flyers
from user-selected providers.
This data is then offered to third-party applications via
a consistent, unified and comprehensive API.

This way, the load of implementing and maintaining the various interfaces
to the online flyers is distributed onto the shoulders
of the Cata-Log contributors, instead of a single developer.

To further the ease of adaption for third-party developers,
the Cata-Log project includes client-libraries to its API for various languages,
including Java and Swift for mobile- as well as Javascript for web-development.

Adding new flyer providers to Cata-Log is designed to be as easy as possible.
A provider interface is defined by a single Python3 class.
The documentation gives an extensive example and guideline for its implementation.

It's the ultimate goal of the Cata-Log project to have a viewer for
current store offers in the major open-source shopping-planning applications.

## Project Status

*ALPHA*

- The backend is near stable, with some refactors pending.

- The provisional webui still needs some polishing.
  Vital capabilities for managing providers and configs are missing.

- I have added the most relevant german flyer providers,
  other regions must be contributed
  as I am not familiar with the stores or the languages used.

## Roadmap

- Small refactors in the backend
- More provider classes
- Setup client libraries and ship them
-

## Installation

The Cata-Log server is intended to be run
with the container image provided at [dockerhub][dockerhub].

### Docker

Use *docker compose* using [the compose file](docker/docker-compose.minimal.yml)
or an equivalent *docker run* command.

### Podman

Do the same thing as above, just using *podman* instead of *docker*.

### Kubernetes

You can use a tool like [kompose](https://kompose.io)
to translate [the docker compose file](docker/docker-compose.minimal.yml)
to a kubernetes cluster configuration.

### Agentic installation

If you want an agent to install Cata-Log for you,
point it to [the install.md file](install.md), e.g.

```bash
  curl -fsSL https://github.com/cata-log/cata-log-hub/blob/master/install.md | claude
```

## Documentation

The full documentation is available on [ReadTheDocs][readthedocs].

## Contributing

THIS PROJECT LIVES FROM YOUR CONTRIBUTIONS!

If there is a provider class you are missing, give implementing it a try.
The quickstart and guide for implementing a provider class are in the documentation.

Thank you to [everybody who helped with advancing this project](CONTRIBUTORS.md)
and [who helped with translation](TRANSLATORS.rst)!

## License

This software is proudly released under
[the GNU Affero General Public License v3.0 or later (AGPLv3) open-source license](LICENSE).

Its documentation is licensed under
[the Creative Commons Attributions-ShareAlike 4.0 International (CC BY-SA 4.0) license](docs/LICENSE).

Any contributions will be subject to the same licensing.

[dockerhub]: https://hub.docker.com/r/dacid99/cata-log
[readthedocs]: https://cata-log.readthedocs.io/latest/
