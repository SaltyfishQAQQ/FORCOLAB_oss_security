import requests
import pandas as pd
import os
import re
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

def remove_quoted_lines(df, column_name='body'):
    """
    Remove quoted lines from a specified column in the DataFrame.

    Parameters:
        df (pd.DataFrame): 	DataFrame containing text data.
        column_name (str): 	Name of the column from which quoted lines (starting with '>') should be removed.

    Returns:
        pd.DataFrame: DataFrame with quoted lines removed from the specified column.
    """

    # Remove lines starting with '>'
    df[column_name] = df[column_name].dropna().apply(
        lambda x: "\n".join([line for line in x.splitlines() if not line.strip().startswith(">")])
    )
    return df
    

def extract_mention(text):
	"""
    Extract the first mentioned username (preceded by '@') from a text string.

    Parameters:
        text (str): Text containing a potential mention.

    Returns:
        str or None: The username mentioned in the text, or None if no mention is found.
    """

	if pd.isnull(text):
		return None
	match = re.search(r'@(\w+)', text)
	if match:
		return match.group(1)  
	return None  

def find_reply_to(df):
    """
    Determine the 'reply_to' author for each message in a DataFrame based on a heuristic of mentions and previous authors.

    Parameters:
        df (pd.DataFrame): DataFrame with messages containing 'from' and 'body' columns.

    Returns:
        list: A list of authors that each message replies to.
    """
    
    # List to store reply_to author for each message
    reply_to_list = []
    previous_author = None
    
    # Iterate over each row in the DataFrame
    for i in range(len(df)):
        current_author = df.iloc[i]['from']
        mention = extract_mention(df.iloc[i]['body'])
        
        # If a mention is found, set reply_to as the mentioned person
        if mention:
            reply_to_list.append(mention)
        else:
            # If no mention is found, look for the previous different author to reply to
            if previous_author and current_author == previous_author:
                for j in range(i - 1, -1, -1):
                    if df.iloc[j]['from'] != current_author:
                        reply_to_list.append(df.iloc[j]['from'])
                        break
                else:
                    # If no previous different author is found, default to the original creator
                    reply_to_list.append(df.iloc[0]['from'])
            else:
                # Default to the previous message's author
                reply_to_list.append(df.iloc[i - 1]['from'] if i > 0 else df.iloc[0]['from'])
        
        # Update previous_author to the current one for the next iteration
        previous_author = current_author
    
    return reply_to_list

def clean_thread(folder_path):
    """
    Clean CSV files in a folder by removing quoted lines and determining replying relationship for each message.

    Parameters:
        folder_path (str): Path to the folder containing CSV files to be cleaned.

    Returns:
        None
    """
    
    file_count = 0
    print("Data Cleaning in Progress\n")

    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            try:
                df = pd.read_csv(folder_path + file)
                original_creator = df.iloc[0]['from']
                
                # Remove quoted lines and fill missing 'from' values with the original creator
                df = remove_quoted_lines(df)
                df['from'] = df['from'].fillna(original_creator)

                # Determine 'to' field based on reply relationship and save back to CSV
                df['to'] = find_reply_to(df)
                df.to_csv(folder_path + file, index=False)
                file_count += 1
            
            except KeyError as e:
                print(f"Error in file {file}: KeyError -> {e}")
    
    print(f"Total {file_count} files cleaned\n")



def count_words_or_characters(text, mode='words'):
    """
    Count words or characters in a text string.

    Parameters:
        text (str): 	Text to count words or characters in.
        mode (str): 	Mode for counting ('words' or 'characters').

    Returns:
        int: The number of words or characters in the text.

    Raises:
        ValueError: If mode is not 'words' or 'characters'.
    """
    
    if pd.isnull(text):
        return 0
    if mode == 'words':
        return len(text.split())
    elif mode == 'characters':
        return len(text)
    else:
        raise ValueError("Mode should be 'words' or 'characters'.")


def calculate_author_contributions(source_path = 'tukaani-project_xz/', mode='words'):
    """
    Calculate the contributions of each author based on word or character count in message bodies within CSV files.

    Parameters:
        source_path (str): 	Path to the source directory containing the "individual_issue_PR/" folder with CSV files.
        mode (str): 		Mode for counting ('words' or 'characters').

    Returns:
        pd.DataFrame: DataFrame containing authors and their respective contribution counts, sorted by count in descending order.
    """
    
    # Define the folder path
    folder_path = os.path.join(source_path, "individual_issue_PR/")
    author_contributions = defaultdict(int)
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            
            # Calculate contribution for each message in the file
            for index, row in df.iterrows():
                try:
                    author = row['from']
                    text = row['body']
                    count = count_words_or_characters(text, mode=mode)
                    author_contributions[author] += count
                except KeyError as e:
                    # Report error for missing keys in a specific row
                    print(f"KeyError: {e} in file {filename} at row {index}")
                    print(f"Row content: {row}")

    # Convert author contributions to a DataFrame and sort by contribution count
    contribution_df = pd.DataFrame(list(author_contributions.items()), columns=['from', 'count'])
    contribution_df = contribution_df.sort_values(by='count', ascending=False)         
    
    return contribution_df


def get_unique_authors_from_folder(folder_path):
    """
    Retrieve unique authors from 'from' column across all CSV files in a specified folder.

    Parameters:
        folder_path (str): Path to the folder containing CSV files.

    Returns:
        set: A set of unique authors found in the CSV files' 'from' column.
    """
    
    # Initialize an empty set to store unique authors
    unique_authors = set()
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            
            # Add unique authors from 'from' column to the set
            if 'from' in df.columns:
                unique_authors.update(df['from'].dropna().unique())
    
    return unique_authors



    