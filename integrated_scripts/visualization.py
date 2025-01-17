import pandas as pd
import matplotlib.pyplot as plt
from pyvis.network import Network
from IPython.display import display, HTML, IFrame
import os

def post_analysis_visualization(post_sentiment_results):
    """
    Visualize the sentiment analysis results for pull requests (PRs), issues, and other entities.

    Parameters:
        post_sentiment_results (pd.DataFrame): DataFrame containing sentiment analysis results with columns
                                                'sentiment' and 'type' (e.g., 'PR' or 'Issue').

    Returns:
        None
    """
    
    # Group the sentiment analysis results by sentiment and type, and fill missing values with 0
    sentiment_counts = post_sentiment_results.groupby(['sentiment', 'type']).size().unstack(fill_value=0)
    sentiment_counts = sentiment_counts.reindex(['POS', 'NEU', 'NEG'])
    
    # Plot the data as a bar chart with color distinction for each type
    sentiment_counts.plot(kind='bar', stacked=False, color=['blue', 'orange', 'gray'])
    
    # Customize the chart's title, labels, and legend
    plt.title('Sentiment Analysis for PRs, Issues, and MLs')
    plt.xlabel('Sentiment')
    plt.ylabel('Count')
    plt.xticks(rotation=0)
    plt.legend(title='Type', loc='upper right')
    plt.show()


def generate_network(source_path, user_interaction_df, file_name='network_graph.html', number_of_interactions=0):
    """
    Generate and visualize a network of user interactions based on sentiment analysis.

    Parameters:
        source_path (str):                  Path to save the generated network graph HTML file.
        user_interaction_df (pd.DataFrame): DataFrame containing user interactions, including 'from', 'to',
                                            'positive', 'neutral', and 'negative' columns.
        file_name (str):                    Name of the HTML file to save the network graph.
        number_of_interactions (int):       Minimum number of interactions between users to include in the graph.

    Returns:
        output_path: Path to the saved HTML file of the network graph.
    """
    
    print(f"Generating network graph with user interactions...")

    # Initialize the PyVis network with specific physics settings for optimal visualization
    net = Network(height='750px', width='100%', notebook=True, directed=True)
    net.barnes_hut(gravity=-10000, central_gravity=0.3, spring_length=150, spring_strength=0.01)

    # Filter the DataFrame to include only interactions above a specified number
    user_interaction_df = user_interaction_df[
        (user_interaction_df['positive'].apply(len) + 
         user_interaction_df['neutral'].apply(len) + 
         user_interaction_df['negative'].apply(len)) > number_of_interactions
    ]
    
    # Add nodes to the network for each unique author
    authors = pd.concat([user_interaction_df['from'], user_interaction_df['to']]).unique()
    for author in authors:
        net.add_node(author, label=author, title=author)
    
    # Add edges representing interactions between users, with weights and colors based on sentiment
    for _, row in user_interaction_df.iterrows():
        weight = len(row['positive']) + len(row['neutral']) + len(row['negative'])
        source = row['from']
        target = row['to']

        # Initialize counters for calculating the average sentiment score
        total_sentiment_score = 0
        message_count = 0

        # Loop over all messages to calculate total sentiment score and message count
        for message_data in row['positive'] + row['negative'] + row['neutral']:
            total_sentiment_score += message_data['score']
            message_count += 1

        # Calculate the average sentiment score for the interaction
        avg_sentiment_score = total_sentiment_score / message_count if message_count > 0 else 0
        
        # Set the edge color based on average sentiment score
        if avg_sentiment_score >= 0.2:
            color = '#0624FF'  # Positive sentiment color
        elif avg_sentiment_score <= -0.2:
            color = '#f7b500'  # Negative sentiment color
        else:
            color = '#808080'  # Neutral sentiment color
    
        # Add an edge to the network graph with weight, color, and interaction details
        net.add_edge(
            source, target, value=weight,
            title=f"Pos: {len(row['positive'])}, Neu: {len(row['neutral'])}, Neg: {len(row['negative'])}, Score: {avg_sentiment_score:.3f}",
            color=color
        )

    # Save the generated network to an HTML file
    output_path = os.path.join(source_path, file_name)
    net.save_graph(output_path)
    print(f"Network saved to {output_path}")
    print("----------------------------------------------")
    
    # Return the path of the saved network graph
    return output_path


def show_graph(output_path):
    """
    Display the generated PyVis network graph within a Jupyter notebook.

    Parameters:
        output_path (str): Path to the HTML file containing the network graph.

    Returns:
        None
    """
    
    # Check if the specified file path exists
    if os.path.exists(output_path):
        # Display the HTML graph in an iframe for in-notebook visualization
        display(IFrame(output_path, width='100%', height='750px'))
    else:
        print(f"Error: {output_path} does not exist.")
