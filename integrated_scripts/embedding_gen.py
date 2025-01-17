from karateclub import Graph2Vec
import networkx as nx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import node2vec


def create_graphs_from_interactions(user_interaction_df):
    """
    Converts the user interaction DataFrame into a list of NetworkX directed graphs.
    
    Parameters:
        user_interaction_df (pd.DataFrame): DataFrame containing 'from', 'to', 'positive', 'neutral', and 'negative' columns.

    Returns:
        List of NetworkX graphs.
    """

    # create a single directed graph for the given user interactions
    G = nx.DiGraph()
    for _, row in user_interaction_df.iterrows():
        source = row['from']
        target = row['to']
        weight = len(row['positive']) + len(row['neutral']) + len(row['negative'])

        total_sentiment_score = 0
        message_count = 0

        # compute the total sentiment score and count of messages
        for message_data in row['positive'] + row['negative'] + row['neutral']:
            total_sentiment_score += message_data['score']
            message_count += 1
        
        # calculate average sentiment score
        avg_sentiment_score = total_sentiment_score / message_count if message_count > 0 else 0

        # add edge
        G.add_edge(source, target, weight=weight, sentiment_score=avg_sentiment_score)
    
    return [G]

def compute_graph_embeddings(graph):
    """
    Compute graph embeddings using Graph2Vec while preserving the original node names.

    Parameters:
        graph (list of NetworkX graphs): List of NetworkX graphs to compute embeddings for.

    Returns:
        np.ndarray: Graph embeddings as a 2D numpy array.
        dict: Mapping of original node names to numeric labels.
        dict: Mapping of numeric labels back to original node names.
    """
    # create mapping of original node names to node index
    original_names = list(graph[0].nodes())
    node_to_int = {name: i for i, name in enumerate(original_names)}
    int_to_node = {i: name for i, name in enumerate(original_names)}

    # convert node labels to integers
    graph[0] = nx.relabel_nodes(graph[0], node_to_int)

    # get graph embeddings using Graph2Vec
    model = Graph2Vec(dimensions=128, wl_iterations=2)
    model.fit(graph)

    embeddings = model.get_embedding()
    return embeddings, node_to_int, int_to_node




def calculate_node_embeddings(graph, dimensions=64, walk_length=30, num_walks=200):
    """
    Calculates node embeddings using Node2Vec.

    Parameters:
        graph (NetworkX Graph): Input graph.
        dimensions (int): Number of dimensions for embeddings.
        walk_length (int): Length of random walks.
        num_walks (int): Number of random walks per node.

    Returns:
        dict: A mapping of node names to their embeddings.
    """
    # run Node2Vec to generate node embeddings
    node2vec = Node2Vec(graph, dimensions=dimensions, walk_length=walk_length, num_walks=num_walks, weight_key='weight')
    model = node2vec.fit()

    # extract embeddings as a dictionary {node: embedding}
    node_embeddings = {node: model.wv[node] for node in graph.nodes()}
    return node_embeddings



def cluster_node_embeddings(node_embeddings, clusters=3):
    """
    Perform clustering on node embeddings.

    Parameters:
        node_embeddings (dict): A dictionary of node embeddings {node: embedding}.
        clusters (int): Number of clusters for KMeans.

    Returns:
        dict: A mapping of nodes to their cluster labels.
    """
    # data prep for clustering
    node_list = list(node_embeddings.keys())
    embeddings = list(node_embeddings.values())

    # perform KMeans clustering
    kmeans = KMeans(n_clusters=clusters, random_state=42)
    labels = kmeans.fit_predict(embeddings)

    # map nodes to their cluster labels
    node_clusters = {node: label for node, label in zip(node_list, labels)}
    return node_clusters, embeddings, labels, node_list

def visualize_clusters(embeddings, labels, node_list, int_to_node=None):
    """
    Visualize clusters using t-SNE for dimensionality reduction with original node names.

    Parameters:
        embeddings (list): Node embeddings.
        labels (list): Cluster labels for each node.
        node_list (list): List of original node names (not indices).
        int_to_node (dict): Mapping of numeric node labels back to original names.
    """

    # convert embeddings to a NumPy array
    embeddings = np.array(embeddings)

    # reduce dimensionality for visualization
    tsne = TSNE(n_components=2, random_state=42)
    reduced_embeddings = tsne.fit_transform(embeddings)

    # plot the embeddings with cluster colors
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(
        reduced_embeddings[:, 0],
        reduced_embeddings[:, 1],
        c=labels,
        cmap='viridis',
        s=100,
        alpha=0.8
    )

    # add node labels (use original names if int_to_node is provided)
    for i, node in enumerate(node_list):
        label = int_to_node[node] if int_to_node else str(node)
        plt.text(reduced_embeddings[i, 0], reduced_embeddings[i, 1], label, fontsize=8, alpha=0.9)

    plt.colorbar(scatter, label='Cluster')
    plt.title("Node Clusters (t-SNE Visualization of Embeddings)")
    plt.show()
