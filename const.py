"""BC Hydro Constants."""

DOMAIN = "bchydro"

# Customized user agent for getting the attention of BCHydro devs
USER_AGENT = "https://github.com/dipakparmar/homeassistant_bchydro"

# Main login page. Several redirects follow.
URL_LOGIN_PAGE = "https://app.bchydro.com/BCHCustomerPortal/web/login.html"
URL_POST_LOGIN = "https://app.bchydro.com/sso/UI/Login"
URL_LOGIN_GOTO = "https://app.bchydro.com:443/BCHCustomerPortal/web/login.html"

# Account related URLs
URL_GET_ACCOUNTS = "https://app.bchydro.com/BCHCustomerPortal/web/getAccounts.html"
URL_ACCOUNTS_OVERVIEW = "https://app.bchydro.com/BCHCustomerPortal/web/accountProfile.html"
URL_GET_ACCOUNT_JSON = "https://app.bchydro.com/evportlet/web/global-data.html"
URL_POST_CONSUMPTION_XML = "https://app.bchydro.com/evportlet/web/consumption-data.html"

# Time constants in seconds
FIVE_MINUTES = 300

# Period constants
ENUM_CURRENT_BILLING_PERIOD = "Current billing period"
ENUM_LAST_BILLING_PERIOD = "Last billing period"
ENUM_LAST_7_DAYS = "Last 7 days"
ENUM_LAST_30_DAYS = "Last 30 days"
