Feature: Github Module Display Repos
    Github Access module response to the view

    Scenario: View Requests Data returns data
        Given Orgs repo list exists
        When View requests data
        Then githubRepoList is not empty

    Scenario: View Requests Data returns empty
        Given Orgs repo list does not exist
        When View requests data
        Then githubRepoList is empty

    Scenario: View Validates Request
        When View requests validation
        Then validated request is returned
