# mamayo

**WORK IN PROGRESS; NONE OF THIS ACTUALLY WORKS YET  :)**

mamayo helps you put your Python Web application on the Internet.

If you're scoffing and thinking "I already know how to do that!  I just write an Upstart job to keep Gunicorn running and define a new reverse proxy endpoint in my nginx configuration", then this is not for you!  This is for:

* Smaller projects,
* People with shared hosting who don't know anything about Python or WSGI, but would like to run some Python Web software, and
* People who sometimes want to run a small one-off Web app on their own hardware and dislike the `mod_wsgi` approach, but don't want to muck around with all the setup and configuration files and needing root.

Dare I even call it: Python Deployment for Humans.

## Name

The word "mamayo" (ままよ) is defined by the [WWWJDIC project](http://www.csse.monash.edu.au/~jwb/cgi-bin/wwwjdic.cgi?1C) as:

    whatever; never mind; I don't care; the hell with it

This is the mamayo philosophy.  I don't care about WSGI or proxies or Twisted Web; I just want to serve this thing.

## Installation

Install mamayo with `pip`:

    pip install --user mamayo


TODO: what if you don't have pip?

TODO: what if you don't understand the command line?  (single egg blob to drop somewhere?)

## Configuration




## Unanswered questions

* What's the convention for where to put apps?
* How do we run this thing the first time?  How do we run it on boot?
* To meet the requirement of adding new apps at runtime, we basically have to proxy the entire app through mamayo.  How do we minimize the hit for things that we don't control?  (Also, how do we deal with static assets that are part of apps themselves?)
    * nginx's `try_files`?  (May not work with upstreams...)
    * X-Sendfile?  (Doesn't work with anything but static files...)
    * Special status code for talking to the rproxy?




## Future features

* Web interface for managing your WSGI apps, installing stuff into virtualenvs, reading error logs, viewing stats, etc.
* Seamless upgrade.
* App hooks for installation/upgrades -- database setup, etc.
* Library adapter to run any kind of WSGI app (special detection for known common frameworks?) as CGI, FastCGI, HTTP...



## Requirements (for the deploy part anyway)

* Avoid dying _ever_.
    * Respawn when we crash.
    * Notice when the child process has become unresponsive and kill it.
    * Notice when the supervisor is trapped in a loop and, as a last effort, bail.  (Email the user?)
* Support nginx, lighttpd, apache2.
* Require _minimal_ use of root to install; nginx, for example, will generally need root to edit its configuration.
* Require **NO** root to add an app.
* Don't require a configuration file.
* Don't put code in the document root.
* Try to avoid giant perf hits, like CGI or proxying every single request.
* Use existing components, like gunicorn and uWSGI.
* Work on Dreamhost and NearlyFreeSpeech with minimal effort.  (Other obvious targets?  Many shared hosts suck, so I can't target them all, but a baseline of a few popular free/cheap hosts would be awesome.)
* Be practical for shared hosts to install and let their users use.
