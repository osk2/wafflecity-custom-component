"""API client for Waffle City."""

import logging
from collections.abc import Callable
from typing import Any, TypedDict

import aiohttp

from .const import (
    AUTH_API,
    BIZ_API,
    ENDPOINT_LOGIN,
    ENDPOINT_PARCELS,
    ENDPOINT_PROFILE,
    ENDPOINT_TOKEN_REFRESH,
)

_LOGGER = logging.getLogger(__name__)


class TokenData(TypedDict):
    """Token data structure for persistence."""

    token: str
    user_id: str
    community_ids: list[str]


class WaffleCityAuthError(Exception):
    """Authentication error."""


class WaffleCityApiError(Exception):
    """API error."""


class WaffleCityApi:
    """Waffle City API client."""

    def __init__(
        self,
        phone: str,
        password: str,
        country_code: str = "TW",
        session: aiohttp.ClientSession | None = None,
        on_token_update: Callable[[TokenData], None] | None = None,
    ) -> None:
        """Initialize the API client."""
        self._phone = phone
        self._password = password
        self._country_code = country_code
        self._session = session
        self._token: str | None = None
        self._user_id: str | None = None
        self._community_ids: list[str] = []
        self._owns_session = False
        self._on_token_update = on_token_update

    @property
    def user_id(self) -> str | None:
        """Return the user ID."""
        return self._user_id

    @property
    def community_ids(self) -> list[str]:
        """Return the community IDs."""
        return self._community_ids

    def get_token_data(self) -> TokenData | None:
        """Get current token data for persistence."""
        if not self._token or not self._user_id:
            return None
        return TokenData(
            token=self._token,
            user_id=self._user_id,
            community_ids=self._community_ids,
        )

    def set_token_data(self, data: TokenData) -> None:
        """Restore token data from storage."""
        self._token = data["token"]
        self._user_id = data["user_id"]
        self._community_ids = data["community_ids"]
        _LOGGER.debug("Restored token data for user_id=%s", self._user_id)

    def _notify_token_update(self) -> None:
        """Notify listener of token update."""
        if self._on_token_update and self._token and self._user_id:
            self._on_token_update(
                TokenData(
                    token=self._token,
                    user_id=self._user_id,
                    community_ids=self._community_ids,
                )
            )

    async def validate_token(self) -> bool:
        """Validate if the current token is still valid by fetching profile."""
        if not self._token:
            return False

        try:
            await self._fetch_profile()
            _LOGGER.debug("Token validated successfully")
            return True
        except (WaffleCityApiError, WaffleCityAuthError):
            _LOGGER.debug("Token validation failed")
            return False

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        """Close the session if we own it."""
        if self._owns_session and self._session:
            await self._session.close()
            self._session = None

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = self._token
        return headers

    async def authenticate(self) -> bool:
        """Authenticate with Waffle City."""
        session = await self._get_session()

        payload = {
            "phone": self._phone,
            "password": self._password,
            "country_code": self._country_code,
            "app": "city.waffle.user",
            "manufacturer": "HomeAssistant",
            "model": "HA-Integration",
            "platform": "Linux",
            "os_version": "1.0",
            "app_version": "1.0",
        }

        try:
            async with session.post(
                f"{AUTH_API}{ENDPOINT_LOGIN}",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Linux; HomeAssistant; M2012K11AG Build/AP4A.250105.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.200 Mobile Safari/537.36",
                    "X-Requested-With": "city.waffle.user",
                },
            ) as resp:
                data = await resp.json()

                if data.get("code") != 0:
                    error_msg = data.get("msg", "Authentication failed")
                    _LOGGER.error("Authentication failed: %s", error_msg)
                    raise WaffleCityAuthError(error_msg)

                self._token = data["data"]["token"]
                _LOGGER.debug("Successfully authenticated with Waffle City")

                # Fetch profile to get user_id and community_ids
                await self._fetch_profile()
                self._notify_token_update()
                return True

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error during authentication: %s", err)
            raise WaffleCityApiError(f"Connection error: {err}") from err

    async def _fetch_profile(self) -> None:
        """Fetch user profile to get user_id and community_ids."""
        session = await self._get_session()

        try:
            async with session.get(
                f"{AUTH_API}{ENDPOINT_PROFILE}",
                headers=self._get_headers(),
            ) as resp:
                data = await resp.json()

                # Handle token expiration
                if data.get("code") == 401:
                    raise WaffleCityAuthError("Token expired")

                if data.get("code") != 0:
                    error_msg = data.get("msg", "Failed to fetch profile")
                    _LOGGER.error("Failed to fetch profile: %s", error_msg)
                    raise WaffleCityApiError(error_msg)

                profile = data["data"]
                self._user_id = profile["user_id"]

                # Extract unique community IDs from groups
                self._community_ids = list(
                    {
                        g["community_id"]
                        for g in profile.get("groups", [])
                        if g.get("community_id")
                    }
                )

                _LOGGER.debug(
                    "Profile fetched: user_id=%s, communities=%s",
                    self._user_id,
                    self._community_ids,
                )

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error fetching profile: %s", err)
            raise WaffleCityApiError(f"Connection error: {err}") from err

    async def refresh_token(self) -> bool:
        """Refresh the authentication token."""
        if not self._token:
            return await self.authenticate()

        session = await self._get_session()

        try:
            async with session.patch(
                f"{AUTH_API}{ENDPOINT_TOKEN_REFRESH}",
                headers=self._get_headers(),
            ) as resp:
                data = await resp.json()

                if data.get("code") != 0:
                    _LOGGER.warning("Token refresh failed, re-authenticating")
                    return await self.authenticate()

                self._token = data["data"]["token"]
                _LOGGER.debug("Token refreshed successfully")
                self._notify_token_update()
                return True

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error refreshing token: %s", err)
            raise WaffleCityApiError(f"Connection error: {err}") from err

    async def get_packages(self) -> list[dict[str, Any]]:
        """Fetch all packages for the user."""
        if not self._token or not self._user_id:
            raise WaffleCityApiError("Not authenticated")

        session = await self._get_session()

        params = {}
        if self._community_ids:
            params["community_ids"] = ",".join(self._community_ids)

        endpoint = ENDPOINT_PARCELS.format(user_id=self._user_id)

        try:
            async with session.get(
                f"{BIZ_API}{endpoint}",
                headers=self._get_headers(),
                params=params,
            ) as resp:
                data = await resp.json()

                # Handle token expiration
                if data.get("code") == 401:
                    _LOGGER.info("Token expired, refreshing...")
                    await self.refresh_token()
                    return await self.get_packages()

                if data.get("code") != 0:
                    error_msg = data.get("msg", "Failed to fetch packages")
                    _LOGGER.error("Failed to fetch packages: %s", error_msg)
                    raise WaffleCityApiError(error_msg)

                packages = data.get("data", [])
                _LOGGER.debug("Fetched %d packages", len(packages))
                _LOGGER.debug("Packages data: %s", packages)
                return packages

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error fetching packages: %s", err)
            raise WaffleCityApiError(f"Connection error: {err}") from err

    async def get_pending_packages(self) -> list[dict[str, Any]]:
        """Get packages that have not been picked up."""
        packages = await self.get_packages()
        pending = [
            p for p in packages
            if not p.get("pickup", False)
        ]
        _LOGGER.debug("Found %d pending packages", len(pending))
        return pending
