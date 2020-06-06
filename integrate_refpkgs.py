#!/usr/bin/env python3

import glob
import shutil
import argparse
import re
import os

from treesapp import refpkg as ts_refpkg


def get_arguments():
    parser = argparse.ArgumentParser(description="integrate_refpkgs.py is a script that allows users to integrate "
                                                 "all reference packages stored in this repository into a TreeSAPP "
                                                 "installation directory.")
    parser.add_argument("-i", "--treesapp_install", required=True,
                        help="Path to a TreeSAPP installation directory. "
                             "Reference packages will be integrated into this installation.")
    parser.add_argument("-n", "--name", required=False,
                        default=None,
                        help="The name or names of reference packages that you would like to be integrated. "
                             "If multiple names are provided, separate only with commas (no spaces).")
    parser.add_argument("-l", "--list", required=False,
                        default=False, action="store_true",
                        help="List all of the reference package names that are available for integration.")

    return parser.parse_args()


_RefPkgPattern = re.compile(r"(\w{2,10})_build.json")


def gather_refpkg_dirs() -> list:
    refpkg_files = []
    for final_dir in glob.iglob("**/final_outputs/", recursive=True):
        # Ensure the directory contains all the right files
        dir_files = glob.glob(final_dir + "*")
        if not dir_files:
            continue
        x = 0
        while x < len(dir_files):
            if not _RefPkgPattern.match(os.path.basename(dir_files[x])):
                dir_files.pop(x)
            else:
                x += 1
        if len(dir_files) == 1:
            refpkg_files.append(dir_files.pop())
    return refpkg_files


def instantiate_refpkgs(refpkg_files: list) -> list:
    ref_packages = []
    refpkg_file_map = {}
    print("Instantiating reference packages:")
    for refpkg_json in refpkg_files:
        refpkg = ts_refpkg.ReferencePackage()
        refpkg.f__json = refpkg_json
        refpkg.slurp()
        if not refpkg.validate():
            continue
        ref_packages.append(refpkg)
        refpkg_file_map[refpkg.prefix] = refpkg_json

    print("\t" +
          "\n\t".join([refpkg_name + ": " + refpkg_file_map[refpkg_name] for refpkg_name in sorted(refpkg_file_map)]))
    return ref_packages


def list_refpkgs(ref_packages: list) -> None:
    refpkg_list = []
    for refpkg in ref_packages:  # type: ts_refpkg.ReferencePackage
        refpkg_list.append(refpkg.prefix)
    print("Available reference packages:\n\t%s" % "\n\t".join(refpkg_list))
    return


def filter_refpkgs_by_name(ref_packages: list, names: str) -> None:
    targets = names.split(',')
    x = 0
    while x < len(ref_packages):
        refpkg = ref_packages[x]
        if refpkg.prefix not in targets:
            ref_packages.pop(x)
        else:
            x += 1

    if len(ref_packages) == 0:
        print("No reference packages were found that matched target names '%s'" % names)

    return


def validate_treesapp_refpkg_dir(treesapp_dir: str) -> None:
    if not os.path.isdir(treesapp_dir):
        print("Sorry human, '%s' isn't a directory. Better luck next time." % treesapp_dir)

    if os.sep == treesapp_dir[-1]:
        treesapp_dir = treesapp_dir[:-1]

    # Detect whether the directory is a beneath a TreeSAPP installation or just a plain directory
    base, dir1 = os.path.split(treesapp_dir)
    if dir1 == "data":
        base, dir2 = os.path.split(base)
        if dir2 == "treesapp":
            print("Copying reference packages into TreeSAPP installation directory")
            return
    print("Copying reference packages into custom directory location")
    return


def copy_refpkg_files_to_treesapp(ref_packages, refpkg_repository: str) -> None:
    # Ensure the directory exists
    validate_treesapp_refpkg_dir(refpkg_repository)

    for refpkg in ref_packages:  # type: ts_refpkg.ReferencePackage
        shutil.copy(refpkg.f__json, refpkg_repository)
    return


def main():
    args = get_arguments()
    refpkg_dirs = gather_refpkg_dirs()
    ref_packages = instantiate_refpkgs(refpkg_dirs)

    if args.list:
        list_refpkgs(ref_packages)
        return
    if args.name:
        filter_refpkgs_by_name(ref_packages, args.name)

    # Copy reference pacakge JSON files
    copy_refpkg_files_to_treesapp(ref_packages, args.treesapp_install)

    return


main()
