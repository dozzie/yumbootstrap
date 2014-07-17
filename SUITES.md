Suites format
=============

*Suite* is a description of what to install, from where and what to execute
after installation.

Suite file is expected to have a name of `<suite_name>.suite`.

Suite file
----------

The content is (mostly) typical INI file. Comment lines begin with `;` or `#`
sign (leading spaces are allowed; trailing comments in a line are not
supported).

### main (unnamed) section

Two required keys in main section are `name` (distribution name) and
`release`.

`gpg_key` is a multi-value option. It's a path to public GPG key used to sign
RPMs to be installed.

  * Path is relative to suite file's location.
  * Value can contain `${suite}` placeholder, which will be filled with suite
    name (filename with ".suite" stripped)
  * If value is set with `?=` instead of just `=`, the path is included if the
    specified file exists.

`packages` is a path to packages list file and similarly to `gpg_key`, it's
a multi-value option. The same comments apply: it's relative to suite file's
location, `${suite}` gets expanded and `?=` is supported.

### [post_install] section

`[post_install]` section specifies what scripts to run after installation has
finished. Scripts can have parameters specified, but only with basic
tokenization (i.e. split on whitespaces). `${suite}` placeholder is expanded
here.

Scripts are run in the order which they were defined in suite file. They have
names, so you can run or disable them selectively. Two or more scripts can
share the name, so they will be run or disabled always in a group (*NOTE*:
sharing the name does not affect the execution order).

First token from the script line is either a path to the script (if the token
contains `/`) or a command searched in `$PATH`. If it is a path, it is
relative to suite file's location (*NOTE*: arguments, if any, are left
intact). `?=` in such case is supported.

Scripts are run in the same directory as yumbootstrap was. They have
environment reset, with some predefined variables and `[environment]` section
applied.

Environment variables set by yumbootstrap:

  * `$TARGET` -- directory where suite is installed
  * `$VERBOSE` -- "true" or "false" (lowercase), depending on presence of
    *--verbose* option in yumbootstrap's command line
  * `$SUITE`, `$SUITE_CONF` -- suite name (`${suite}`) and path to suite file
  * `$YUMBOOTSTRAP_DIR` -- directory with yumbootstrap's installation data,
    relative to `$TARGET`
  * `$YUM_CONF` -- `yum.conf` path, relative to `$TARGET`; full path to
    `yum.conf` is `$TARGET/$YUM_CONF`
  * `$SCRIPT_NAME` -- name of the script (the token before `=` or `?=`)
  * `$SCRIPT_PATH` -- path to the script

### [environment] section

Yum and post-install scripts are run with environment variables reset
completely. `[environment]` section is a mean to pass some variables down to
these processes.

The first way is to define a value straight. This is done as typical INI
syntax `NAME = VALUE`, with leading and trailing spaces from value stripped.

The second way is to define what variables are passed from parent's
environment. You just specify a variable name, like `LANG`, or a glob, like
`LC_*` or `SUDO_*`.

### [repositories] section

This section defines where the packages come from. It's a simple,
single-valued list of (name,URL) pairs. No expansion or conditionals are done
here.

### example suite file

    name = CentOS
    release = 5

    gpg_key = gpg-keys/${suite}.asc
    gpg_key ?= gpg-keys/${suite}-secondary.asc

    packages = packages/${suite}.list
    packages ?= packages/${suite}-local.list

    [post_install]
    post = scripts/${suite}.sh
    local ?= scripts/local.py ${suite}
    finalize = scripts/fix_rpmdb.py
    finalize = scripts/clean_yumbootstrap.py

    [repositories]
    centos         = http://mirror.centos.org/centos/5/os/$basearch/
    centos-updates = http://mirror.centos.org/centos/5/updates/$basearch/

    [environment]
    NEW_VARIABLE = value, leading and trailing spaces stripped
    LANG
    LC_*
    SUDO_*

Package list
------------

This file is a simple list of packages to install. Comments (lines beginning
with `#`) and empty lines are ignored.

A line may start with `@` sign, which denotes a package group to be installed.
If it starts with `-` sign, it specifies a package to be excluded from
installation. Any other line is passed to Yum as is. This way package names,
paths and virtual dependencies (e.g. `perl(Foo::Bar)`) are all supported.

### example package list file

    # comments and whitespaces are allowed (and ignored)
    basesystem
    python-rpm

    # paths are allowed
    /usr/bin/db_load

    # group names
    @Core

    # excluded RPMs
    -openssh-server

