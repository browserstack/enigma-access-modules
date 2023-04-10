Feature: ZoomAccess User
    Zoom Access user features

    Scenario: User does not exist on zoom
        Given a user email 
        And User does not exist on zoom
        When I pass approval request
        Then return value should be False
