"""BC Hydro API implementation."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page

from .const import (
    ENUM_CURRENT_BILLING_PERIOD,
    URL_LOGIN_PAGE,
    URL_POST_LOGIN,
    USER_AGENT,
)
from .exceptions import (
    BCHydroAuthException,
    BCHydroInvalidHtmlException,
    BCHydroAlertDialogException,
)
from .types import (
    BCHydroAccount,
    BCHydroDailyElectricity,
    BCHydroInterval,
    BCHydroRates,
    BCHydroDailyUsage,
)

_LOGGER = logging.getLogger(__name__)

class BCHydroApi:
    """BC Hydro API client."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize the API client."""
        self.username = username
        self.password = password
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._authenticated = False
        
        # Cache for data
        self._account: Optional[BCHydroAccount] = None
        self._usage: Optional[BCHydroDailyUsage] = None
        self._latest_point: Optional[BCHydroDailyElectricity] = None

    async def _ensure_browser(self) -> None:
        """Ensure browser is running."""
        if not self._browser:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True,
            )
            self._page = await self._browser.new_page(
                user_agent=USER_AGENT,
            )

    async def _authenticate(self) -> None:
        """Authenticate with BC Hydro."""
        if self._authenticated:
            return

        await self._ensure_browser()
        if not self._page:
            raise BCHydroAuthException("Browser page not initialized")

        try:
            # Navigate to login page
            await self._page.goto(URL_LOGIN_PAGE)

            # Fill in login form
            await self._page.fill("#username", self.username)
            await self._page.fill("#password", self.password)

            # Click submit and wait for navigation
            await asyncio.gather(
                self._page.wait_for_navigation(),
                self._page.click("#loginSubmit"),
            )

            # Check for error messages
            error_msg = await self._page.query_selector(".alert.error:not(.hidden)")
            if error_msg:
                error_text = await error_msg.text_content()
                raise BCHydroAuthException(f"Login failed: {error_text}")

            # If multiple accounts, select first one
            account_list = await self._page.query_selector_all(".accountListDiv")
            if account_list:
                await account_list[0].click()

            self._authenticated = True

        except Exception as err:
            self._authenticated = False
            raise BCHydroAuthException(f"Authentication failed: {str(err)}") from err

    async def _validate_html(self, html: str) -> BeautifulSoup:
        """Validate HTML response."""
        if not html:
            raise BCHydroInvalidHtmlException("Empty HTML response")

        soup = BeautifulSoup(html, "html.parser")
        
        # Check for alert dialogs
        alerts = soup.select(".alert.error:not(.hidden)")
        if alerts:
            error_msg = " ".join(alert.get_text(strip=True) for alert in alerts)
            raise BCHydroAlertDialogException(f"Alert dialog detected: {error_msg}")

        return soup

    async def refresh(self) -> None:
        """Refresh account data."""
        if not self._authenticated:
            await self._authenticate()

        try:
            # Navigate to consumption page
            await self._page.click("#ViewAndPayProfile")
            await self._page.wait_for_selector("#consumptionTableSection")

            # Get latest usage data
            table_html = await self._page.inner_html("#consumptionTableSection")
            soup = await self._validate_html(table_html)

            # Parse consumption data
            self._usage = self._parse_consumption_data(soup)
            if self._usage and self._usage.electricity:
                self._latest_point = self._usage.electricity[-1]

        except Exception as err:
            self._authenticated = False
            raise BCHydroAuthException(f"Failed to refresh data: {str(err)}") from err

    def _parse_consumption_data(self, soup: BeautifulSoup) -> BCHydroDailyUsage:
        """Parse consumption data from HTML."""
        table = soup.find(id="consumptionTable")
        if not table:
            raise BCHydroInvalidHtmlException("Consumption table not found")

        # Parse consumption rows
        electricity = []
        for row in table.find_all("tr")[1:]:  # Skip header row
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            date_str = cells[0].get_text(strip=True)
            consumption = float(cells[1].get_text(strip=True))
            cost = float(cells[2].get_text(strip=True).replace("$", ""))
            
            date = datetime.strptime(date_str, "%b %d, %Y")
            interval = BCHydroInterval(
                start=date,
                end=date,
            )

            electricity.append(
                BCHydroDailyElectricity(
                    consumption=consumption,
                    cost=cost,
                    interval=interval,
                )
            )

        # Create usage object
        return BCHydroDailyUsage(
            account=self._account,
            interval=BCHydroInterval(
                start=electricity[0].interval.start,
                end=electricity[-1].interval.end,
            ),
            rates=BCHydroRates(
                step1_rate=0.0954,  # Current BC Hydro Step 1 rate
                step2_rate=0.1427,  # Current BC Hydro Step 2 rate
                threshold=1332.0,   # Current threshold in kWh
            ),
            electricity=electricity,
        )

    async def get_latest_usage(self) -> float:
        """Get latest usage value."""
        if not self._latest_point:
            await self.refresh()
        return self._latest_point.consumption if self._latest_point else 0.0

    async def get_latest_cost(self) -> float:
        """Get latest cost value."""
        if not self._latest_point:
            await self.refresh()
        return self._latest_point.cost if self._latest_point else 0.0

    async def get_latest_interval(self) -> Dict:
        """Get latest interval information."""
        if not self._latest_point:
            await self.refresh()
        return {
            "start": self._latest_point.interval.start if self._latest_point else None,
            "end": self._latest_point.interval.end if self._latest_point else None,
            "billing_period_end": self._latest_point.interval.billing_period_end if self._latest_point else None,
        }

    async def __aenter__(self):
        """Async enter."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit."""
        if self._browser:
            await self._browser.close()
