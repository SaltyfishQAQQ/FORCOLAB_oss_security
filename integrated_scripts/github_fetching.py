import pandas as pd
import gh_tokens
import ScraperExtend as scraper
import requests
import os
import datetime

def initialize_scraper():
        """
        Initialize the GitHub scraper.

        Returns:
                gh_api: An initialized scraper instance with GitHub tokens.
        """
        gh_api = scraper.ScraperExtend(gh_tokens.tokens)
        return gh_api


def fetch_thread(gh_api, repo_name, folder_location, thread_type, thread_numbers, start_date, end_date):
        """
        Fetch threads (issues or pull requests) from a GitHub repository, filter them by date range,
        and save the details to CSV files.

        Parameters:
                gh_api (ScraperExtend): Initialized GitHub API scraper.
                repo_name (str):        Name of the GitHub repository.
                folder_location (str):  Path to save the fetched threads.
                thread_type (str):      Type of thread ('issue' or 'pr').
                thread_numbers (list):  List of thread IDs to fetch.
                start_date (datetime):  Start date for filtering threads.
                end_date (datetime):    End date for filtering threads.

        Returns:
                None
        """

        # Initialize counter of fetched threads
        count = 0
        
        # Create the folder if it does not exist
        if not os.path.exists(folder_location):
                os.makedirs(folder_location)

        for id in thread_numbers:
                # Fetch detailed information for the thread (issue or PR)
                thread_info = gh_api.repo_get_issue_detail(repo_name, id)
                
                # Extract the thread creation date
                thread_date = thread_info.get("created_at")
                thread_date_dt = datetime.datetime.strptime(thread_date, '%Y-%m-%dT%H:%M:%SZ')

                # Skip if it's outside the specified date range
                if not (start_date <= thread_date_dt <= end_date):
                        continue

                # Fetch needed information for the thread
                header_body = thread_info.get("body")
                thread_author = thread_info.get('user', {}).get('login')

                timeline = gh_api.issue_pr_timeline(repo_name, id)
                events_df = pd.DataFrame(timeline)
                events_df.rename(columns={'author': 'from'}, inplace=True)
                events_df = events_df[['event', 'from', 'created_at', 'body']]

                # Filter events to keep only comments
                events_df = events_df[(events_df['event'] == 'commented')]
                if events_df.empty:
                        continue  # Skip if there are no comments in the timeline

                # Create a DataFrame entry for the initial thread event
                title_df = pd.DataFrame({
                        'event': ['thread_started'],
                        'from': [thread_author],
                        'created_at': [thread_date],
                        'body': [header_body]
                })

                # Concatenate the initial thread entry with the comment events
                events_df = pd.concat([title_df, events_df], ignore_index=True)

                # Save the thread information to a CSV file
                file_name = folder_location + thread_type + "_" + str(id) + ".csv"
                events_df.to_csv(file_name, index=False)
                
                count += 1

        print(f"Total {count} {thread_type} fetched\n")



def fetch_issues_pr(repo_name='tukaani-project/xz', folder_location='tukaani-project_xz/', 
                    start_year=2018, start_month=1, start_day=1, end_year=2024, end_month=6, end_day=1):
        """
        Fetch issues and pull requests from a GitHub repository within a specified date range,
        save the details to separate CSV files, and return the path where files are saved.

        Parameters:
                repo_name (str):        Name of the GitHub repository.
                folder_location (str):  Path to save the fetched data.
                start_year (int):       Start year for filtering issues and PRs.
                start_month (int):      Start month for filtering issues and PRs.
                start_day (int):        Start day for filtering issues and PRs.
                end_year (int):         End year for filtering issues and PRs.
                end_month (int):        End month for filtering issues and PRs.
                end_day (int):          End day for filtering issues and PRs.

        Returns:
                folder_path: The path where issue and PR files are saved.
        """

        # Initialize the folder path and GitHub scraper
        folder_path = os.path.join(folder_location, "individual_issue_PR/")
        gh_api = initialize_scraper()

        # Fetch all issues and pull requests for the specified repository and time
        start_date = datetime.datetime(start_year, start_month, start_day)
        end_date = datetime.datetime(end_year, end_month, end_day)
        all_issues = gh_api.repo_issues(repo_name)
        all_prs = gh_api.repo_pulls(repo_name)

        # Extract issue and PR IDs into lists
        issues_df = pd.DataFrame(all_issues)
        prs_df = pd.DataFrame(all_prs)
        issues_ids = issues_df['number'].tolist()
        prs_ids = prs_df['number'].tolist()

        print(f"Fetching Issues and PRs for {repo_name}\n")

        # Fetch issues and PRs within the specified date range and save to the folder path
        fetch_thread(gh_api, repo_name, folder_path, 'issue', issues_ids, start_date, end_date)
        fetch_thread(gh_api, repo_name, folder_path, 'pr', prs_ids, start_date, end_date)

        return folder_path



def fetch_commit_info(repo_name='tukaani-project/xz', 
                      folder_location='tukaani-project_xz/', 
                      start_year=2018, start_month=1, start_day=1, 
                      end_year=2024, end_month=6, end_day=1):
        """
        Fetch commit information from a GitHub repository, filter commits by date, and save them to a CSV file.

        Parameters:
                repo_name (str):        Name of the GitHub repository.
                folder_location (str):  Path to save the fetched commit information.
                start_year (int):       Start year for filtering commits.
                start_month (int):      Start month for filtering commits.
                start_day (int):        Start day for filtering commits.
                end_year (int):         End year for filtering commits.
                end_month (int):        End month for filtering commits.
                end_day (int):          End day for filtering commits.

        Returns:
                commit_info_df: A DataFrame containing the filtered commit information.
        """
        
        # Initialize the scraper
        gh_api = initialize_scraper()
        
        # Ensure the folder exists
        if not os.path.exists(folder_location):
                os.makedirs(folder_location)
        
        # Define the start and end date as datetime objects
        
        
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
        commit_info_df = pd.DataFrame(extracted_data)
        
        # Filter out rows with invalid dates and apply the date range filter
        start_date = datetime.datetime(start_year, start_month, start_day)
        end_date = datetime.datetime(end_year, end_month, end_day)

        def safe_strptime(date_str):
                try:
                        return datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
                except (ValueError, TypeError):
                        return None  # Return None if the date is invalid
        
        commit_info_df['committer_date'] = commit_info_df['committer_date'].apply(safe_strptime)
        commit_info_df['author_date'] = commit_info_df['author_date'].apply(safe_strptime)
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
                commit_info_df (pd.DataFrame):  DataFrame containing commit information.
                top_n (int):                    The number of top committers to return.
                
        Returns:
                top_committers: A DataFrame containing the top N committers and their commit counts.
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

