Feature: Opsgenie Module Display Teams
    Opsgenie Access module response to the view

    Scenario: View teams list return data
        Given Orgs team list exists
        When View requests data
        Then teams_list is not empty

    Scenario: View Requests Data returns empty
        Given Orgs team list does not exists
        When View requests data
        Then teams_list is empty
