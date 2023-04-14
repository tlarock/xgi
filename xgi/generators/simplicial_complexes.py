"""Generators for some simplicial complexes.

All the functions in this module return a SimplicialComplex class.

"""

import random
from collections import defaultdict
from itertools import combinations

import networkx as nx
import numpy as np
from scipy.special import comb

from ..classes import SimplicialComplex
from ..classes.function import subfaces
from ..utils.utilities import find_triangles

__all__ = [
    "random_simplicial_complex",
    "random_flag_complex_d2",
    "random_flag_complex",
    "flag_complex",
    "flag_complex_d2",
]


def random_simplicial_complex(N, ps, seed=None):
    """Generates a random hypergraph

    Generate N nodes, and connect any d+1 nodes
    by a simplex with probability ps[d-1]. For each simplex,
    add all its subfaces if they do not already exist.

    Parameters
    ----------
    N : int
        Number of nodes
    ps : list of float
        List of probabilities (between 0 and 1) to create a
        hyperedge at each order d between any d+1 nodes. For example,
        ps[0] is the wiring probability of any edge (2 nodes), ps[1]
        of any triangles (3 nodes).
    seed : int or None (default)
        The seed for the random number generator

    Returns
    -------
    Simplicialcomplex object
        The generated simplicial complex

    References
    ----------
    Described as 'random simplicial complex' in
    "Simplicial Models of Social Contagion", Nature Communications 10(1), 2485,
    by I. Iacopini, G. Petri, A. Barrat & V. Latora (2019).
    https://doi.org/10.1038/s41467-019-10431-6

    Example
    -------
    >>> import xgi
    >>> H = xgi.random_simplicial_complex(20, [0.1, 0.01])

    """

    if seed is not None:
        np.random.seed(seed)

    if (np.any(np.array(ps) < 0)) or (np.any(np.array(ps) > 1)):
        raise ValueError("All elements of ps must be between 0 and 1 included.")

    nodes = range(N)
    simplices = []

    for i, p in enumerate(ps):
        d = i + 1  # order, ps[0] is prob of edges (d=1)

        potential_simplices = combinations(nodes, d + 1)
        n_comb = comb(N, d + 1, exact=True)
        mask = np.random.random(size=n_comb) <= p  # True if simplex to keep

        simplices_to_add = [e for e, val in zip(potential_simplices, mask) if val]

        simplices += simplices_to_add

    S = SimplicialComplex()
    S.add_nodes_from(nodes)
    S.add_simplices_from(simplices)

    return S


def flag_complex(G, max_order=2, ps=None, seed=None):
    """Generate a flag (or clique) complex from a
    NetworkX graph by filling all cliques up to dimension max_order.

    Parameters
    ----------
    G : Networkx Graph

    max_order : int
        maximal dimension of simplices to add to the output simplicial complex
    ps: list of float
        List of probabilities (between 0 and 1) to create a
        hyperedge from a clique, at each order d. For example,
        ps[0] is the probability of promoting any 3-node clique (triangle) to
        a 3-hyperedge.
    seed: int or None (default)
        The seed for the random number generator

    Returns
    -------
    S : SimplicialComplex

    Notes
    -----
    Computing all cliques quickly becomes heavy for large networks. `flag_complex_d2`
    is faster to compute up to order 2.

    See also
    --------
    flag_complex_d2

    """
    # This import needs to happen when this function is called, not when it is
    # defined.  Otherwise, a circular import error would happen.
    from ..classes import SimplicialComplex

    if seed is not None:
        random.seed(seed)

    nodes = G.nodes()
    edges = G.edges()

    # compute all maximal cliques to fill
    max_cliques = list(nx.find_cliques(G))

    S = SimplicialComplex()
    S.add_nodes_from(nodes)
    S.add_simplices_from(edges)
    if not ps:  # promote all cliques
        S.add_simplices_from(max_cliques, max_order=max_order)
        return S

    if max_order:  # compute subfaces of order max_order (allowed max cliques)
        max_cliques_to_add = subfaces(max_cliques, order=max_order)
    else:
        max_cliques_to_add = max_cliques

    # store max cliques per order
    cliques_d = defaultdict(list)
    for x in max_cliques_to_add:
        cliques_d[len(x)].append(x)

    # promote cliques with a given probability
    for i, p in enumerate(ps[: max_order - 1]):
        d = i + 2  # simplex order
        cliques_d_to_add = [el for el in cliques_d[d + 1] if random.random() <= p]
        S.add_simplices_from(cliques_d_to_add, max_order=max_order)

    return S


def flag_complex_d2(G, p2=None, seed=None):
    """Generate a flag (or clique) complex from a
    NetworkX graph by filling all cliques up to dimension 2.

    Parameters
    ----------
    G : networkx Graph
        Graph to consider
    p2: float
        Probability (between 0 and 1) of filling empty triangles in graph G
    seed: int or None (default)
        The seed for the random number generator

    Returns
    -------
    S : xgi.SimplicialComplex

    Notes
    -----
    Computing all cliques quickly becomes heavy for large networks. This
    is faster than `flag_complex` to compute up to order 2.

    See also
    --------
    flag_complex
    """
    # This import needs to happen when this function is called, not when it is
    # defined.  Otherwise, a circular import error would happen.
    from ..classes import SimplicialComplex

    if seed is not None:
        random.seed(seed)

    nodes = G.nodes()
    edges = G.edges()

    S = SimplicialComplex()
    S.add_nodes_from(nodes)
    S.add_simplices_from(edges)

    triangles_empty = find_triangles(G)

    if p2 is not None:
        triangles = [el for el in triangles_empty if random.random() <= p2]
    else:
        triangles = triangles_empty

    S.add_simplices_from(triangles)

    return S


def random_flag_complex_d2(N, p, seed=None):
    """Generate a maximal simplicial complex (up to order 2) from a
    :math:`G_{N,p}` Erdős-Rényi random graph by filling all empty triangles with 2-simplices.

    Parameters
    ----------
    N : int
        Number of nodes
    p : float
        Probabilities (between 0 and 1) to create an edge
        between any 2 nodes
    seed : int or None (default)
        The seed for the random number generator

    Returns
    -------
    SimplicialComplex

    Notes
    -----
    Computing all cliques quickly becomes heavy for large networks.
    """
    if seed is not None:
        random.seed(seed)

    if (p < 0) or (p > 1):
        raise ValueError("p must be between 0 and 1 included.")

    G = nx.fast_gnp_random_graph(N, p, seed=seed)

    return flag_complex_d2(G)


def random_flag_complex(N, p, max_order=2, seed=None):
    """Generate a flag (or clique) complex from a
    :math:`G_{N,p}` Erdős-Rényi random graph by filling all cliques up to dimension max_order.

    Parameters
    ----------
    N : int
        Number of nodes
    p : float
        Probability (between 0 and 1) to create an edge
        between any 2 nodes
    max_order : int
        maximal dimension of simplices to add to the output simplicial complex
    seed : int or None (default)
        The seed for the random number generator

    Returns
    -------
    SimplicialComplex

    Notes
    -----
    Computing all cliques quickly becomes heavy for large networks.
    """

    if (p < 0) or (p > 1):
        raise ValueError("p must be between 0 and 1 included.")

    G = nx.fast_gnp_random_graph(N, p, seed=seed)

    nodes = G.nodes()
    edges = list(G.edges())

    # compute all triangles to fill
    max_cliques = list(nx.find_cliques(G))

    S = SimplicialComplex()
    S.add_nodes_from(nodes)
    S.add_simplices_from(max_cliques, max_order=max_order)

    return S