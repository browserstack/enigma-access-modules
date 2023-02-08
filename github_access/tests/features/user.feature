Feature: GithubAccess User
    Github Access user features

    Scenario: User does not exist on github
        Given A git username
        And User does not exist on github
        When I pass approval request
        Then return value should be False

    Scenario: Invite user to organisation fails
        Given A git username
        And User exists on github
        And User does not exist in git org
        And User is not invited to org
        And User cannot be added to the org
        When I pass approval request
        Then return value should be False

    Scenario: User is already invited to organisation
        Given A git username
        And User exists on github
        And User does not exist in git org
        And User is invited to org
        When I pass approval request
        Then return value should be False

    Scenario: Invite user to organisation is success
        Given A git username
        And User exists on github
        And User does not exist in git org
        And User is not invited to org
        And User can be added to the org
        When I pass approval request
        Then return value should be False

    Scenario: Repository does not exist on github
        Given A git username
        And User exists on github
        And User exists in git org
        And Repository does not exist on github
        When I pass approval request
        Then return value should be False
