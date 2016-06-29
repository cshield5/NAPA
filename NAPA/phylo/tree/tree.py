from ete2 import PhyloTree


def load_tree_sequences(nwk_file, fasta_file):
    ''' Load a tree with associated sequences on leaves. '''
    tree = PhyloTree(newick = nwk_file, format = 1)
    tree.link_to_alignment(alignment = fasta_file, alg_format = 'fasta')
    return tree


def filter_leaves(tree, node_name_list):
    if not len(node_name_list):
        return tree.get_leaves() # no filtering -- all leaves returned
    return filter(lambda node: node.name in node_name_list, tree.get_leaves())
    
def get_mrca(tree, nodes):
    return tree.get_common_ancestor(nodes)

def get_mrca_leaf_names(tree, node_name_list):
    node_subset = filter_leaves(tree, node_name_list)
    return get_mrca(tree, node_subset)

def get_ancestor_to_node_mutation_set(tree, anc_seq, node_list): 
