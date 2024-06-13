Feature: Reference Commands
    Commands to allow mods to quickly reference rules and resources,
    as well as add new commands of this kind without requiring programmers.
    Background: We are in a server
        Given startup has been run
        Given we are in a server
        Given we've configured the required authorisations
    Scenario Outline: User interacts with the command-editing interface
        Given a user with <privileges> privileges
        When the user <affects> a command
        Then <consequence>
    Examples: Editing
        | privileges      | affects    | consequence            |
        | command-editing | edits      | the command is updated |
        | no              | edits      | the user is informed they don't have the required privileges |
    Examples: Adding
        | privileges      | affects    | consequence            |
        | command-editing | adds       | the command is created |
        | no              | adds       | the user is informed they don't have the required privileges |
    Examples: Removing
        | privileges      | affects    | consequence            |
        | command-editing | removes    | the command is removed |
        | no              | removes    | the user is informed they don't have the required privileges |

    Scenario Outline: User runs a reference command
        Given a set of predefined test commands
        And a <type> user with <privileges> privileges
        When the user runs a test command
        Then <consequence>
    Examples:
        | type      | privileges       | consequence                              |
        | non-admin | no               | the user is informed they don't have the required privileges |
        | admin     | no               | the expected test reference is brought up |
        | non-admin | reference command| the expected test reference is brought up |