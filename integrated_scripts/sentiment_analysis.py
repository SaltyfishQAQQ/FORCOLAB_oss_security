from pysentimiento import create_analyzer
import torch
import os
import pandas as pd
from collections import defaultdict
import data_cleaning as cleaner
import requests
import shutil
import github_fetching as fetcher
import re
import ast

# Load the sentiment analysis model
analyzer = create_analyzer(task = "sentiment", lang = "en")

def classify_pr_or_issue(filename):
    """
    Classify a file as a 'PR' or 'Issue' based on the filename.

    Parameters:
        filename (str): The name of the file.

    Returns:
        str: 'PR' if filename suggests a pull request, 'Issue' if it suggests an issue, or 'Unknown' if undetermined.
    """
    
    # Check if 'pr' or 'issue' appears in the filename to classify
    if 'pr' in filename.lower():
        return 'PR'
    elif 'issue' in filename.lower():
        return 'Issue'
    else:
        return 'Unknown'


def count_dataset(user_interactions):
    """
    Count and print the total number of author pairs and messages in a DataFrame.

    Parameters:
        user_interactions (pd.DataFrame): DataFrame containing user interactions.

    Returns:
        None
    """
    
    # Calculate the number of author pairs
    num_pairs = len(user_interactions)
    num_messages = 0
    
    # Count messages across sentiment columns
    for index, row in user_interactions.iterrows():
        num_messages += len(row['positive']) + len(row['negative']) + len(row['neutral'])
        
    print("Number of author pairs: " + str(num_pairs))
    print("Number of messages: " + str(num_messages))


def update_sentiment_tracker(sentiment_tracker, source_author, target_in_message, sentiment, sentiment_score, original_message, filename):
    """
    Update sentiment tracking for interactions between authors.

    Parameters:
        sentiment_tracker (dict):   Dictionary storing sentiment data.
        source_author (str):        Name of the source author.
        target_in_message (str):    Name of the target author mentioned.
        sentiment (str):            Sentiment category ('POS', 'NEU', or 'NEG').
        sentiment_score (float):    Score associated with the sentiment.
        original_message (str):     The message text.
        filename (str):             Name of the source file.

    Returns:
        None
    """
    
    # Append the sentiment details based on the sentiment type
    if sentiment == 'POS':
        sentiment_tracker[(source_author, target_in_message)]['POS'].append({
            'message': original_message,
            'score': sentiment_score,
            'file_name': filename
        })
    elif sentiment == 'NEU':
        sentiment_tracker[(source_author, target_in_message)]['NEU'].append({
            'message': original_message,
            'score': sentiment_score,
            'file_name': filename
        })
    elif sentiment == 'NEG':
        sentiment_tracker[(source_author, target_in_message)]['NEG'].append({
            'message': original_message,
            'score': sentiment_score,
            'file_name': filename
        })


def get_sentiment_score(sentiment_result):
    """
    Determine sentiment label and score based on sentiment probabilities.

    Parameters:
        sentiment_result (SentimentResult): Result object from sentiment analysis.

    Returns:
        sentiment, sentiment_score: Sentiment label ('POS', 'NEU', or 'NEG') and the sentiment score.
    """
    
    # Calculate sentiment score by combining positive and negative probabilities
    sentiment_score = sentiment_result.probas['POS']*1 + sentiment_result.probas['NEG']*(-1)
    sentiment = "NEU"
    
    # Determine sentiment label based on score threshold
    if sentiment_score > 0.2:
        sentiment = "POS"
    elif sentiment_score < -0.2:
        sentiment = "NEG"

    return sentiment, sentiment_score


def get_github_user_name(username, token=os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")):
    """
    Fetch the GitHub display name for a username via API.

    Parameters:
        username (str):     GitHub username.
        token (str):        GitHub access token.

    Returns:
        username: Display name if available, else the username itself.
    """
    
    # Define GitHub API URL and authorization headers
    url = f"https://api.github.com/users/{username}"
    headers = {"Authorization": f"token {token}"}
    
    # Send a GET request to the GitHub API to get user name
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get('name', username)
    else:
        return username


def clean_user_interactions(source_path, sentiment_tracker):
    """
    Clean user interactions by removing invalid or self-interactions and low contributors.

    Parameters:
        source_path (str):          Path to the source directory.
        sentiment_tracker (dict):   Dictionary storing sentiment interactions.

    Returns:
        user_interactions: DataFrame with cleaned user interactions.
    """
    
    # Initialize an empty list to store cleaned interactions
    result_list = []
    for (source_author, target_in_message), sentiments in sentiment_tracker.items():
        result_list.append({
            'from': source_author,
            'to': target_in_message,
            'positive': sentiments['POS'],
            'neutral': sentiments['NEU'],
            'negative': sentiments['NEG']
        })
    user_interactions = pd.DataFrame(result_list)

    # Set up a directory for deleted interactions
    directory = os.path.join(source_path, "deleted_user_interactions/")
    if not os.path.exists(directory):
        os.mkdir(directory)
    else:
        shutil.rmtree(directory)
        os.mkdir(directory)

    # Step 1: Remove invalid 'to' values and save removed records
    invalid_to = user_interactions[user_interactions['to'].isna()]
    user_interactions = user_interactions.dropna(subset=['to'])
    invalid_to.to_csv(os.path.join(directory, "removed_invalid_to.csv"), index=False)

    # Step 2: Remove self-interactions and save removed records
    self_interactions = user_interactions[user_interactions['from'] == user_interactions['to']]
    user_interactions = user_interactions[user_interactions['from'] != user_interactions['to']]
    self_interactions.to_csv(os.path.join(directory, "removed_self_interactions.csv"), index=False)

    # Step 3: Filter out rows with authors below the contribution threshold
    contribution_df = cleaner.calculate_author_contributions()
    threshold = contribution_df['count'].describe()['50%']
    authors_to_eliminate = contribution_df[contribution_df['count'] < threshold]['from']
    below_threshold_interactions = user_interactions[
        user_interactions['from'].isin(authors_to_eliminate) |
        user_interactions['to'].isin(authors_to_eliminate)
    ]
    user_interactions = user_interactions[
        ~user_interactions['from'].isin(authors_to_eliminate) & 
        ~user_interactions['to'].isin(authors_to_eliminate)
    ]
    below_threshold_interactions.to_csv(os.path.join(directory, "removed_below_threshold_interactions.csv"), index=False)

    print("Done cleaning for user interactions")
    print("Now fetching GitHub usernames")

    # Fetch GitHub usernames for authors in interactions
    user_interactions['from'] = user_interactions['from'].apply(get_github_user_name)
    user_interactions['to'] = user_interactions['to'].apply(get_github_user_name)

    # Step 4: Remove rows where 'from' or 'to' is empty after GitHub username fetching
    empty_from_to = user_interactions[user_interactions['from'].isna() | user_interactions['to'].isna()]
    user_interactions = user_interactions.dropna(subset=['from', 'to'])
    empty_from_to.to_csv(os.path.join(directory, "removed_empty_from_to.csv"), index=False)

    print("Done GitHub username fetching")
    print("Cleaned user interactions saved.")

    return user_interactions


def sentiment_analysis(source_path='tukaani-project_xz/'):
    """
    Perform both message and post-level sentiment analysis 

    Parameters:
        source_path (str): Path to the directory containing post files.

    Returns:
        post_sentiment_results, cleaned_user_interactions: DataFrames that contains post and message-level sentiment analysis
    """
    
    # Initialize the folder path and sentiment tracker
    folder_path = os.path.join(source_path, "individual_issue_PR/")
    print("Running sentence-level sentiment analysis...")
    count = 0
    
    sentiment_tracker = defaultdict(lambda: {'POS': [], 'NEU': [], 'NEG': []})
    post_sentiment_results = []
    analyzer = create_analyzer(task="sentiment", lang="en")

    # Process each file in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            sentiment_score_total = 0
            num_messages = 0
            
            # Perform sentiment analysis on each row in the DataFrame
            for index, row in df.iterrows():
                source_author = row['from']
                
                # Ensure 'target_author' is treated as a list
                target_author = row['to']
                if isinstance(target_author, str):
                    try:
                        target_author = ast.literal_eval(target_author)  # Convert string to list
                    except (ValueError, SyntaxError):
                        target_author = []  # Default to an empty list if parsing fails

                # Ensure target_author is always a list
                if not isinstance(target_author, list):
                    target_author = [target_author]
                
                text = str(row['body'])
                
                # Analyze sentiment of the text
                result = analyzer.predict(text)
                sentiment, sentiment_score = get_sentiment_score(result)
                
                sentiment_score_total += sentiment_score
                num_messages += 1
                
                for target in target_author:
                    # Update sentiment tracker with result
                    update_sentiment_tracker(sentiment_tracker, source_author, target, sentiment, sentiment_score, text, filename)

            sentiment_score_avg = sentiment_score_total / num_messages if num_messages > 0 else 0
            
            if sentiment_score_avg > 0.2:
                post_sentiment = "POS"
            elif sentiment_score_avg < -0.2:
                post_sentiment = "NEG"
            else:
                post_sentiment = "NEU"
            
            # Append post sentiment analysis result to list
            post_sentiment_results.append({
                'name': filename,
                'type': classify_pr_or_issue(filename),
                'sentiment': post_sentiment,
                'sentiment_score': sentiment_score_avg
            })
        
        count += 1
    
    post_sentiment_results = pd.DataFrame(post_sentiment_results).sort_values(by=['name'])
    
    print("Sentence-level sentiment analysis done on " + str(count) + " posts.")
    print("\nNow cleaning user interactions...")
    
    # Clean user interactions based on sentiment tracker
    cleaned_user_interactions = clean_user_interactions(source_path, sentiment_tracker)
    print("\nNow constructing individual conversations")
    
    # Construct individual conversation files
    construct_individual_conversations(source_path, cleaned_user_interactions)
    
    return post_sentiment_results, cleaned_user_interactions


def construct_individual_conversations(folder_path, user_interactions):
    """
    Construct individual conversation files for each unique user interaction.

    Parameters:
        folder_path (str):                  Path to the directory where conversation files will be stored.
        user_interactions (pd.DataFrame):   DataFrame containing user interactions.

    Returns:
        None
    """
    
    # Create output directory for conversation files
    output_dir = os.path.join(folder_path, 'individual_conversations')
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    else:
        shutil.rmtree(output_dir)
        os.mkdir(output_dir)
    
    # Process each interaction row in the DataFrame
    for index, row in user_interactions.iterrows():
        from_author = row['from']
        to_author = row['to']
    
        # Initialize lists to store conversation details
        messages = []
        moods = []
        filenames = []
        scores = []
    
        # Populate lists with positive, neutral, and negative messages
        for message_data in row['positive']:
            messages.append(message_data['message'])
            filenames.append(message_data['file_name'])
            moods.append('positive')
            scores.append(message_data.get('score', None))
    
        for message_data in row['neutral']:
            messages.append(message_data['message'])
            filenames.append(message_data['file_name'])
            moods.append('neutral')
            scores.append(message_data.get('score', None))
    
        for message_data in row['negative']:
            messages.append(message_data['message'])
            filenames.append(message_data['file_name'])
            moods.append('negative')
            scores.append(message_data.get('score', None))
    
        # Create a DataFrame for the conversation
        conversation_df = pd.DataFrame({
            'from': [from_author] * len(messages),
            'to': [to_author] * len(messages),
            'file_name': filenames,
            'message': messages,
            'mood': moods,
            'score': scores
        })
    
        try:
            # Save the conversation to a CSV file
            file_name = f'{from_author}_to_{to_author}.csv'.replace(' ', '_')
            conversation_df.to_csv(os.path.join(output_dir, file_name), index=False)
        except Exception as e:
            print(f"Skipping file {file_name} due to error: {e}")
    
    print("Individual CSV files have been created.")



def track_sentiment_given_and_received(user_interaction_df):
    """
    Track the sentiment given and received by each user, and return aggregated results.

    Parameters:
        user_interaction_df (pd.DataFrame): DataFrame containing user interactions.

    Returns:
        sentiment_summary_df: A DataFrame with aggregated sentiment scores and counts (given and received).
    """
    
    # Initialize dictionaries to track sentiment given and received by users
    sentiment_given = {}
    sentiment_received = {}

    # Helper function to update sentiment tracking dictionaries
    def update_sentiment_tracker(user_dict, key, score, message_count, pos, neu, neg):
        if key not in user_dict:
            user_dict[key] = {
                'total_score': 0, 'message_count': 0, 
                'positive': 0, 'neutral': 0, 'negative': 0
            }
        user_dict[key]['total_score'] += score
        user_dict[key]['message_count'] += message_count
        user_dict[key]['positive'] += pos
        user_dict[key]['neutral'] += neu
        user_dict[key]['negative'] += neg

    # Process each interaction in the DataFrame
    for _, row in user_interaction_df.iterrows():
        source = row['from']
        target = row['to']

        # Count sentiment types and score
        pos_count = len(row['positive'])
        neu_count = len(row['neutral'])
        neg_count = len(row['negative'])
        total_score = sum([msg['score'] for msg in row['positive'] + row['neutral'] + row['negative']])
        message_count = pos_count + neu_count + neg_count

        # Update sentiment dictionaries for source and target
        update_sentiment_tracker(sentiment_given, source, total_score, message_count, pos_count, neu_count, neg_count)
        update_sentiment_tracker(sentiment_received, target, total_score, message_count, pos_count, neu_count, neg_count)

    # Convert tracking dictionaries to DataFrames
    given_df = pd.DataFrame([
        {
            'user': user,
            'sentiment_given': data['total_score'] / data['message_count'] if data['message_count'] > 0 else 0,
            'messages_given': data['message_count'],
            'positive_given': data['positive'],
            'neutral_given': data['neutral'],
            'negative_given': data['negative']
        }
        for user, data in sentiment_given.items()
    ])

    received_df = pd.DataFrame([
        {
            'user': user,
            'sentiment_received': data['total_score'] / data['message_count'] if data['message_count'] > 0 else 0,
            'messages_received': data['message_count'],
            'positive_received': data['positive'],
            'neutral_received': data['neutral'],
            'negative_received': data['negative']
        }
        for user, data in sentiment_received.items()
    ])

    # Merge given and received DataFrames for final summary
    sentiment_summary_df = pd.merge(given_df, received_df, on='user', how='outer').fillna(0)
    return sentiment_summary_df
