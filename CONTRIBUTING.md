# Contributing to RefPkgs

TreeSAPP was developed knowing full well that it will never have a large impact without widespread engagement from the community.
Curating sequences for refpkgs is *hard* and time-consuming. Building an good reference package -- one that won't lead to spurious annotations --
often requires extensive knowledge of the enzyme and domains within them,
and their evolutionary history within the context of the protein family.

We have built some reference packages that are available both within RefPkgs and TreeSAPP that we hope lead to accurate classifications.
However, that small set only represents what we felt comfortable with.

This is why it is our goal to enable experts to create, reproduce and validate the reference packages that are distributed as part of the TreeSAPP software.

## Overview

- Reference packages are created using `treesapp create`
- Reference packages are tested using `treesapp purity`
- Reference packages are uploaded to RefPkgs

# How to Contribute

1. Install TreeSAPP

    Reference packages rely on TreeSAPP, and in order for both the `refpkg_manager.py` script to your and for you to build
new reference packages TreeSAPP must be installed. Please follow the [instructions](https://github.com/hallamlab/TreeSAPP/wiki/Installing-TreeSAPP)
and leave an issue using the TreeSAPP issue if you run into any issues.

2. Fork `RefPkgs` to your GitHub account

    This will allow you to make edits (such as including new directories, fasta files, etc.) to the `RefPkgs` repository
without being an official contributor. Your contributions will still be tracked though!

3. Clone your forked version of `RefPkgs`

    Clone the `RefPkgs` repository onto your local machine.

4. Move into `RefPkgs` and create a new branch with `git checkout -b MyBranchName`

    You are now ready to edit the repository and begin creating any new reference packages.

5. Build a reference package with `treesapp create`
 
    `RefPkgs` is currently supporting the TreeSAPP version (0.8.4 a development version on the ng-update branch).
The instructions to build a reference package using this version are available [here](https://docs.google.com/document/d/1QmQzKFO5lV2VYL5M-p8NyodBbmwAhhtcOPU3NjsMCu0/edit#heading=h.b1xi59elqo3a).
Some key points are:  
    - Ensure the paths are relative to RefPkgs installation directory
    - If the inputs are large, consider clustering to remove duplicates
    - Leave all inputs used in the path, except for NCBI taxid files (if used)
    - Use `--delete` flag to remove the 'intermediates' directory

6. Optionally, test with `treesapp purity`

    This command quickly attempts to classify [TIGRFAM](http://tigrfams.jcvi.org/cgi-bin/index.cgi) seed sequences
    using the new reference package. If the reference package is able to classify sequences from unexpected families it
    strongly indicates your reference package is impure. This could be the result of misannotated sequences finding their
    way into your candidate reference sequences or perhaps a domain is shared between your target and the off-target protein family.
    More details on using `treesapp purity` are available [here](https://github.com/hallamlab/TreeSAPP/wiki/Testing-the-functional-purity-of-reference-packages).

7. Commit and push your new reference package

    If you are satisfied with your reference package and no errors were encountered while running any of the commands
    you can now commit the files from the reference package to your `RefPkgs` repository.
    If you wrote the outputs to `Methanogenesis/MtrA/seed_refpkg/` your commands from the `RefPkgs` directory could be:

    ```shell script
    git add Methanogenesis/MtrA/seed_refpkg/
    git commit -m "New reference package for MtrA"
    git push -u origin MyBranchName
    ```

8. Create a pull request to the main RefPkgs repository
    
    Here is the [official help page](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork) on how to do just this.

9. Receive eternal praise from developers :)
