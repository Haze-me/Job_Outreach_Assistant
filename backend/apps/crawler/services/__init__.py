"""Crawler service layer.

Split by responsibility so each piece is testable on its own:

* ``http``       -- safe fetching: SSRF guards, timeouts, size caps, robots.txt
* ``discovery``  -- deciding which internal pages are worth visiting
* ``extraction`` -- pulling email addresses out of fetched HTML
* ``scanner``    -- orchestration: runs a scan and records its results
"""
