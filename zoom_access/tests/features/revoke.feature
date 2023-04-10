Feature: ZoomAccess Revoke
    Zoom Access module revoke access feature

    Scenario: Revoke User Access to a zoom success
        Given a user email
        And Access will be revoked
        When I pass revoke request
        Then Email will be sent

    Scenario: Revoke User Access to a zoom fails
        Given a user email
        And Access can not be revoked
        When I pass revoke request
        Then Email will be sent
