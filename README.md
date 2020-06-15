# RefPkgs

Welcome to the repository for reference packages (refpkgs)!

This project is dependent on [TreeSAPP](https://github.com/hallamlab/TreeSAPP), 
a tool for annotating taxonomic and functional anchor genes in genomes and proteins using phylogenetic placement.
By the same token, TreeSAPP is dependent on RefPkgs as these hold the components essential to sequence annotation:

1. A multiple sequence alignment (FASTA)
2. A profile HMM
3. A phylogenetic tree (Newick)
4. Map between sequence name and taxonomic lineage

In the subdirectories there are many reference packages that are ready to be used for classification by TreeSAPP.
These are broadly, and arbitrarily, broken down into the pathways the reference packages are involved in.
To view all available reference packages first clone the repository locally then use  `integrate_refpkgs.py`.

```shell script
git clone https://github.com/hallamlab/RefPkgs.git
cd RefPkgs
./integrate_refpkgs.py -l
```

Please run `./integrate_refpkgs.py -h` to view the options available to you.

**NOTE**: TreeSAPP does need to be installed for this to work.

If you are interested in building a new reference package and depositing it here for everyone to use,
please read our [contributing](https://github.com/hallamlab/RefPkgs/CONTRIBUTING.md) guide on how to best do this.
