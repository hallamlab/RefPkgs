#!/usr/bin/env python3

import glob
import shutil
import argparse
import re
import os
import sys
import logging
from datetime import datetime as dt

from treesapp import refpkg as ts_refpkg
from treesapp.classy import prep_logging
from treesapp.commands import create


def get_arguments():
    parser = argparse.ArgumentParser(description="refpkg_manager.py is a script that allows users to integrate "
                                                 "all reference packages stored in this repository into a TreeSAPP "
                                                 "installation directory.")
    parser.add_argument("-i", "--treesapp_install",
                        required=False, default=None,
                        help="Path to a TreeSAPP installation directory. "
                             "Reference packages will be integrated into this installation.")
    parser.add_argument("-n", "--name",
                        required=False, default=None,
                        help="The name or names of reference packages that you would like to be integrated. "
                             "If multiple names are provided, separate only with commas (no spaces).")
    parser.add_argument("-l", "--list",
                        required=False, default=False, action="store_true",
                        help="List all of the reference package names that are available for integration.")

    parser.add_argument("--update", required=False, default=False, action="store_true",
                        help="Updates reference packages specified by the user with --name parameter.")

    parser.add_argument("--template", default=None, choices=["slurm"],
                        help="[ IN PROGRESS ] "
                             "Create a template file for running `treesapp create` to rebuild reference packages.")

    parser.add_argument("--copy", default=False, action="store_true",
                        help="Copies the reference packages specified (all by default) to a directory.")

    return parser.parse_args()


_RefPkgPattern = re.compile(r"(\w{2,10})_build.pkl")  # This needs to match ReferencePackage.refpkg_suffix


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
    logging.info("Instantiating reference packages:\n")
    for refpkg_json in refpkg_files:
        refpkg = ts_refpkg.ReferencePackage()
        refpkg.f__json = refpkg_json
        try:
            refpkg.slurp()
            if not refpkg.validate():
                continue
            ref_packages.append(refpkg)
        except (IndexError, KeyError, AttributeError, TypeError):
            logging.warning("Unable to load reference package %s. Skipping.\n" % refpkg.f__json)
        refpkg_file_map[refpkg.prefix] = refpkg_json

    logging.info("\t" + "\n\t".join([refpkg_name + ": " + refpkg_file_map[refpkg_name] for
                                     refpkg_name in sorted(refpkg_file_map)]) + "\n")
    return ref_packages


def list_refpkgs(ref_packages: list) -> None:
    refpkg_list = []
    for refpkg in ref_packages:  # type: ts_refpkg.ReferencePackage
        refpkg_list.append(refpkg.prefix)
    logging.info("Available reference packages:\n\t%s" % "\n\t".join(refpkg_list) + "\n")
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
        logging.warning("No reference packages were found that matched target names '%s'\n" % names)

    return


def build_templates(ref_packages: list, scheduler: str) -> None:
    """
    Automatically generate scripts for launching treesapp create with popular job scheduling systems.

    :param scheduler:
    :param ref_packages:
    :return:
    """
    # TODO: Parse the treesapp create command from each reference package
    # TODO: Find the number of threads to use
    if scheduler == "slurm":
        pass
    else:
        logging.error("Unknown scheduler provided. Unable to write template file.\n")
        sys.exit(3)
    return


def rebuild_gather_reference_packages(ref_packages: list) -> None:
    """
    Attempts to rebuild every reference package in ref_packages by running treesapp create.
    It uses the command in the ReferencePackage.cmd attribute to pull all the parameters needed.

    The original treesapp create outputs are overwritten and this is ensured by including the '--overwrite' flag

    :param ref_packages: A list of ReferencePackage instances
    :return: None
    """
    for refpkg in ref_packages:  # type: ts_refpkg.ReferencePackage
        # Parse the treesapp create command from each reference package
        create_cmd_str = re.sub(r"^treesapp create ", '', refpkg.cmd)
        create_params = create_cmd_str.split()
        if "--overwrite" not in create_params:
            create_params.append("--overwrite")

        # Find the path of the output
        if "--output" in create_params:
            rebuild_path = create_params[create_params.index("--output") + 1]
        elif "-o" in create_params:
            rebuild_path = create_params[create_params.index("-o") + 1]
        else:
            logging.error("Unable to find the output path (with neither '-o' nor '--output') "
                          "in treesapp create command used for '{}'\n".format(refpkg.prefix))
            sys.exit(3)

        # Attempt to rebuild
        try:
            # Run treesapp create with each reference package's command
            create(create_params)
        except:
            logging.warning("treesapp create was unable to rebuild '{}'.\n".format(refpkg.prefix))

        refpkg.f__json = os.path.join(rebuild_path, "final_outputs", refpkg.prefix + refpkg.refpkg_suffix)
        refpkg.slurp()

    return


def validate_treesapp_refpkg_dir(treesapp_dir: str) -> None:
    if not os.path.isdir(treesapp_dir):
        logging.error("Sorry human, '%s' isn't a directory. Better luck next time.\n" % treesapp_dir)
        raise AssertionError

    if os.sep == treesapp_dir[-1]:
        treesapp_dir = treesapp_dir[:-1]

    # Detect whether the directory is a beneath a TreeSAPP installation or just a plain directory
    base, dir1 = os.path.split(treesapp_dir)
    if dir1 == "data":
        base, dir2 = os.path.split(base)
        if dir2 == "treesapp":
            logging.info("Copying reference packages into TreeSAPP installation directory\n")
            return
    logging.info("Copying reference packages into custom directory location\n")
    return


def copy_refpkg_files_to_treesapp(ref_packages, refpkg_repository: str) -> None:
    # Ensure the directory exists
    validate_treesapp_refpkg_dir(refpkg_repository)

    for refpkg in ref_packages:  # type: ts_refpkg.ReferencePackage
        shutil.copy(refpkg.f__json, refpkg_repository)
    return


def main():
    prep_logging(log_file_name=os.path.join(os.getcwd(),
                                            "refpkgs_" + dt.now().strftime("%Y-%m-%d") + "_log.txt"),
                 verbosity=False)

    args = get_arguments()

    refpkg_dirs = gather_refpkg_dirs()
    ref_packages = instantiate_refpkgs(refpkg_dirs)

    # TODO: Differentiate reference packages found in directories made by treesapp update
    if args.list:
        list_refpkgs(ref_packages)
        return
    if args.name:
        filter_refpkgs_by_name(ref_packages, args.name)

    if args.template:
        build_templates(ref_packages, args.template)

    if args.update:
        rebuild_gather_reference_packages(ref_packages)

    if args.copy:
        # Copy reference package pickle files
        if not args.treesapp_install:
            logging.error("TreeSAPP installation directory was not provided. Not sure where to copy the refpkgs!\n")
            return
        copy_refpkg_files_to_treesapp(ref_packages, args.treesapp_install)

    return


main()
