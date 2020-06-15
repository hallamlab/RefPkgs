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

- Install TreeSAPP

- Fork `RefPkgs` to your GitHub account

- Clone your forked version of `RefPkgs`

- Move into `RefPkgs` and create a new branch with `git checkout -b MyBranchName`

- Build refpkg with `treesapp create`
    - ensure the paths are relative
    - If the inputs are large, consider clustering to remove duplicates
    - Leave all inputs used in the path, except for NCBI taxid files (if used)
    - Use `--delete` flag to remove the 'intermediates' directory

- Test with `treesapp purity`

- Commit your new refpkg
    - And push

- Create a pull request to the main RefPkgs repository
    - Here is the [official help page](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork) on how to do just this.

- Receive eternal praise from developers :)
