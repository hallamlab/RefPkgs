#!/usr/bin/env python3

import re
import os
import sys
import glob
import shutil
import argparse
import logging
import unittest
from datetime import datetime as dt
from time import sleep

from treesapp import refpkg as ts_refpkg
from treesapp.classy import prep_logging
from treesapp.commands import create

_RefPkgPattern = re.compile(r"(\w{2,10})_build.pkl")  # This needs to match ReferencePackage.refpkg_suffix


class RefPkgsTestSuite(unittest.TestCase):
    def setUp(self) -> None:
        self.mcra_pickle = "Methanogenesis/McrA/seed_refpkg/final_outputs/McrA_build.pkl"
        self.puha_pickle = "Photosynthesis/PuhA/seed_refpkg/final_outputs/PuhA_build.pkl"
        self.mcra_refpkg = ts_refpkg.ReferencePackage("")
        self.puha_refpkg = ts_refpkg.ReferencePackage("")
        self.xmoa_dir = "Nitrogen_metabolism/Nitrification/XmoA/"
        self.tmp_dir_path = "./temp_refpkg_dir/"

        # Clear out the temporary directory if it exists. Needs to be empty for tests
        if os.path.isdir(self.tmp_dir_path):
            shutil.rmtree(self.tmp_dir_path)

        # Load the McrA and PuhA reference packages
        self.mcra_refpkg.f__json = self.mcra_pickle
        self.puha_refpkg.f__json = self.puha_pickle
        self.mcra_refpkg.slurp()
        self.puha_refpkg.slurp()

        return

    def tearDown(self) -> None:
        if os.path.isdir(self.tmp_dir_path):
            shutil.rmtree(self.tmp_dir_path)
        return

    def test_refpkg_pattern(self):
        self.assertEqual(None, _RefPkgPattern.match(self.mcra_pickle))
        self.assertTrue(_RefPkgPattern.match(os.path.basename(self.mcra_pickle)))
        return

    def test_gather_refpkg_dirs(self):
        # Test on empty dir
        pickles = gather_refpkg_pickles(dir_path=self.tmp_dir_path + "**")
        self.assertEqual(0, len(pickles))
        # Test on dir with single reference package
        pickles = gather_refpkg_pickles(dir_path=os.path.join(self.xmoa_dir, "XmoA_seed", "**"))
        self.assertEqual(1, len(pickles))
        # Test on root directory
        pickles = gather_refpkg_pickles()
        self.assertTrue(len(pickles) > 1)

    def test_instantiate_refpkgs(self):
        return

    def test_validate_treesapp_refpkg_dir(self):
        with self.assertRaises(AssertionError):
            validate_treesapp_refpkg_dir(self.tmp_dir_path)
        self.assertFalse(validate_treesapp_refpkg_dir(treesapp_dir=self.xmoa_dir))
        return

    def test_filter_refpkgs_by_name(self):
        test_refpkg_list = [self.mcra_refpkg, self.puha_refpkg]
        filter_refpkgs_by_name(ref_packages=test_refpkg_list, names="McrA")
        self.assertEqual(1, len(test_refpkg_list))
        return

    def test_clean_out_create_dir(self):
        os.mkdir(self.tmp_dir_path)
        clean_out_create_dir(self.tmp_dir_path)
        self.assertFalse(os.path.isdir(self.tmp_dir_path))
        return


def get_arguments(sys_args):
    parser = argparse.ArgumentParser(description="refpkg_manager.py is a script that allows users to integrate "
                                                 "all reference packages stored in this repository into a TreeSAPP "
                                                 "installation directory.")
    cg = parser.add_argument_group("Compute cluster commands")
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
    parser.add_argument("-o", "--output_dir", default="./temp_refpkg_dir/", required=False,
                        help="Path of directory to write output files. [ DEFAULT = ./temp_refpkg_dir/ ]")

    parser.add_argument("--update", required=False, default=False, action="store_true",
                        help="Updates reference packages specified by the user with --name parameter.")
    parser.add_argument("--copy", default=False, action="store_true",
                        help="Copies the reference packages specified (all by default) to a directory.")
    parser.add_argument("--threads", default=2, type=int,
                        help="Number of threads to use when rebuilding the reference package(s). [ DEFAULT = 2 ]")

    cg.add_argument("--template", required=False, default=None,
                    help="A template file containing scheduler-specific arguments."
                         " The 'treesapp create' command will be written beneath in a new file.")
    cg.add_argument("--scheduler", default="slurm", choices=["slurm"],
                    help="The system's scheduling software determines the template format. [ DEFAULT = slurm ]")

    return parser.parse_args(sys_args)


def gather_refpkg_pickles(dir_path="**/final_outputs/") -> list:
    refpkg_files = []
    for final_dir in glob.iglob(dir_path, recursive=True):
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
    logging.info("Instantiating reference packages... ")
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
    logging.info("done.\n")

    return ref_packages


def list_refpkgs(ref_packages: list) -> None:
    """
    Prints the 'prefix' attribute for each ReferencePackage instance in ref_packages to the logging.info stream

    :param ref_packages: A list of ts_refpkg.ReferencePackage instances
    :return: None
    """
    logging.info("Listing reference package summaries:\n")

    refpkg_summary_str = "\t".join(["Name", "Code-name",
                                    "Molecule", "Tree builder", "RefPkg-type", "Leaf nodes",
                                    "Description", "Created", "Last-updated"]) + "\n"

    for refpkg in sorted(ref_packages, key=lambda x: x.prefix):  # type: ts_refpkg.ReferencePackage
        refpkg_summary_str += "\t".join([refpkg.prefix, refpkg.refpkg_code,
                                         refpkg.molecule, refpkg.tree_tool, refpkg.kind, str(refpkg.num_seqs),
                                         refpkg.description, refpkg.date, refpkg.update]) + "\n"
    logging.info(refpkg_summary_str)

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


def create_command_validator(command_list: list):
    arguments_to_check = ["--accession2taxid", "-a", "--accession2lin", "--seqs2lineage", "--profile"]
    for arg in arguments_to_check:
        try:
            i = command_list.index(arg)
            arg_file = command_list[i+1]
            if not os.path.isfile(arg_file):
                logging.warning("File '{}' was not found, unable to use argument {}.\n".format(arg_file, arg))
                command_list.pop(i+1)
                command_list.pop(i)
        except ValueError:
            continue

    stage_param = "--stage"
    if stage_param in command_list:
        i = command_list.index(stage_param)
        stage_name = command_list.pop(i+1)
        command_list.pop(i)
        logging.info("Removing '{} {}' from treesapp create command.\n".format(stage_param, stage_name))

    if "--overwrite" not in command_list:
        command_list.append("--overwrite")

    return


def build_templates(ref_packages: list, template: str, scheduler: str, n_proc=4) -> None:
    """
    Automatically generate scripts for launching treesapp create with popular job scheduling systems.

    :param scheduler: Name of the computer cluster's scheduler
    :param template: Path to a file containing scheduler arguments. New commands will be appended to this file
    :param ref_packages: The list of ReferencePackage instances to rebuild
    :param n_proc: The number of parallel processes to use on the grid system
    :return: None
    """
    with open(template, 'r') as template_handler:
        jobscript_lines = template_handler.readlines()

    if scheduler == "slurm":
        jobscript_lines.append("\n")
        jobscript_lines.append("srun -n 1 {} ".format(n_proc))
    else:
        logging.error("Unknown scheduler provided. Unable to write template file.\n")
        sys.exit(3)

    for refpkg in ref_packages:  # type: ts_refpkg.ReferencePackage
        # Parse the treesapp create command from each reference package
        create_params = refpkg.cmd.split()
        # Correct a treesapp create command based on the presence/absence of file paths
        create_command_validator(create_params)

        if create_params[0:2] != ["treesapp", "create"]:
            create_params = ["treesapp", "create"] + create_params

        output_file = refpkg.prefix + '_' + scheduler + '.txt'
        try:
            output_handler = open(output_file, 'w')
        except IOError:
            logging.error("Unable to open '{}' for writing.\n".format(output_file))
            sys.exit(3)

        output_handler.write(''.join(jobscript_lines))
        output_handler.write(' '.join(create_params) + "\n")
        output_handler.close()

    return


def clean_out_create_dir(ts_dir: str) -> None:
    """
    A function designed for removing files and directories specific to treesapp create outputs from a directory.
    Just don't want any catastrophes, okay?

    :return: None
    """
    ts_dirs = ["intermediates", "final_outputs"]
    ts_files = glob.glob(os.path.join(ts_dir, "*_log.txt"))
    if os.path.isdir(ts_dir):
        for dir_name in ts_dirs:
            if os.path.isdir(os.path.join(ts_dir, dir_name)):
                shutil.rmtree(os.path.join(ts_dir, dir_name))
    for fname in ts_files:
        os.remove(fname)
    os.rmdir(ts_dir)
    return


def preserve_pickled_things(refpkg: ts_refpkg.ReferencePackage, replacement_refpkg) -> None:
    # Include the previous refpkg code and description before the update
    preserved_attributes = {attr: None for attr in ["refpkg_code", "description"]}
    for attr in preserved_attributes:
        preserved_attributes[attr] = refpkg.__dict__[attr]

    refpkg.f__json = replacement_refpkg
    refpkg.slurp()

    # Swap the default refpkg attributes with the preserved values
    for attr in preserved_attributes:
        refpkg.__dict__[attr] = preserved_attributes[attr]
    refpkg.pickle_package()

    return


def rebuild_gather_reference_packages(ref_packages: list, output_dir: str) -> None:
    """
    Attempts to rebuild every reference package in ref_packages by running treesapp create.
    It uses the command in the ReferencePackage.cmd attribute to pull all the parameters needed.

    The original treesapp create outputs are overwritten and this is ensured by including the '--overwrite' flag

    :param ref_packages: A list of ReferencePackage instances
    :param output_dir: Path to a directory for writing outputs
    :return: None
    """
    for refpkg in ref_packages:  # type: ts_refpkg.ReferencePackage
        # Parse the treesapp create command from each reference package
        create_cmd_str = re.sub(r"^treesapp create ", '', refpkg.cmd)
        create_params = create_cmd_str.split()
        create_command_validator(create_params)

        # Find the path of the output
        if "--output" in create_params:
            rebuild_path = create_params[create_params.index("--output") + 1]
        elif "-o" in create_params:
            rebuild_path = create_params[create_params.index("-o") + 1]
        else:
            logging.error("Unable to find the output path (with neither '-o' nor '--output') "
                          "in treesapp create command used for '{}'\n".format(refpkg.prefix))
            sys.exit(3)

        # Save the original treesapp create output directory in case of failure
        rebuild_path = rebuild_path.rstrip(os.sep)
        temp_refpkg_path = os.path.join(output_dir, os.path.split(rebuild_path)[-1])
        if os.path.exists(temp_refpkg_path):
            logging.warning("Directory '{}' is not empty and will be overwritten. "
                            "Cancel within 5 seconds to stop... ".format(temp_refpkg_path))
            sleep(5)
            shutil.rmtree(temp_refpkg_path)
        shutil.copytree(rebuild_path, temp_refpkg_path)

        if not os.path.isdir(temp_refpkg_path):
            logging.error("Copying previous treesapp create outputs failed. "
                          "Temporary directory {} doesn't exist.".format(temp_refpkg_path))
            sys.exit(5)
        else:
            clean_out_create_dir(rebuild_path)

        # Attempt to rebuild
        try:
            # Run treesapp create with each reference package's command
            create(create_params)
        except:
            logging.warning("treesapp create was unable to rebuild '{}'."
                            " The original outputs are being restored.\n".format(refpkg.prefix))
            clean_out_create_dir(rebuild_path)
            shutil.copytree(temp_refpkg_path, rebuild_path)

        preserve_pickled_things(refpkg,
                                os.path.join(rebuild_path, "final_outputs", refpkg.prefix + refpkg.refpkg_suffix))

        # Remove the saved treesapp create outputs
        shutil.rmtree(temp_refpkg_path)

    return


def validate_treesapp_refpkg_dir(treesapp_dir: str) -> bool:
    if not os.path.isdir(treesapp_dir):
        logging.error("Sorry human, '{}' isn't a directory. Better luck next time.\n".format(treesapp_dir))
        raise AssertionError

    if os.sep == treesapp_dir[-1]:
        treesapp_dir = treesapp_dir[:-1]

    # Detect whether the directory is a beneath a TreeSAPP installation or just a plain directory
    base, dir1 = os.path.split(treesapp_dir)
    if dir1 == "data":
        base, dir2 = os.path.split(base)
        if dir2 == "treesapp":
            logging.info("Copying reference packages into TreeSAPP installation directory\n")
            return True
    logging.info("Copying reference packages into custom directory location\n")
    return False


def copy_refpkg_files_to_treesapp(ref_packages: list, refpkg_repository: str) -> None:
    """
    After building or rebuilding reference packages in the RefPkgs repository, users may want to copy the pickle files
    (e.g. PuhA_build.pkl) to either a TreeSAPP installation directory or another directory where they're keeping pkl
    files for their analyses.
    This function facilitates copying, without the user have to find the paths and copy everything - they just need to
    provide the ReferencePackage.prefix values for the reference packages they want to copy.

    :param ref_packages: A list of ReferencePackage instances with f__json attributes
    :param refpkg_repository: Path to a directory where the reference packages are to be copied.
     All instances in ref_packages will be copied.
    :return: None
    """
    # Ensure the directory exists
    validate_treesapp_refpkg_dir(refpkg_repository)

    for refpkg in ref_packages:  # type: ts_refpkg.ReferencePackage
        shutil.copy(refpkg.f__json, refpkg_repository)
    return


def manage_refpkgs(sys_args):
    args = get_arguments(sys_args)
    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)

    prep_logging(log_file_name=os.path.join(args.output_dir,
                                            "log_refpkg_manager_" + dt.now().strftime("%Y-%m-%d") + ".txt"),
                 verbosity=False)

    refpkg_pickles = gather_refpkg_pickles()
    ref_packages = instantiate_refpkgs(refpkg_pickles)

    logging.info("Reference package pickles found:\n" +
                 "\t" + "\n\t".join([refpkg.prefix + ": " + refpkg.f__json for
                                     refpkg in sorted(ref_packages, key=lambda x: x.prefix)]) + "\n")

    # TODO: Differentiate reference packages found in directories made by treesapp update
    if args.list:
        list_refpkgs(ref_packages)
        return
    if args.name:
        filter_refpkgs_by_name(ref_packages, args.name)

    if args.template:
        build_templates(ref_packages, scheduler=args.scheduler, template=args.template)

    if args.update:
        rebuild_gather_reference_packages(ref_packages, args.output_dir)

    if args.copy:
        # Copy reference package pickle files
        if not args.treesapp_install:
            logging.error("TreeSAPP installation directory was not provided. Not sure where to copy the refpkgs!\n")
            return
        copy_refpkg_files_to_treesapp(ref_packages, args.treesapp_install)

    return


if __name__ == "__main__":
    # unittest.main()
    manage_refpkgs(sys.argv[1:])
