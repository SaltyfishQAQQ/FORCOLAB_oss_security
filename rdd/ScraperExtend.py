import stscraper as scraper

class ScraperExtend(scraper.GitHubAPI):
    
    @scraper.api_filter(lambda issue: 'pull_request' not in issue)
    @scraper.api('repos/%s/issues', paginate=True, state='closed')
    def repo_closed_issues(self, repo_slug):
        """Get closed issues of a given repository (not including pull requests)"""
        # https://developer.github.com/v3/issues/#list-issues-for-a-repository
        return repo_slug

    @scraper.api('repos/%s/issues/%s')
    def repo_get_issue_detail(self, repo_slug,pull_id):
        """Given repo_slug and pull_id, return the detail of the a PR/issue
        params:
        - repo_slug: repository full repo slug (e.g., "owner/repo")
        - pull_id: issue or pull request id (e.g., 125)
        output:
        - issue/pull request details as described in the API
        https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#get-an-issue
        """
        return repo_slug,pull_id

    #from https://github.com/shuiblue/GitHubAPI-Crawler by Prof.Shurui Zhou, for collecting issue/PR timelines
    #more details on the timeline API can be found here:
    # https://docs.github.com/en/rest/issues/timeline?apiVersion=2022-11-28
    def issue_pr_timeline(self, repo, issue_id):
        """ Return timeline on an issue or a pull request
        params:
        - repo: repository full repo slug (e.g., "owner/repo")
        - issue_id: issue or pull request id (e.g., 125)
        output:
        - all events on the issue or pull request specifically parsed for needed fields, which is subject to change/extend.
        For details on the timeline API, see:
        https://docs.github.com/en/rest/issues/timeline?apiVersion=2022-11-28
        """
        url = "repos/%s/issues/%s/timeline" % (repo, issue_id)
        events = self.request(url, paginate=True, state='all')
        for event in events:
            if event['event'] == 'cross-referenced':
                author = event['actor'] or {}
                assignees = event['source']['issue']['assignees'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': "",
                    'created_at': event.get('created_at'),
                    'id': event['source']['issue']['number'],
                    'repo': event['source']['issue']['repository']['full_name'],
                    'type': 'pull_request' if 'pull_request' in event['source']['issue'].keys() else 'issue',
                    'state': event['source']['issue']['state'],
                    'assignees': ''.join(assignee.get('login') for assignee in assignees),
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'referenced':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event['created_at'],
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'labeled':
                author = event['actor'] or {}
                label = event['label'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': label['name'],
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'unlabeled':
                author = event['actor'] or {}
                label = event['label'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': label['name'],
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'committed':
                author = event['author'] or {}
                yield {
                    'event': event['event'],
                    'author': '',
                    'author_name': author['name'],
                    'email': author['email'],
                    'author_type': '',
                    'author_association': '',
                    'commit_id': event['sha'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'reviewed':
                author = event['user'] or {}
                html_link = event['_links']['html'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': event['author_association'],
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': event['state'],
                    'assignees': '',
                    'label': '',
                    'body': event['body'],
                    'submitted_at': event.get('submitted_at'),
                    'links': html_link.get('href'),
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'commented':
                user = event['user']
                yield {
                    'event': event['event'],
                    'author': user['login'],
                    'author_name': '',
                    'email': '',
                    'author_type': user['type'],
                    'author_association': event['author_association'],
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': event['body'],
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'assigned':
                author = event['actor'] or {}
                assignees = event['assignee'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': assignees.get('login'),
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'unassigned':
                author = event['actor'] or {}
                assignees = event['assignee'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': assignees.get('login'),
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'closed':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'subscribed':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'unsubscribed':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'merged':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'mentioned':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'connected':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': '',
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'disconnected':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': '',
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'milestoned':
                author = event['actor'] or {}
                milestone = event['milestone'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': milestone['title'],
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'demilestoned':
                author = event['actor'] or {}
                milestone = event['milestone'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': milestone['title'],
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'marked_as_duplicate':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'unmarked_as_duplicate':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'locked':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': event['lock_reason'],
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'unlocked':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'convert_to_draft':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label':'',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'ready_for_review':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'pinned':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label':'',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'unpinned':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'reopened':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'renamed':
                author = event['actor'] or {}
                rename = event['rename'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': rename.get('from'),
                    'body': rename.get('to'),
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'transferred':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'review_requested':
                author = event['actor'] or {}
                requester = event['review_requester'] or {}
                try:
                    reviewer = event['requested_reviewer']['login'] or{} 
                except:
                    reviewer = event['requested_team']['name'] or{} 
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': requester.get('login'),
                    'reviewer': reviewer,
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'review_requested_removed':
                author = event['actor'] or {}
                requester = event['review_requester'] or {}
                try:
                    reviewer = event['requested_reviewer']['login'] or{} 
                except:
                    reviewer = event['requested_team']['name'] or{} 
                
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': requester.get('login'),
                    'reviewer': reviewer,
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'review_dismissed':
                author = event['actor'] or {}
                review = event['dismissed_review'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': review.get('state'),
                    'dismissal_message': review.get('dismissal_message')
                }
            elif event['event'] == 'head_ref_restored':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'head_ref_force_pushed':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'head_ref_deleted':
                author = event['actor'] or {}
                yield {
                    'event': event['event'],
                    'author': author.get('login'),
                    'author_name': '',
                    'email': '',
                    'author_type': author.get('type'),
                    'author_association': '',
                    'commit_id': event['commit_id'],
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'commit-commented':
                comments = event['comments'] or {}
                users = []
                for comment in comments:
                    if comment['user'] != None:
                        users.append(comment['user'])
                    else:
                        users.append({})
                yield {
                    'event': event['event'],
                    'author': ', '.join(str(user.get('login') or '') for user in users),
                    'author_name': '',
                    'email': '',
                    'author_type': ', '.join(str(user.get('type') or '') for user in users),
                    'author_association': ', '.join(comment['author_association'] for comment in comments),
                    'commit_id': ', '.join(comment['commit_id'] for comment in comments),
                    'created_at': ', '.join(comment.get('created_at') for comment in comments),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': ''.join(comment['body'] for comment in comments),
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
            elif event['event'] == 'line-commented':
                comments = event['comments'] or {}
                users = []
                for comment in comments:
                    if comment['user'] != None:
                        users.append(comment['user'])
                    else:
                        users.append({})
                yield {
                    'event': event['event'],
                    'author': ', '.join(str(user.get('login') or '') for user in users),
                    'author_name': '',
                    'email': '',
                    'author_type': ', '.join(str(user.get('type') or '') for user in users),
                    'author_association': ', '.join(comment['author_association'] for comment in comments),
                    'commit_id': ', '.join(comment['commit_id'] for comment in comments),
                    'created_at': ', '.join(comment.get('created_at') for comment in comments),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': ''.join(comment['body'] for comment in comments),
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }            
            else:
                yield {
                    'event': event['event'],
                    'author': '',
                    'author_name': '',
                    'email': '',
                    'author_type': '',
                    'author_association': '',
                    'commit_id': '',
                    'created_at': event.get('created_at'),
                    'id': '',
                    'repo': '',
                    'type': '',
                    'state': '',
                    'assignees': '',
                    'label': '',
                    'body': '',
                    'submitted_at': '',
                    'links': '',
                    'old_name': '',
                    'new_name': '',
                    'requester': '',
                    'reviewer': '',
                    'dismissed_state': '',
                    'dismissal_message': ''
                }
