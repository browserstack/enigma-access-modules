Feature: OpsgenieAccess User
    Opsgenie Access user features

    Scenario: User does not exist on Opsgenie
        Given A user_email
        And User does not exist on Opsgenie
        When I pass approval request
        Then return value should be False

    Scenario: Add user to Opsgenie success
        Given A user_email
        And a name
        And a role
        And User does not exist on Opsgenie
        And User can be added to Opsgenie
        And User can be added to Opsgenie team
        When I pass approval request for adding user to opsgenie
        Then return value should be true

    Scenario: Add user to Opsgenie fails
        Given A user_email
        And a name
        And a role
        And User does not exist on Opsgenie
        When I pass approval request for adding user to opsgenie
        Then return value should be False

