# Introduction

My odoo dev commands

# To install

```
// install in development mode in your current python env
$ git clone https://github.com/caburj/my-odoo-cli.git
$ cd my-odoo-cli
$ pip install -e .

// copy .odev file in your home dir
$ cp .odev ~/.odev
$ cat
[DEFAULT]
conda-env = master
odoo-src = ~/Projects/odoo-dev/src
worktree-src = ~/Projects/odoo-dev/worktrees
default-dbname = testdb
default-port = 8070
workspace-dir = ~/Projects/workspaces
kernelspec-dir = ~/Projects/kernelspecs
```

**NOTE** Folders defined in the .odev file have to exist.

# Sample Usage

**Prepare worktree for existing branch in origin**

```
// the code below checkouts worktrees for saas-12.4 in community and enterprise
// and create vscode workspace.
$ odev -b saas-12.4 prepare
```

**Initialize an new instance**

```
// Initializes an odoo instance based on branch saas-12.4 with db named
// testdb-saas-12.4. Installing accounting and pos modules.
$ odev -b saas-12.4 -d testdb-saas-12.4 init -i point_of_sale account_accountant
```

**Start an instance**

```
// other odoo-bin options can be passed after '-w' option
$ odev -b saas-12.4 -d testdb-saas-12.4 start -w --test-enable --test-tag account
```

# Help

```
Usage: odev [OPTIONS] COMMAND [ARGS]...

My personal odoo dev commands in the terminal.

Options:
-d, --dbname TEXT [default: testdb]
-p, --port TEXT [default: 8070]
-b, --branch TEXT [default: master]
-e, --conda-env TEXT
--help Show this message and exit.

Commands:
cd
copy-db Duplicate an existing database.
gen-kernelspec Start a shell instance.
init Once worktrees are available, start new instance.
prepare Check out appropriate branch to worktrees (both community...
remove Remove `prepared` branch (workstrees and workspace).
shell Start a shell instance.
start Start an existing instance.
```
