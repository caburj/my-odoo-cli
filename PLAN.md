# Tasks

* [X] ~~*Use config file to set conda env, odoo src dir, worktree dir*~~ [2019-06-10]
* [X] ~~*worktree interaction*~~ [2019-06-10]
    - checkout to worktree
    - use worktree as working dir
* [X] ~~*create workspace after new worktree*~~ [2019-06-10]
* [X] ~~*be able to properly checkout odoo-dev branches.*~~ [2019-06-16]
* [X] ~~*delete branch workspace*~~ [2019-06-16]

# Proposed Features

This app is about odoo development workflow.
* [ ] Specify only one branch name and will create/fetch branch for
odoo and enterprise. e.g.
    ```
    $ odev -b master-pos-test-jcb new
    ```
    - the above will create branch `master-pos-test-jcb` in both odoo and
    enterprise repos. But if the branch exists in remote (including -dev), the
    remote branch will be checkout.
