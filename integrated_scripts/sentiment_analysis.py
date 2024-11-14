from pysentimiento import create_analyzer
import torch
import os
import pandas as pd
from collections import defaultdict
import data_cleaning as cleaner
import requests
import shutil
import github_fetching as fetcher

analyzer = create_analyzer(task = "sentiment", lang = "en")

def group_text_from_csv(df):
    grouped_text = ""
    column_name = 'body'
    
    grouped_text += "".join(df[column_name].dropna()) + "\n"

    return str(grouped_text)

def classify_pr_or_issue(filename):
    if 'pr' in filename.lower():
        return 'PR'
    elif 'issue' in filename.lower():
        return 'Issue'
    else:
        return 'Unknown'

def is_valid_author(author_name):
    # Ensure the input is a string; if not, return False
    if not isinstance(author_name, str):
        return False
    
    # Check if the name contains only letters, spaces, hyphens, apostrophes, or digits
    return bool(re.match(r'^[a-zA-Z0-9\s\'-]+$', author_name))

def count_dataset(user_interactions):
    num_pairs = len(user_interactions)
    num_messages = 0
    
    for index, row in user_interactions.iterrows():
        num_messages = num_messages + len(row['positive']) + len(row['negative']) + len(row['neutral'])
        
    print("Number of author pairs: " + str(num_pairs))
    print("Number of messages: " + str(num_messages))



def update_sentiment_tracker(sentiment_tracker, source_author, target_in_message, sentiment, sentiment_score, original_message, filename):
    if sentiment == 'POS':
        sentiment_tracker[(source_author, target_in_message)]['POS'].append({
            'message': original_message,
            'score': sentiment_score,
            'file_name' : filename
        })
    elif sentiment == 'NEU':
        sentiment_tracker[(source_author, target_in_message)]['NEU'].append({
            'message': original_message,
            'score': sentiment_score,
            'file_name' : filename
        })
    elif sentiment == 'NEG':
        sentiment_tracker[(source_author, target_in_message)]['NEG'].append({
            'message': original_message,
            'score': sentiment_score,
            'file_name' : filename
        })

def get_sentiment_score(sentiment_result):
    sentiment_score = sentiment_result.probas['POS']*1 + sentiment_result.probas['NEG']*(-1)
    sentiment = "NEU"
    if sentiment_score >0.2:
        sentiment = "POS"
    elif sentiment_score < (-0.2):
        sentiment = "NEG"

    return sentiment, sentiment_score

def get_github_user_name(username, token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")):
    url = f"https://api.github.com/users/{username}"
    headers = {"Authorization": f"token {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('name') == None:
            return username
            
        return data.get('name', username)  # Return username if the real name is not found
    else:
        print(f"Error: Unable to fetch data for username '{username}'. Status code: {response.status_code}")
        return username

def clean_user_interactions(source_path, sentiment_tracker):
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

    directory = os.path.join(source_path, "deleted_user_interactions/")
    if not os.path.exists(directory):
        os.mkdir(directory)
    else:
        shutil.rmtree(directory)
        os.mkdir(directory)

    # Step 1: Remove invalid 'to' values
    invalid_to = user_interactions[user_interactions['to'].isna()]
    user_interactions = user_interactions.dropna(subset=['to'])
    invalid_to.to_csv(os.path.join(directory, "removed_invalid_to.csv"), index=False)

    # Step 2: Remove self-interactions
    self_interactions = user_interactions[user_interactions['from'] == user_interactions['to']]
    user_interactions = user_interactions[user_interactions['from'] != user_interactions['to']]
    self_interactions.to_csv(os.path.join(directory, "removed_self_interactions.csv"), index=False)

    # Step 3: Filter out rows where authors are below the contribution threshold
    contribution_df = cleaner.calculate_author_contributions()
    contribution_df = contribution_df.sort_values(by='count', ascending=False)
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
    user_interactions = user_interactions.sort_values(by=['from'])
    user_interactions['from'] = user_interactions['from'].apply(get_github_user_name)
    user_interactions['to'] = user_interactions['to'].apply(get_github_user_name)
    print("Done GitHub username fetching")

    return user_interactions


def post_sentiment_analysis(source_path = 'tukaani-project_xz/'):
    print("Running post-level sentiment analysis...")
    count = 0
    post_sentiment_results = []
    folder_path = os.path.join(source_path, 'individual_issue_PR/')
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            grouped_text = group_text_from_csv(df)
            
            result = analyzer.predict(grouped_text)
            sentiment, sentiment_score = get_sentiment_score(result)
            
            post_sentiment_results.append({
                'name': filename,
                'type': classify_pr_or_issue(filename),
                'sentiment': sentiment,
                'sentiment_score': sentiment_score
            })
            count += 1
    post_sentiment_results = pd.DataFrame(post_sentiment_results).sort_values(by=['name'])
    print("Post-level sentiment analysis done on " + str(count) + " posts.")
    return post_sentiment_results


def sentence_sentiment_analysis(source_path = 'tukaani-project_xz/'):
    folder_path = os.path.join(source_path, "individual_issue_PR/")
    print("Running sentence-level sentiment analysis...")
    count = 0
    sentiment_tracker = defaultdict(lambda: {'POS': [], 'NEU': [], 'NEG': []})
    analyzer = create_analyzer(task = "sentiment", lang = "en")

    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            
            for index, row in df.iterrows():
                source_author = row['from']
                target_author = row['to']
                text = str(row['body'])
                result = analyzer.predict(text)
                sentiment, sentiment_score = get_sentiment_score(result)
                update_sentiment_tracker(sentiment_tracker, source_author, target_author, sentiment, sentiment_score, text, filename)
        
        count+=1
    
    print("Sentence-level sentiment analysis done on " + str(count) + " posts.")
    print("\nNow cleaning user interactions...")
    cleaned_user_interactions = clean_user_interactions(source_path, sentiment_tracker)
    print("\nNow constructing individual conversations")
    construct_individual_conversations(source_path, cleaned_user_interactions)
    
    return cleaned_user_interactions


def construct_individual_conversations(folder_path, user_interactions):
    # Ensure the output directory exists
    output_dir = os.path.join(folder_path, 'individual_conversations')
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    else:
        shutil.rmtree(output_dir)
        os.mkdir(output_dir)
    
    # Iterate through each row in the DataFrame
    for index, row in user_interactions.iterrows():
        from_author = row['from']
        to_author = row['to']
    
        # Initialize lists to hold data for the new CSV
        messages = []
        moods = []
        filenames = []
        scores = []
    
        # Assuming 'positive', 'neutral', and 'negative' columns contain lists of dicts
        for message_data in row['positive']:  # Use eval() to convert stringified list to list object
            messages.append(message_data['message'])
            filenames.append(message_data['file_name'])
            moods.append('positive')
            scores.append(message_data.get('score', None))  # Assuming score is a key in the message dict
    
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
    
        # Create a DataFrame for this pair
        conversation_df = pd.DataFrame({
            'from': [from_author] * len(messages),
            'to': [to_author] * len(messages),
            'file_name': filenames,
            'message': messages,
            'mood': moods,
            'score': scores
        })
    
        try:
            file_name = f'{from_author}_to_{to_author}.csv'.replace(' ', '_')
            conversation_df.to_csv(os.path.join(output_dir, file_name), index=False)
        except Exception as e:
            print(f"Skipping file {file_name} due to error: {e}")
    
    print("Individual CSV files have been created.")



def track_sentiment_given_and_received(user_interaction_df):
    """
    Track the sentiment given and received by each user, along with interaction counts, and save the summary as a CSV file.

    Parameters:
        source_path (str): Folder path to save the CSV file.
        user_interaction_df (pd.DataFrame): DataFrame containing user interactions.
        file_name (str): Name of the output CSV file.

    Returns:
        pd.DataFrame: A DataFrame with aggregated sentiment scores and counts (given and received).
    """

    # Initialize dictionaries to store sentiment scores, message counts, and sentiment type counts
    sentiment_given = {}
    sentiment_received = {}

    # Helper function to update the tracker dictionaries
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

    # Iterate over each interaction row in the DataFrame
    for _, row in user_interaction_df.iterrows():
        source = row['from']
        target = row['to']

        # Calculate sentiment-related metrics for this interaction
        pos_count = len(row['positive'])
        neu_count = len(row['neutral'])
        neg_count = len(row['negative'])

        total_score = sum([msg['score'] for msg in row['positive'] + row['neutral'] + row['negative']])
        message_count = pos_count + neu_count + neg_count

        # Update sentiment trackers for the source (given) and target (received)
        update_sentiment_tracker(sentiment_given, source, total_score, message_count, pos_count, neu_count, neg_count)
        update_sentiment_tracker(sentiment_received, target, total_score, message_count, pos_count, neu_count, neg_count)

    # Create DataFrames for sentiment given and received
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

    # Merge the two DataFrames to create a complete summary
    sentiment_summary_df = pd.merge(given_df, received_df, on='user', how='outer').fillna(0)


    return sentiment_summary_df

def identify_threat(
    sentiment_summary_df, top_committer_df, top_n=5
):
    """
    Aggregate sentiment summary with contribution data and identify the most dangerous person(s).

    Parameters:
        sentiment_summary_df (pd.DataFrame): DataFrame containing user sentiment metrics.
        top_committer_df (pd.DataFrame): DataFrame containing top committers and their contributions.
        top_n (int): Number of top dangerous users to return.

    Returns:
        pd.DataFrame: DataFrame containing the top dangerous users with selected columns.
    """

    # Step 1: Filter sentiment data to include only top committers
    top_contributors_sentiment = sentiment_summary_df[
        sentiment_summary_df['user'].isin(top_committer_df['author_name'])
    ]

    # Step 2: Merge with commit count from top_committer_df
    merged_df = pd.merge(
        top_contributors_sentiment, 
        top_committer_df[['author_name', 'commit_count']],
        left_on='user', right_on='author_name',
        how='inner'
    )

    # Step 3: Sort by the received sentiment score (from lowest to highest)
    ranked_contributors = merged_df.sort_values(
        by='sentiment_received', ascending=True
    )

    # Step 4: Select the top N contributors with the lowest sentiment score
    top_dangerous_users = ranked_contributors.head(top_n)

    # Step 5: Return only the relevant columns
    return top_dangerous_users[['user', 'sentiment_received', 'sentiment_given', 'commit_count']]

