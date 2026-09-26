# Scenario: Tracking Area Update (TAU) Reject (Cause #10)

## Problem Description
A UE moves into a new area and attempts to perform a Tracking Area Update (TAU). The network responds with a `TRACKING AREA UPDATE REJECT` carrying EMM cause #10. The device drops connection.

## Relevant Specifications
- 3GPP TS 24.301 (NAS protocol for EPS)

## Expected Investigation Steps
1. The agent should identify the EMM cause code 10.
2. The agent should retrieve the exact meaning of cause #10 ("Implicitly detached") from 24.301.
3. The agent should explain that the network considers the UE detached (often due to inactivity timer mismatches or core network sync issues) and that the UE must initiate a new Attach procedure.

## Log Snippet Context
```
09:15:22.001 [NAS] Tx TRACKING AREA UPDATE REQUEST (GUTI=...)
09:15:22.210 [NAS] Rx TRACKING AREA UPDATE REJECT (EMM Cause: 10)
09:15:22.215 [NAS] EMM state changed to EMM-DEREGISTERED.NORMAL-SERVICE
```
