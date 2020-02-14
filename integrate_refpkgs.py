#!/usr/bin/env python3

from treesapp import classy
from treesapp import create_refpkg
from treesapp.file_parsers import load_json_build
from collections import namedtuple
import glob
import shutil
import argparse
import re
import os
import sys


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


RefPkg_Patterns = [re.compile(r"(\w{2,10}).hmm"), re.compile(r"(\w{2,10}).fa"),
                   re.compile(r"(\w{2,10})_bestModel.txt"), re.compile(r"(\w{2,10})_tree.txt"),
                   re.compile(r"tax_ids_(\w{2,10}).txt"), re.compile(r"(\w{2,10})_bipartitions.txt"),
                   re.compile(r"(\w{2,10})_build.json")]


def gather_refpkg_dirs() -> list:
    refpkg_dirs = []
    for final_dir in glob.iglob("**/final_outputs/", recursive=True):
        # Ensure the directory contains all the right files
        dir_files = glob.glob(final_dir + "*")
        if not dir_files:
            continue
        for pattern in RefPkg_Patterns:
            x = 0
            for f_path in dir_files:
                if pattern.match(os.path.basename(f_path)):
                    dir_files.pop(x)
                    break
                x += 1
        if len(dir_files) == 0:
            refpkg_dirs.append(final_dir)
    return refpkg_dirs


def load_marker_build_instances(refpkg_dirs: list, targets=None) -> list:
    if targets is None:
        targets = {}
    markers = []
    empty_dirs = []

    for refpkg_dir in refpkg_dirs:
        marker_build = classy.MarkerBuild()
        for fname in glob.glob(refpkg_dir + "*"):
            build_file = re.match(r"(\w{2,10})_build.json", os.path.basename(fname))
            if build_file and build_file.group(1) in targets:
                marker_build.cog = build_file.group(1)
                targets.remove(marker_build.cog)
                build_params = load_json_build(fname)
                if marker_build.cog != build_params["RefPkg"]["name"]:
                    print("Discrepancy between RefPkg names from file name (%s) and JSON (%s)." %
                          (marker_build.cog, build_params["RefPkg"]["name"]))
                    sys.exit(5)
                marker_build.dict_to_attributes(build_params)
                markers.append(marker_build)
                break
        if not marker_build.cog:
            empty_dirs.append(refpkg_dir)

    if targets:
        [print("Warning: unable to find JSON file in refpkg directory '%s'." % refpkg_dir) for refpkg_dir in empty_dirs]

    return markers


def consensus_name(dir_files: list) -> str:
    candidates = set()
    for pattern in RefPkg_Patterns:
        for f_path in dir_files:
            re_match = pattern.match(os.path.basename(f_path))
            if re_match:
                candidates.add(re_match.group(1))
                break
    if len(candidates) == 1:
        return candidates.pop()
    else:
        print("Unable to determine reference package name for directory '%s'." % os.path.dirname(dir_files[1]))
        return ""


def instantiate_refpkgs(refpkg_dirs: list) -> list:
    ref_packages = []
    for refpkg_dir in refpkg_dirs:
        refpkg_name = consensus_name(glob.glob(refpkg_dir + "*"))
        if not refpkg_name:
            continue
        refpkg = classy.ReferencePackage(refpkg_name=refpkg_name)
        refpkg.gather_package_files(refpkg_dir)
        ref_packages.append(refpkg)
    return ref_packages


def list_refpkgs(ref_packages: list) -> None:
    refpkg_list = []
    for refpkg in ref_packages:  # type: classy.ReferencePackage
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


def validate_treesapp_refpkg_dir(treesapp_dir: str) -> namedtuple:
    if not os.path.isdir(treesapp_dir):
        print("Sorry human, '%s' isn't a directory. Better luck next time." % treesapp_dir)

    hmm_dir = glob.glob(treesapp_dir + os.sep + "hmm_data" + os.sep)
    aln_dir = glob.glob(treesapp_dir + os.sep + "alignment_data" + os.sep)
    tree_dir = glob.glob(treesapp_dir + os.sep + "tree_data" + os.sep)

    refpkg_repository = namedtuple("refpkg_repository", "hmm_dir aln_dir tree_dir")
    if len(hmm_dir) != 1:
        print("Sorry, we're looking for a single directory here:", hmm_dir)
    else:
        refpkg_repository.hmm_dir = hmm_dir[0]
    if len(aln_dir) != 1:
        print("Sorry, we're looking for a single directory here:", aln_dir)
    else:
        refpkg_repository.aln_dir = aln_dir[0]
    if len(tree_dir) != 1:
        print("Sorry, we're looking for a single directory here:", tree_dir)
    else:
        refpkg_repository.tree_dir = tree_dir[0]
    return refpkg_repository


def copy_refpkg_files_to_treesapp(ref_packages, refpkg_repository) -> None:
    for refpkg in ref_packages:  # type: classy.ReferencePackage
        shutil.copy(refpkg.profile, refpkg_repository.hmm_dir)
        shutil.copy(refpkg.msa, refpkg_repository.aln_dir)
        shutil.copy(refpkg.tree, refpkg_repository.tree_dir)
        shutil.copy(refpkg.lineage_ids, refpkg_repository.tree_dir)
        shutil.copy(refpkg.model_info, refpkg_repository.tree_dir)
        if os.path.isfile(refpkg.boot_tree):
            shutil.copy(refpkg.boot_tree, refpkg_repository.tree_dir)
    return


def update_refpkg_table(marker_builds, param_file):
    for marker_build in marker_builds:  # type: classy.MarkerBuild()
        create_refpkg.update_build_parameters(param_file, marker_build)
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
    marker_builds = load_marker_build_instances(refpkg_dirs, {refpkg.prefix for refpkg in ref_packages})

    refpkg_repo = validate_treesapp_refpkg_dir(args.treesapp_install)

    # Copy refpkg files
    copy_refpkg_files_to_treesapp(ref_packages, refpkg_repo)

    param_file = args.treesapp_install + os.sep + "ref_build_parameters.tsv"
    update_refpkg_table(marker_builds, param_file)

    return


main()
