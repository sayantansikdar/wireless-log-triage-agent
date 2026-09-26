# Scenario: EMM Attach Reject (Cause #15)

## Problem Description
A UE (User Equipment) is attempting to attach to the LTE network but is repeatedly receiving an `ATTACH REJECT` message with EMM cause code 15. The device fails to gain service.

## Relevant Specifications
- 3GPP TS 24.301 (Non-Access-Stratum (NAS) protocol for Evolved Packet System (EPS))

## Expected Investigation Steps
1. The agent should identify the EMM cause code 15.
2. The agent should retrieve the exact meaning of cause #15 ("No Suitable Cells In tracking area") from the cause code tables in 24.301 section 5.5.1.2.5 or Annex A.
3. The agent should summarize the network's rationale for the rejection and suggest what the UE should do next (e.g., attempt to attach to a different tracking area or RAT).

## Log Snippet Context
```
14:32:01.123 [NAS] Tx ATTACH REQUEST (IMSI=001011234567890)
14:32:01.450 [NAS] Rx ATTACH REJECT (EMM Cause: 15)
14:32:01.455 [NAS] EMM state changed to EMM-DEREGISTERED.PLMN-SEARCH
```
