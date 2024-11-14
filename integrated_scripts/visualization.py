import pandas as pd
import matplotlib.pyplot as plt
from pyvis.network import Network
from IPython.display import display, HTML, IFrame
import os

def post_analysis_visualization(post_sentiment_results):
    # Count the number of each sentiment type for PRs and Issues
    sentiment_counts = post_sentiment_results.groupby(['sentiment', 'type']).size().unstack(fill_value=0)
    
    # Reorder the rows to have the desired order: positive, neutral, negative
    sentiment_counts = sentiment_counts.reindex(['POS', 'NEU', 'NEG'])
    
    # Plotting the data
    sentiment_counts.plot(kind='bar', stacked=False, color=['blue', 'orange', 'gray'])
    
    plt.title('Sentiment Analysis for PRs, Issues, and MLs')
    plt.xlabel('Sentiment')
    plt.ylabel('Count')
    plt.xticks(rotation=0)
    plt.legend(title='Type', loc='upper right')
    plt.show()

def generate_network(source_path, user_interaction_df, file_name='network_graph.html', number_of_interactions=0):
    # Initialize the pyvis Network with tuned physics to balance clustering and spreading
    net = Network(height='750px', width='100%', notebook=True, directed=True)
    net.barnes_hut(gravity=-10000, central_gravity=0.3, spring_length=150, spring_strength=0.01)

    # Filter the DataFrame based on the number of interactions
    user_interaction_df = user_interaction_df[
        (user_interaction_df['positive'].apply(len) + 
         user_interaction_df['neutral'].apply(len) + 
         user_interaction_df['negative'].apply(len)) > number_of_interactions
    ]
    
    # Add nodes for each unique author
    authors = pd.concat([user_interaction_df['from'], user_interaction_df['to']]).unique()
    for author in authors:
        net.add_node(author, label=author, title=author)
    
    
    
    # Add edges for each interaction
    for _, row in user_interaction_df.iterrows():
        weight = len(row['positive']) + len(row['neutral']) + len(row['negative'])
        source = row['from']
        target = row['to']

        # Initialize counters for the total score and number of messages
        total_sentiment_score = 0
        message_count = 0

        # Combine loops to calculate the total score and count messages
        for message_data in row['positive'] + row['negative'] + row['neutral']:
            total_sentiment_score += message_data['score']
            message_count += 1

        # Calculate the average sentiment score
        avg_sentiment_score = total_sentiment_score / message_count if message_count > 0 else 0
        
        # Determine the color based on sentiment using interpolation
        if avg_sentiment_score >= 0.2:
            color = '#0624FF'
        elif avg_sentiment_score <= -0.2:
            color = '#f7b500'
        else:
            color = '#808080'
    
        # Add an edge from source to target with weight and custom color
        net.add_edge(source, target, value=weight, title=f"Pos: {len(row['positive'])}, Neu: {len(row['neutral'])}, Neg: {len(row['negative'])}, Score: {avg_sentiment_score:.3f}", color=color)

    output_path = os.path.join(source_path, file_name)
    net.save_graph(output_path)
    print(f"Network saved to {output_path}")
    
    # Show the network
    return output_path


def show_graph(output_path):
    """Displays the PyVis network graph inside a Jupyter notebook."""
    # Check if the file exists
    if os.path.exists(output_path):
        # Display the HTML graph using IFrame for proper rendering
        display(IFrame(output_path, width='100%', height='750px'))
    else:
        print(f"Error: {output_path} does not exist.")
