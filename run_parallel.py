import argparse, sys, os
import subprocess as sp

"""
Run all of the steps through plotting the K selection plot of cNMF sequentially using GNU
parallel to run the factorization steps in parallel. The same optional arguments are available
as for running the individual steps of cnmf.py

Example command:
python run_parallel.py --output-dir $output_dir \
            --name test --counts path_to_counts.df.npz \
            -k 6 7 8 9 --n-iter 5 --total-workers 2 \
            --seed 5
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--name",
        type=str,
        help="[all] Name for this analysis. All output will be placed in [output-dir]/[name]/...",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="[all] Output directory. All output will be placed in [output-dir]/[name]/...",
        nargs="?",
    )
    parser.add_argument(
        "-c",
        "--counts",
        type=str,
        help="[prepare] Input counts in cell x gene matrix as df.npz or tab separated txt file",
    )
    parser.add_argument(
        "-k",
        "--components",
        type=int,
        help='[prepare] Numper of components (k) for matrix factorization. Several can be specified with "-k 8 9 10"',
        nargs="+",
        default=[10],
    )
    parser.add_argument(
        "-n",
        "--n-iter",
        type=int,
        help="[prepare] Numper of iteration for each factorization",
        default=100,
    )
    parser.add_argument(
        "--total-workers",
        type=int,
        help="[all] Total workers that are working together.",
        default=1,
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="[prepare] Master seed for generating the seed list.",
        default=18,
    )
    parser.add_argument(
        "--numgenes",
        type=int,
        help="[prepare] Number of high variance genes to use for matrix factorization.",
        default=None,
    )
    parser.add_argument(
        "--genes-file",
        type=str,
        help="[prepare] File containing a list of genes to include, one gene per line. Must match column labels of counts matrix.",
        default=None,
    )
    parser.add_argument(
        "--tpm",
        type=str,
        help="[prepare] Pre-computed TPM values as df.npz or tab separated txt file. Cell x Gene matrix. If none is provided, TPM will be calculated automatically. This can be helpful if a particular normalization is desired.",
        default=None,
    )
    parser.add_argument(
        "--subset",
        help="[prepare] AnnData.obs column name to subset on before performing NMF",
        nargs="*",
    )
    parser.add_argument(
        "--subset-val",
        dest="subset_val",
        help="[prepare] Value to match in AnnData.obs[args.subset]",
        nargs="*",
    )
    parser.add_argument(
        "-l",
        "--layer",
        type=str,
        default=None,
        help="[prepare] Key from .layers to use. Default '.X'.",
    )

    parser.add_argument(
        "--auto-k",
        help="[consensus] Automatically pick k value for consensus based on maximum \
            stability",
        action="store_true",
    )
    parser.add_argument(
        "--local-density-threshold",
        type=str,
        help="[consensus] Threshold for the local density filtering. This string must convert to a float >0 and <=2",
        default="0.5",
    )
    parser.add_argument(
        "--local-neighborhood-size",
        type=float,
        help="[consensus] Fraction of the number of replicates to use as nearest neighbors for local density filtering",
        default=0.30,
    )
    parser.add_argument(
        "--show-clustering",
        dest="show_clustering",
        help="[consensus] Produce a clustergram figure summarizing the spectra clustering",
        action="store_true",
    )
    parser.add_argument(
        "--cleanup",
        help="[consensus] Remove excess files after saving results to clean workspace",
        action="store_true",
    )

    # Collect args
    args = parser.parse_args()
    argdict = vars(args)

    # convert arguments from list to string for passing to cnmf.py
    argdict["components"] = " ".join([str(k) for k in argdict["components"]])
    if argdict["subset"]:
        argdict["subset"] = " ".join([str(k) for k in argdict["subset"]])
        argdict["subset_val"] = " ".join([str(k) for k in argdict["subset_val"]])

    # Directory containing cNMF and this script
    cnmfdir = os.path.dirname(sys.argv[0])
    if len(cnmfdir) == 0:
        cnmfdir = "."

    # Run prepare
    prepare_opts = [
        "--{} {}".format(k.replace("_", "-"), argdict[k])
        for k in argdict.keys()
        if argdict[k] is not None
    ]
    prepare_cmd = "python {}/cnmf.py prepare ".format(cnmfdir)
    prepare_cmd += " ".join(prepare_opts)
    print(prepare_cmd)
    sp.call(prepare_cmd, shell=True)

    # Run factorize
    workind = " ".join([str(x) for x in range(argdict["total_workers"])])
    factorize_cmd = (
        "nohup parallel python %s/cnmf.py factorize --output-dir %s --name %s --worker-index {} ::: %s"
        % (cnmfdir, argdict["output_dir"], argdict["name"], workind)
    )
    print(factorize_cmd)
    sp.call(factorize_cmd, shell=True)

    # Run combine
    combine_cmd = "python %s/cnmf.py combine --output-dir %s --name %s" % (
        cnmfdir,
        argdict["output_dir"],
        argdict["name"],
    )
    print(combine_cmd)
    sp.call(combine_cmd, shell=True)

    # Plot K selection
    Kselect_cmd = "python %s/cnmf.py k_selection_plot --output-dir %s --name %s" % (
        cnmfdir,
        argdict["output_dir"],
        argdict["name"],
    )
    print(Kselect_cmd)
    sp.call(Kselect_cmd, shell=True)

    # Delete individual iteration files
    clean_cmd = "rm %s/%s/cnmf_tmp/*.iter_*.df.npz" % (
        argdict["output_dir"],
        argdict["name"],
    )
    print(clean_cmd)
    sp.call(clean_cmd, shell=True)

    if argdict["auto_k"]:
        consensus_cmd = "python {}/cnmf.py consensus --output-dir {} --name {} --auto-k --local-density-threshold {}".format(
            cnmfdir,
            argdict["output_dir"],
            argdict["name"],
            argdict["local_density_threshold"],
        )
        if argdict["show_clustering"]:
            consensus_cmd = " ".join([consensus_cmd, "--show-clustering"])
        if argdict["cleanup"]:
            consensus_cmd = " ".join([consensus_cmd, "--cleanup"])
        print(consensus_cmd)
        sp.call(consensus_cmd, shell=True)


if __name__ == "__main__":
    main()
