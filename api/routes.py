"""
HTTP routes that delegate to service-layer APIs.
API names match the spreadsheet/documentation.
"""
from typing import Optional

from fastapi import FastAPI

from services import account_subscription, device_location, streaming, reporting

app = FastAPI(title="Video Stream Platform API")


# --- Account & Subscription Management ---

@app.post("/createUser")
def createUser_route(name: str, email: str, plan_id: int):
    account_subscription.createUser(name, email, plan_id)
    return {"ok": True}

@app.post("/modifyUser")
def modifyUser_route(name: str, email: str, plan_id: int):
    account_subscription.modifyUser(name, email, plan_id)
    return {"ok": True}

@app.get("/listUserAccounts")
def listUserAccounts_route():
    return account_subscription.listUserAccounts()


@app.post("/modifySubscriptionPlan")
def modifySubscriptionPlan_route(plan_id: int, name: str, price: float, max_streams: int):
    account_subscription.modifySubscriptionPlan(plan_id, name, price, max_streams)
    return {"ok": True}

@app.post("/createSubscriptionPlan")
def createSubscriptionPlan_route(name: str, price: float, max_streams: int):
    account_subscription.createSubscriptionPlan(name, price, max_streams)
    return {"ok": True}

@app.get("/listSubscriptionPlans")
def listSubscriptionPlans_route():
    return account_subscription.listSubscriptionPlans()



# --- Device & Location Intelligence ---

@app.get("/listDevices")
def listDevices_route(user_id: int):
    return device_location.listDevices(user_id)


@app.get("/listLocations")
def listLocations_route(user_id: int):
    return device_location.listLocations(user_id)


@app.post("/validateDeviceMFA")
def validateDeviceMFA_route(device_id: int, location_id: int, user_home_location_id: Optional[int] = None):
    ok = device_location.validateDeviceMFA(device_id, location_id, user_home_location_id)
    return {"allowed": ok}


# --- Streaming Session & Enforcement ---

@app.post("/attemptStartSession")
def attemptStartSession_route(user_id: int, device_id: int, location_id: int):
    return streaming.attemptStartSession(user_id, device_id, location_id)


@app.post("/trackUserLoginLogout")
def trackUserLoginLogout_route(user_id: int, action: str):
    streaming.trackUserLoginLogout(user_id, action)
    return {"ok": True}


@app.post("/createModifyWatchTime")
def createModifyWatchTime_route(session_id: int, duration_seconds: int):
    streaming.createModifyWatchTime(session_id, duration_seconds)
    return {"ok": True}


@app.get("/listWatchHistory")
def listWatchHistory_route(user_id: int):
    return streaming.listWatchHistory(user_id)


# --- Reporting ---

@app.get("/reportTotalActiveSessions")
def reportTotalActiveSessions_route():
    return {"count": reporting.reportTotalActiveSessions()}


@app.get("/reportSuspiciousActivity")
def reportSuspiciousActivity_route():
    return reporting.reportSuspiciousActivity()
