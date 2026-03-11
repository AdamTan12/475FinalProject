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


@app.post("/createModifyPaymentInfo")
def createModifyPaymentInfo_route(email: str, amount: float, status: str = "Pending"):
    account_subscription.createModifyPaymentInfoByEmail(email, amount, status)
    return {"ok": True}


@app.get("/reportMonthlyRevenue")
def reportMonthlyRevenue_route(month: int, year: int):
    return {"total": account_subscription.reportMonthlyRevenue(month, year)}


# --- Device & Location Intelligence ---

@app.get("/listDevices")
def listDevices_route(email: str):
    return device_location.listDevices(email)


@app.get("/listLocations")
def listLocations_route(email: str):
    return device_location.listLocations(email)


@app.post("/validateDeviceMFA")
def validateDeviceMFA_route(device_id: int, location_id: int, user_home_location_id: Optional[int] = None):
    ok = device_location.validateDeviceMFA(device_id, location_id, user_home_location_id)
    return {"allowed": ok}


# --- Streaming Session & Enforcement ---

@app.post("/attemptStateSession")
def attemptStateSession_route(
    email: str,
    device_fingerprint: str,
    latitude: float,
    longitude: float,
    ip_address: str,
):
    granted = streaming.attemptStateSession(
        email, device_fingerprint, latitude, longitude, ip_address
    )
    return {"granted": granted}


@app.post("/attemptStartSession")
def attemptStartSession_route(user_id: int, device_id: int, location_id: int):
    return streaming.attemptStartSession(user_id, device_id, location_id)


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
