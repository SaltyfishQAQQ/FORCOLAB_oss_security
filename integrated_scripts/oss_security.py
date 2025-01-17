#!/usr/bin/env python3

import github_fetching as fetcher
import data_cleaning as cleaner
import sentiment_analysis as analyzer
import visualization as visualizer
import pandas as pd
import embedding_gen as emb_gen

def main():
    print("Welcome to the OSS_Security Project!")

    # Get user input for the target repository and date range
    target_repo = input("Enter the name of the target repository (after github.com/): ")
    
    start_date = input("Enter the start date for data collection (YYYY-MM-DD): ")

    end_date = input("Enter the end date for data collection (YYYY-MM-DD): ")
    print("----------------------------------------------")

    folder_path = target_repo.replace('/', '_')


    # Fetch user interaction data from the target repository
    issue_pr_location = fetcher.fetch_issues_pr(repo_name=target_repo, folder_location=folder_path, start_date=start_date, end_date=end_date)
    
    # Clean the data
    cleaner.clean_thread(issue_pr_location)

    # Analyze the sentiment of the cleaned data
    post_sentiment_results, user_interactions = analyzer.sentiment_analysis()

    # Visualize the sentiment analysis results
    user_interactions = pd.DataFrame(user_interactions)
    graph_path = visualizer.generate_network(folder_path, user_interactions, 'network_graph.html', 0) 

    visualizer.show_graph(graph_path)

if __name__ == "__main__":
    main()