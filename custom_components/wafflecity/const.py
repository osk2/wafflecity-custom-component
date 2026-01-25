"""Constants for the Waffle City integration."""

DOMAIN = "wafflecity"

# API URLs
AUTH_API = "https://prod.wafflecity.one/auth"
BIZ_API = "https://prod.wafflecity.one/biz"

# API Endpoints
ENDPOINT_LOGIN = "/v2/users/phone/login"
ENDPOINT_PROFILE = "/v2/users/profile"
ENDPOINT_TOKEN_REFRESH = "/v2/users/tokens/refresh"
ENDPOINT_PARCELS = "/v4/packages/users/{user_id}/parcels"

# Configuration keys
CONF_PHONE = "phone"
CONF_PASSWORD = "password"
CONF_COUNTRY_CODE = "country_code"

# Defaults
DEFAULT_COUNTRY_CODE = "TW"
DEFAULT_SCAN_INTERVAL = 900  # 15 minutes in seconds

# Supported country codes
COUNTRY_CODES = [
    "TW",  # Taiwan
    "CN",  # China
    "HK",  # Hong Kong
    "MO",  # Macau
    "JP",  # Japan
    "KR",  # South Korea
    "TH",  # Thailand
    "SG",  # Singapore
    "MY",  # Malaysia
    "ID",  # Indonesia
    "VN",  # Vietnam
    "PH",  # Philippines
    "AU",  # Australia
    "IN",  # India
]
