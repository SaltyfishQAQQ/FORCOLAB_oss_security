import requests
import pandas as pd
import os
import re
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

def remove_quoted_lines(df, column_name='body'):
    # Apply the line filtering to the specified column
    df[column_name] = df[column_name].dropna().apply(
        lambda x: "\n".join([line for line in x.splitlines() if not line.strip().startswith(">")])
    )
    return df
    

def extract_mention(text):
    if pd.isnull(text):
        return None
    match = re.search(r'@(\w+)', text)
    if match:
        return match.group(1)  
    return None  

def find_reply_to(df):
    """Determine the 'reply_to' author for each message based on the heuristic."""
    reply_to_list = []
    previous_author = None
    
    for i in range(len(df)):
        current_author = df.iloc[i]['from']
        mention = extract_mention(df.iloc[i]['body'])
        
        if mention:
            # If a mention is found, reply_to is the mentioned person
            reply_to_list.append(mention)
        else:
            # If no mention is found, reply to the previous different author
            if previous_author and current_author == previous_author:
                # Find the nearest previous different author
                for j in range(i-1, -1, -1):
                    if df.iloc[j]['from'] != current_author:
                        reply_to_list.append(df.iloc[j]['from'])
                        break
                else:
                    # If no previous different author is found, default to the original creator
                    reply_to_list.append(df.iloc[0]['from'])
            else:
                # Default to the previous message's author
                reply_to_list.append(df.iloc[i-1]['from'] if i > 0 else df.iloc[0]['from'])
        
        previous_author = current_author
    
    return reply_to_list

def clean_thread(folder_path):
    file_count = 0
    print("Data Cleaning in Progress\n")

    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            try:
                df = pd.read_csv(folder_path + file)

                original_creator = df.iloc[0]['from']
                df = remove_quoted_lines(df)
                df['from'] = df['from'].fillna(original_creator)
                df['to'] = find_reply_to(df)
                df.to_csv(folder_path + file, index=False)
                file_count += 1
            
            except KeyError as e:
                print(f"Error in file {file}: KeyError -> {e}")
    
    print(f"Total {file_count} files cleaned\n")



def count_words_or_characters(text, mode='words'):
    if pd.isnull(text):
        return 0
    if mode == 'words':
        return len(text.split())
    elif mode == 'characters':
        return len(text)
    else:
        raise ValueError("Mode should be 'words' or 'characters'.")


def calculate_author_contributions(source_path = 'tukaani-project_xz/', mode='words'):
    folder_path = os.path.join(source_path, "individual_issue_PR/")
    author_contributions = defaultdict(int)
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            
            for index, row in df.iterrows():
                try:
                    author = row['from']
                    text = row['body']
                    count = count_words_or_characters(text, mode=mode)
                    author_contributions[author] += count
                except KeyError as e:
                    print(f"KeyError: {e} in file {filename} at row {index}")
                    print(f"Row content: {row}")

          
    contribution_df = pd.DataFrame(list(author_contributions.items()), columns=['from', 'count'])
    contribution_df = contribution_df.sort_values(by = 'count', ascending=False)         
    
    return contribution_df


def get_unique_authors_from_folder(folder_path):
    unique_authors = set()
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            
            if 'from' in df.columns:
                unique_authors.update(df['from'].dropna().unique())
    
    return unique_authors



    