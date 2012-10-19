import networkx as nx

G=nx.path_graph(1800)

h = (nx.pagerank_scipy(G,max_iter=300, tol=1e-08))

print(h)