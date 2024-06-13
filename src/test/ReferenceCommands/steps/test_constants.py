from unittest.mock import MagicMock,Mock,NonCallableMock,NonCallableMagicMock
import discord as dcd

## Constant placeholder roles
EDITCOMMAND_ROLE = NonCallableMagicMock(dcd.Role)
EDITCOMMAND_ROLE.configure_mock(
    id=0
)
REFERENCE_ROLE = NonCallableMagicMock(dcd.Role)
REFERENCE_ROLE.configure_mock(
    id=1
)