"""
HTTP routes that delegate to service-layer APIs.
API names match the spreadsheet/documentation.
"""
from fastapi import FastAPI, HTTPException

from services import account_subscription, device_location, streaming, reporting

app = FastAPI(title="Video Stream Platform API")


# --- Account & Subscription Management ---

@app.post("/createUserAccount")
def createUserAccount_route(
    name: str,
    email: str,
    planName: str,
    latitude: float = None,
    longitude: float = None,
):
    ok = account_subscription.createUserAccount(name, email, planName, latitude, longitude)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Account creation failed. Ensure the plan exists (createSubscriptionPlan), that account status 'active' exists (e.g. run seed_sample_data.py), and that name/email are unique.",
        )
    return {"ok": True}


@app.post("/createUser")
def createUser_route(name: str, email: str, plan_id: int, status_id: int):
    account_subscription.createUser(name, email, plan_id, status_id)
    return {"ok": True}


@app.post("/updateUserByEmail")
def updateUserByEmail_route(
    email: str,
    newName: str,
    newPlanName: str,
    newAccountStatus: str,
    homeLocID: int = None,
):
    ok = account_subscription.updateUserByEmail(
        email, newName, newPlanName, newAccountStatus, homeLocID
    )
    return {"ok": ok}


@app.get("/listUserAccounts")
def listUserAccounts_route():
    return account_subscription.listUserAccounts()


@app.post("/modifySubscriptionPlan")
def modifySubscriptionPlan_route(name: str, price: float, max_streams: int):
    ok = account_subscription.modifySubscriptionPlan(name, price, max_streams)
    return {"ok": ok}


@app.post("/createSubscriptionPlan")
def createSubscriptionPlan_route(name: str, price: float, max_streams: int):
    ok = account_subscription.createSubscriptionPlan(name, price, max_streams)
    return {"ok": ok}


@app.get("/querySubscriptionPlan")
def querySubscriptionPlan_route(plan_id: int):
    plan = account_subscription.querySubscriptionPlan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@app.get("/listSubscriptionPlans")
def listSubscriptionPlans_route():
    return account_subscription.listSubscriptionPlans()


# --- Device & Location Intelligence ---

@app.post("/addDeviceToAccount")
def addDeviceToAccount_route(
    email: str,
    deviceName: str,
    deviceType: str,
    deviceFingerprint: str,
):
    device_id = device_location.addDeviceToAccount(
        email, deviceName, deviceType, deviceFingerprint
    )
    return {"device_id": device_id}


@app.post("/addDevice")
def addDevice_route(email: str, name: str, device_fingerprint: str):
    device_location.addDeviceByEmail(email, name, device_fingerprint)
    return {"ok": True}


@app.post("/addLocation")
def addLocation_route(latitude: float, longitude: float):
    location_id = device_location.addLocation(latitude, longitude)
    return {"location_id": location_id}


@app.get("/listDevices")
def listDevices_route(email: str):
    return device_location.listDevicesByEmail(email)


@app.get("/listLocations")
def listLocations_route(email: str):
    return device_location.listLocationsByEmail(email)


# --- Streaming Session & Enforcement ---

@app.post("/attemptStartSession")
def attemptStartSession_route(
    email: str,
    device_fingerprint: str,
    latitude: float,
    longitude: float,
):
    granted, reason = streaming.attemptStartSession(email, device_fingerprint, latitude, longitude)
    out = {"granted": granted}
    if not granted and reason:
        out["reason"] = reason
    return out


@app.post("/attemptEndSession")
def attemptEndSession_route(email: str, deviceFingerprint: str):
    ok = streaming.attemptEndSession(email, deviceFingerprint)
    return {"ok": ok}


@app.post("/trackUserLoginLogout")
def trackUserLoginLogout_route(email: str, action: str):
    streaming.trackUserLoginLogoutByEmail(email, action)
    return {"ok": True}


@app.post("/createModifyWatchTime")
def createModifyWatchTime_route(session_id: int, duration_seconds: int):
    streaming.createModifyWatchTime(session_id, duration_seconds)
    return {"ok": True}


@app.get("/listWatchHistory")
def listWatchHistory_route(email: str):
    return streaming.listWatchHistoryByEmail(email)


# --- Reporting ---

@app.get("/reportTotalActiveSessions")
def reportTotalActiveSessions_route():
    return {"count": reporting.reportTotalActiveSessions()}


@app.get("/reportSuspiciousActivity")
def reportSuspiciousActivity_route():
    emails = reporting.reportSuspiciousActivity()
    return {"emails": emails}
