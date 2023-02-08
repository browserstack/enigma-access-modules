Feature: GithubAccess Grant
    Github Access module grant access feature

    Scenario: Grant Merge Access Success
        Given A git username
        And User exists on github
        And User exists in git org
        And Repository exists on github
        And Access can be granted to user for merge
        When I pass approval request
        Then return value should be True

    Scenario: Grant Push Access Success
        Given A git username
        And User exists on github
        And User exists in git org
        And Repository exists on github
        And Access can be granted to user for push
        When I pass approval request for push
        Then return value should be True

    Scenario: Grant Access Fails
        Given A git username
        And User exists on github
        And User exists in git org
        And Repository exists on github
        And Access cannot be granted to user for push
        When I pass approval request for push
        Then return value should be False
