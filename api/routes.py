"""
HTTP routes that delegate to service-layer APIs.
API names match the spreadsheet/documentation.
"""
from fastapi import FastAPI

from services import account_subscription, device_location, streaming, reporting

app = FastAPI(title="Video Stream Platform API")


# --- Account & Subscription Management ---

@app.post("/createUser")
def createUser_route(name: str, email: str, plan_id: int, status_id: int):
    account_subscription.createUser(name, email, plan_id, status_id)
    return {"ok": True}

@app.post("/updateUserByEmail")
def updateUserByEmail_route(email: str, newName: str, newPlanName: str, newAccountStatus: str):
    account_subscription.updateUserByEmail(email, newName, newPlanName, newAccountStatus)
    return {"ok": True}

@app.get("/listUserAccounts")
def listUserAccounts_route():
    return account_subscription.listUserAccounts()


@app.post("/modifySubscriptionPlan")
def modifySubscriptionPlan_route(name: str, price: float, max_streams: int):
    account_subscription.modifySubscriptionPlan(name, price, max_streams)
    return {"ok": True}

@app.post("/createSubscriptionPlan")
def createSubscriptionPlan_route(name: str, price: float, max_streams: int):
    account_subscription.createSubscriptionPlan(name, price, max_streams)
    return {"ok": True}

@app.get("/listSubscriptionPlans")
def listSubscriptionPlans_route():
    return account_subscription.listSubscriptionPlans()


# --- Device & Location Intelligence ---

@app.post("/addDevice")
def addDevice_route(email: str, name: str, device_fingerprint: str):
    device_location.addDeviceByEmail(email, name, device_fingerprint)
    return {"ok": True}

@app.get("/listDevices")
def listDevices_route(email: str):
    return device_location.listDevices(email)

@app.get("/listLocations")
def listLocations_route(email: str):
    return device_location.listLocations(email)


# --- Streaming Session & Enforcement ---

@app.post("/attemptStartSession")
def attemptStartSession_route(
    email: str,
    device_fingerprint: str,
    latitude: float,
    longitude: float,
):
    granted = streaming.attemptStartSession(email, device_fingerprint, latitude, longitude)
    return {"granted": granted}


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
    return reporting.reportSuspiciousActivity()
