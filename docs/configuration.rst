..
   SPDX-License-Identifier: CC-BY-SA 4.0

   Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
   Licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

Configuration
=============

Cata-Log is configured via the docker environment variables.

Mandatory
---------

+----------+----------------------------------------------------------+
| Setting  | Description                                              |
+==========+==========================================================+
| PASSWORD | The password to authenticate with the Cata-Log instance. |
+----------+----------------------------------------------------------+

Optional
--------

+-----------------------+----------+-----------------------------------------------------------------------------------------------+
| Setting               | Default  | Description                                                                                   |
+=======================+==========+===============================================================================================+
| USERNAME              | admin    | The user of the Cata-Log instance.                                                            |
+-----------------------+----------+-----------------------------------------------------------------------------------------------+
| PUBLIC_GET            | False    | Whether the GET endpoints of this instance should be accessible without authentication.       |
+-----------------------+----------+-----------------------------------------------------------------------------------------------+
| REQUEST_TIMEOUT       | 10       | The timeout for HTTP requests to external provider servers in seconds.                        |
+-----------------------+----------+-----------------------------------------------------------------------------------------------+
| MAX_RETRIES           | 3        | How many times jobs that failed due to network errors will be retried.                       |
+-----------------------+----------+-----------------------------------------------------------------------------------------------+
| RETRY_DELAY           | 180      | How long to wait between task retries in seconds.                                             |
+-----------------------+----------+-----------------------------------------------------------------------------------------------+
| EXPIRATION_DAYS       | 14       | Catalog data will be automatically deleted after this number of days after its creation.      |
+-----------------------+----------+-----------------------------------------------------------------------------------------------+
| LOG_LEVEL             | INFO     | Log level of the Cata-Log application. Must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL.  |
+-----------------------+----------+-----------------------------------------------------------------------------------------------+
| LOG_FILE_BACKUP_COUNT | 5        | The number of logfile backups to keep.                                                        |
+-----------------------+----------+-----------------------------------------------------------------------------------------------+
| LOG_FILE_MAXSIZE      | 2097152  | The maximum size of a single logfile before turnover in bytes.                                |
+-----------------------+----------+-----------------------------------------------------------------------------------------------+
