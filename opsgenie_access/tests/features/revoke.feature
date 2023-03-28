Feature: OpsgenieAccess Revoke
    Opsgenie Access module revoke access feature

    Scenario: Revoke User Access to a opsgenie success
        Given a user email
        And Access will be revoked
        When I pass revoke request
        Then Approved Email will be sent

    Scenario: Revoke User Access to a opsgenie fails
        Given a user email
        And Access can not be revoked
        When I pass revoke request
        Then Grantfailed Email will be sent
