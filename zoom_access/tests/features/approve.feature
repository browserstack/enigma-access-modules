Feature: ZoomAccess Grant
  Zoom Access module grant access feature

  Scenario: Grant Standard Access Success
        Given an user email
        And User exists on zoom
        And Access can be granted to user for Standard access
        When I pass approval request for Standard access
        Then return value should be True

  Scenario: Grant Pro License Access Success
        Given an user email
        And User exists on zoom
        And Access can be granted to user for Pro access
        When I pass approval request for Pro access
        Then return value should be True

  Scenario: Grant Access Fails
        Given an user email
        And User exists on zoom
        And Access cannot be granted to user for Standard access
        When I pass approval request for Standard access
        Then return value should be False
