Feature: OpsgenieAccess Grant
    Opsgenie Access module grant access feature

    Scenario: Grant Add user to team Success
        Given an user email
        And User exists on opsgenie
        And Access can be granted to user to add into team
        When I pass approval request for add user to team
        Then return value should be True

    Scenario: Grant Give Admin Access Success
        Given an user email
        And User exists on opsgenie
        And Access can be granted to user to give admin access
        When I pass approval request to give admin access
        Then return value should be True

    Scenario: Grant Access Fails
        Given an user email
        And User exists on opsgenie
        And Access can be granted to user to add into team
        When I pass approval request for add user to team
        Then return value should be False
