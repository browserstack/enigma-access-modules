This document has info regarding Opsgenie Module.

### What it does
- Module is responsible for adding a user into opsgenie team either as a member or as an admin.

### Config Parameters:
Parameter | Type | Required | Description
--- | ---| --- | ---
`OPSGENIE_TOKEN` | `STRING` | `True` | API Key that allows to add the users to the opsgenie teams. To create the key refer to [this](https://support.atlassian.com/opsgenie/docs/api-key-management/)
`IGNORE_TEAMS` | `Array` | `False` (Set it to empty array if not configured) | List of teams that admin dont want all the enigma users to join.
