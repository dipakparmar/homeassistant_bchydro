"""BC Hydro API exceptions."""

class BCHydroError(Exception):
    """Base exception for BC Hydro."""

class BCHydroAuthException(BCHydroError):
    """Authentication error with BC Hydro."""

class BCHydroParamException(BCHydroError):
    """Invalid parameter exception."""

class BCHydroInvalidHtmlException(BCHydroError):
    """Invalid HTML response received."""

class BCHydroInvalidXmlException(BCHydroError):
    """Invalid XML response received."""

class BCHydroAlertDialogException(BCHydroError):
    """Alert dialog error detected."""

class BCHydroInvalidDataException(BCHydroError):
    """Invalid data received."""
