"""BC Hydro API implementation."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from bs4 import BeautifulSoup
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver

from .const import (
    URL_LOGIN_PAGE,
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
        self._driver = None
        self._authenticated = False
        
        # Cache for data
        self._account: Optional[BCHydroAccount] = None
        self._usage: Optional[BCHydroDailyUsage] = None
        self._latest_point: Optional[BCHydroDailyElectricity] = None

    async def _ensure_browser(self) -> None:
        """Ensure browser is running."""
        if not self._driver:
            options = ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'user-agent={USER_AGENT}')
            
            # Set up wire options for better performance
            wire_options = {
                'connection_timeout': None  # Don't timeout
            }
            
            self._driver = webdriver.Chrome(
                options=options,
                seleniumwire_options=wire_options
            )

    async def _authenticate(self) -> None:
        """Authenticate with BC Hydro."""
        if self._authenticated:
            return

        await self._ensure_browser()

        try:
            self._driver.get(URL_LOGIN_PAGE)

            # Wait for and fill in login form
            username_field = WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self._driver.find_element(By.ID, "password")
            submit_button = self._driver.find_element(By.ID, "loginSubmit")

            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            submit_button.click()

            # Check for error messages
            try:
                error_msg = WebDriverWait(self._driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".alert.error:not(.hidden)"))
                )
                raise BCHydroAuthException(f"Login failed: {error_msg.text}")
            except Exception:
                pass  # No error message found, continue

            # If multiple accounts, select first one
            try:
                account = WebDriverWait(self._driver, 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "accountListDiv"))
                )
                account.click()
            except Exception:
                pass  # No account selection needed

            self._authenticated = True

        except Exception as err:
            self._authenticated = False
            raise BCHydroAuthException(f"Authentication failed: {str(err)}") from err

    async def refresh(self) -> None:
        """Refresh account data."""
        if not self._authenticated:
            await self._authenticate()

        try:
            # Navigate to consumption page and wait for data
            self._driver.find_element(By.ID, "ViewAndPayProfile").click()
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.ID, "consumptionTableSection"))
            )

            # Get latest usage data
            table_section = self._driver.find_element(By.ID, "consumptionTableSection")
            table_html = table_section.get_attribute('outerHTML')
            
            soup = BeautifulSoup(table_html, "html.parser")
            self._check_for_errors(soup)

            # Parse consumption data
            self._usage = self._parse_consumption_data(soup)
            if self._usage and self._usage.electricity:
                self._latest_point = self._usage.electricity[-1]

        except Exception as err:
            self._authenticated = False
            raise BCHydroAuthException(f"Failed to refresh data: {str(err)}") from err

    def _check_for_errors(self, soup: BeautifulSoup) -> None:
        """Check for error messages in the HTML."""
        alerts = soup.select(".alert.error:not(.hidden)")
        if alerts:
            error_msg = " ".join(alert.get_text(strip=True) for alert in alerts)
            raise BCHydroAlertDialogException(f"Alert dialog detected: {error_msg}")

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
            try:
                consumption = float(cells[1].get_text(strip=True))
                cost = float(cells[2].get_text(strip=True).replace("$", "").strip())
            except ValueError:
                continue  # Skip rows with invalid numbers
                
            try:
                date = datetime.strptime(date_str, "%b %d, %Y")
            except ValueError:
                continue  # Skip rows with invalid dates

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

        if not electricity:
            raise BCHydroInvalidHtmlException("No valid consumption data found")

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
        if self._driver:
            self._driver.quit()
