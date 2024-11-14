import pandas as pd
import gh_tokens
import ScraperExtend as scraper
import requests
import os
import datetime

def initialize_scraper():
        gh_api = scraper.ScraperExtend(gh_tokens.tokens)
        return gh_api

def fetch_thread(gh_api, repo_name, folder_location, thread_type, thread_numbers, start_date, end_date):
        count = 0
        if not os.path.exists(folder_location):
                os.makedirs(folder_location)

        for id in thread_numbers:
                thread_info = gh_api.repo_get_issue_detail(repo_name, id)
                thread_date = thread_info.get("created_at")

                thread_date_dt = datetime.datetime.strptime(thread_date, '%Y-%m-%dT%H:%M:%SZ')
                # Check if the thread_date is within the desired range
                if not (start_date <= thread_date_dt <= end_date):
                        continue  # Skip this issue/PR if it's outside the date range

                header_body = thread_info.get("body")
                thread_author = thread_info.get('user', {}).get('login')
                
                timeline=gh_api.issue_pr_timeline(repo_name,id)
                events_df = pd.DataFrame(timeline)

                events_df.rename(columns={'author': 'from'}, inplace=True)
                events_df = events_df[['event', 'from', 'created_at', 'body']]

                events_df = events_df[(events_df['event'] == 'commented')]
                if events_df.empty:
                        continue

                title_df = pd.DataFrame({
                        'event': ['thread_started'],
                        'from': [thread_author],
                        'created_at': [thread_date],
                        'body': [header_body]
                })

                events_df = pd.concat([title_df, events_df], ignore_index=True)

                file_name = folder_location + thread_type  + "_" + str(id) + ".csv"
                events_df.to_csv(file_name, index=False)
                count+=1

        print(f"Total {count} {thread_type} fetched\n")



def fetch_issues_pr(repo_name= 'tukaani-project/xz', folder_location = 'tukaani-project_xz/', start_year= 2018, start_month = 1, start_day = 1, end_year = 2024, end_month = 6, end_day=1):
        folder_path = os.path.join(folder_location, "individual_issue_PR/")
        gh_api = initialize_scraper()

        start_date = datetime.datetime(start_year, start_month, start_day)
        end_date = datetime.datetime(end_year, end_month, end_day)

        all_issues = gh_api.repo_issues(repo_name)
        all_prs = gh_api.repo_pulls(repo_name)
        issues_df = pd.DataFrame(all_issues)
        prs_df = pd.DataFrame(all_prs)

        issues_ids = issues_df['number'].tolist()
        prs_ids = prs_df['number'].tolist()

        print(f"Fetching Issues and PRs for {repo_name}\n")
        fetch_thread(gh_api, repo_name, folder_path, 'issue', issues_ids, start_date, end_date)
        fetch_thread(gh_api, repo_name, folder_path, 'pr', prs_ids, start_date, end_date)

        return folder_path


def fetch_commit_info(repo_name='tukaani-project/xz', 
                      folder_location='tukaani-project_xz/', 
                      start_year=2018, start_month=1, start_day=1, 
                      end_year=2024, end_month=6, end_day=1):

        # Initialize the scraper
        gh_api = initialize_scraper()
        
        # Ensure the folder exists
        os.makedirs(folder_location, exist_ok=True)
        
        # Define the start and end date as datetime objects
        start_date = datetime.datetime(start_year, start_month, start_day)
        end_date = datetime.datetime(end_year, end_month, end_day)
        
        # Fetch all commits from the repository
        all_commits = gh_api.repo_commits(repo_name)
        commits_df = pd.DataFrame(all_commits)
        
        # Extract the relevant fields
        extracted_data = {
                'sha': commits_df['sha'],
                'author_name': commits_df['commit'].apply(lambda x: x.get('author', {}).get('name', 'Unknown')),
                'committer_name': commits_df['commit'].apply(lambda x: x.get('committer', {}).get('name', 'Unknown')),
                'author_date': commits_df['commit'].apply(lambda x: x.get('author', {}).get('date', 'Unknown')),
                'committer_date': commits_df['commit'].apply(lambda x: x.get('committer', {}).get('date', 'Unknown')),
                'commit_message': commits_df['commit'].apply(lambda x: x.get('message', 'Unknown')),
        }
        
        # Create a DataFrame from the extracted data
        commit_info_df = pd.DataFrame(extracted_data)
        
        # Convert date strings to datetime objects, handling errors gracefully
        def safe_strptime(date_str):
                try:
                        return datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
                except (ValueError, TypeError):
                        return None  # Return None if the date is invalid
        
        commit_info_df['committer_date'] = commit_info_df['committer_date'].apply(safe_strptime)
        commit_info_df['author_date'] = commit_info_df['author_date'].apply(safe_strptime)
        
        # Filter out rows with invalid dates and apply the date range filter
        commit_info_df = commit_info_df.dropna(subset=['committer_date', 'author_date'])
        commit_info_df = commit_info_df[
                (commit_info_df['committer_date'] >= start_date) & 
                (commit_info_df['committer_date'] <= end_date)
        ]
        
        # Save the filtered DataFrame to a CSV file
        file_name = os.path.join(folder_location, 'commits_info.csv')
        commit_info_df.to_csv(file_name, index=False)
        
        print(f"Filtered commits saved to {file_name}")

        return commit_info_df

def get_top_committers(commit_info_df, top_n=10):
        """
        Get the top N committers from the commit DataFrame.
        
        Parameters:
        commit_info_df (pd.DataFrame): DataFrame containing commit information.
        top_n (int): The number of top committers to return.
        
        Returns:
        pd.DataFrame: A DataFrame containing the top N committers and their commit counts.
        """
        # Group by committer_name and count the number of commits for each committer
        top_committers = (
                commit_info_df
                .groupby('author_name')
                .size()
                .reset_index(name='commit_count')
                .sort_values(by='commit_count', ascending=False)
                .head(top_n)
        )

        return top_committers

