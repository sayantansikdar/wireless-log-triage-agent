# Scenario: Wi-Fi Authentication Timeout (Reason Code 15)

## Problem Description
A device attempts to connect to a Wi-Fi network but fails during the 4-way handshake, eventually disconnecting with reason code 15.

## Relevant Specifications
- IEEE 802.11 (WLAN MAC and PHY Specifications)

## Expected Investigation Steps
1. The agent should identify the Wi-Fi deauthentication/disassociation reason code 15.
2. The agent should retrieve the meaning of reason code 15 ("4-way handshake timeout") from 802.11 Section 9.4.1.7 (Reason Code field).
3. The agent should deduce that this often indicates a WPA/RSN key exchange failure, possibly due to a wrong password (PSK), interference, or an AP-side drop.

## Log Snippet Context
```
18:45:10.500 wpa_supplicant: wlan0: SME: Trying to authenticate with 00:11:22:33:44:55 (SSID='CorporateNet' freq=5220 MHz)
18:45:10.510 wpa_supplicant: wlan0: SME: Authentication request to the driver failed
18:45:11.000 wpa_supplicant: wlan0: CTRL-EVENT-DISCONNECTED bssid=00:11:22:33:44:55 reason=15
```
