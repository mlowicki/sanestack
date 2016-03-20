# sanestack
Check if your dependencies are up to date.

If using [requirements.txt](https://pip.readthedocs.org/en/latest/user_guide/#requirements-files) to specify project's dependencies it's advised to lock their versions ([A Better Pip Workflow™](http://www.kennethreitz.org/essays/a-better-pip-workflow)). This way while releasing you avoid surprises when new version of package will be installed and your application starts to fail for unknown reason even if it worked 10 minutes ago on staging or playground deploy.

But if everything will be locked would be nice to have an automated way to tell if maybe something new has been shipped beyond what is specified to keep your stack up to date with latest fixes. This is what `sanestack` provides. It tells if there are updates for pinned packages.

[![asciicast](https://asciinema.org/a/d59w0r2aar7s1xn9s0ta7uu7y.png)](https://asciinema.org/a/d59w0r2aar7s1xn9s0ta7uu7y)
