# Tasks

* [X] ~~*Use config file to set conda env, odoo src dir, worktree dir*~~ [2019-06-10]

* [X] ~~*worktree interaction*~~ [2019-06-10]
    - checkout to worktree
    - use worktree as working dir

* [X] ~~*create workspace after new worktree*~~ [2019-06-10]

* [X] ~~*be able to properly checkout odoo-dev branches.*~~ [2019-06-16]

* [X] ~~*delete branch workspace*~~ [2019-06-16]

* [X] ~~*Specify only one branch name and will create/fetch branch for odoo and enterprise. e.g.*~~ [2019-06-16]
    ```
    $ odev -b master-pos-test-jcb new
    ```
    - the above command will create branch `master-pos-test-jcb` in both odoo
    and enterprise repos. But if the branch exists in remote (including -dev),
    the remote branch will be checkout.
    - I need more granular control with this.
        - if branch in odoo/odoo-dev and not in enterprise/enterprise-dev,
        checkout odoo worktree and create enterprise worktree based on master.
        - if branch not in odoo/odoo-dev but in enterprise/enterprise-dev,
        create odoo worktree based on master and checkout enterprise worktree.
        - if branch not found in both odoo and enterprise, create new branch in
        both
        - if branch is found in both, checkout both

* [X] ~~*the `new` (rename to `init`) command should not do everything. maybe `prepare` command can be used to prepare dev env - checkout/create branch, create worktree, create workspace. Sample commands:*~~ [2019-06-16]
    ```
    // prepare new dev environment
    $ odev -b master-pos-jcb prepare

    // initialize new db
    $ odev -b master-pos-jcb -d testdb init

    // start db (default db=testdb) and install point_of_sale
    $ odev -b master-pos-jcb start -i point_of_sale

    // start shell
    $ odev -b master-pos-jcb shell
    ```

* [X] ~~*change worktree structure*~~ [2019-06-16]
    ```
    worktree-dir/<branch>/odoo
    worktree-dir/<branch>/enterprise
    ```


# Proposed Features

This app is about odoo development workflow.
