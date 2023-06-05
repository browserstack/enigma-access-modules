Feature: GithubAccess Revoke
    Github Access module revoke access feature

    Scenario: Revoke User Access to a repository success
        Given A git username
        And Access will be revoked
        Then Access is revoked

    Scenario: Revoke User Access to a repository fails
        Given A git username
        And Access can not be revoked
        Then Access is not revoked
