"""
Command-line driver for the Video Streaming Platform.
Usage: python driver.py
"""
from services import account_subscription, device_location, streaming, reporting


# ─── Server layer (calls service functions) ───────────────────────────────────

def Server_listSubscriptionPlans():
    return account_subscription.listSubscriptionPlans()

def Server_listUserAccounts():
    return account_subscription.listUserAccounts()

def Server_listDevices(email):
    return device_location.listDevicesByEmail(email)

def Server_listLocationsByEmail(email):
    return device_location.listLocationsByEmail(email)

def Server_attemptStartSession(email, device_fingerprint, latitude, longitude):
    return streaming.attemptStartSession(email, device_fingerprint, latitude, longitude)

def Server_attemptEndSession(email, device_fingerprint):
    return streaming.attemptEndSession(email, device_fingerprint)

def Server_reportTotalActiveSessions():
    return reporting.reportTotalActiveSessions()

def Server_reportSuspiciousActivity():
    return reporting.reportSuspiciousActivity()


# ─── Client layer (prompts user, calls Server, prints result) ─────────────────

def Client_listSubscriptionPlans():
    result = Server_listSubscriptionPlans()
    print("\n--- Subscription Plans ---")
    for plan in result:
        print(f"  {plan['name']:10}  ${plan['price']:>6}  max_streams={plan['max_streams']}")

def Client_listUserAccounts():
    result = Server_listUserAccounts()
    print(f"\n--- User Accounts ({len(result)} total) ---")
    for u in result:
        print(f"  [{u['user_id']}] {u['name']:25}  {u['email']}")

def Client_listDevices():
    email = input("  Enter user email: ").strip()
    result = Server_listDevices(email)
    print(f"\n--- Devices for {email} ---")
    if not result:
        print("  No devices found.")
    for d in result:
        trusted = "TRUSTED" if d["is_trusted"] else "not trusted"
        print(f"  [{d['device_id']}] {d['name']:12} ({d['device_type'] or 'unknown type'})  {trusted}")

def Client_listLocationsByEmail():
    email = input("  Enter user email: ").strip()
    result = Server_listLocationsByEmail(email)
    print(f"\n--- Locations for {email} ---")
    if not result:
        print("  No locations found.")
    for loc in result:
        print(f"  {loc['description']:25}  lat={loc['latitude']}  lon={loc['longitude']}")

def Client_attemptStartSession():
    email            = input("  Enter user email: ").strip()
    device_fp        = input("  Enter device fingerprint: ").strip()
    latitude         = float(input("  Enter latitude: ").strip())
    longitude        = float(input("  Enter longitude: ").strip())
    granted, reason  = Server_attemptStartSession(email, device_fp, latitude, longitude)
    print("\n--- attemptStartSession Result ---")
    if granted:
        print("  GRANTED: session started successfully.")
    else:
        print(f"  DENIED: {reason}")

def Client_attemptEndSession():
    email     = input("  Enter user email: ").strip()
    device_fp = input("  Enter device fingerprint: ").strip()
    ok        = Server_attemptEndSession(email, device_fp)
    print("\n--- attemptEndSession Result ---")
    print("  Session ended." if ok else "  No active session found.")

def Client_reportTotalActiveSessions():
    count = Server_reportTotalActiveSessions()
    print(f"\n--- Total Active Sessions: {count} ---")

def Client_reportSuspiciousActivity():
    emails = Server_reportSuspiciousActivity()
    print("\n--- Suspicious Activity (>2 active sessions) ---")
    if not emails:
        print("  None detected.")
    for e in emails:
        print(f"  {e}")


# ─── Menu ─────────────────────────────────────────────────────────────────────

MENU = [
    ("listSubscriptionPlans",   Client_listSubscriptionPlans),
    ("listUserAccounts",        Client_listUserAccounts),
    ("listDevices",             Client_listDevices),
    ("listLocationsByEmail",    Client_listLocationsByEmail),
    ("attemptStartSession",     Client_attemptStartSession),
    ("attemptEndSession",       Client_attemptEndSession),
    ("reportTotalActiveSessions", Client_reportTotalActiveSessions),
    ("reportSuspiciousActivity",  Client_reportSuspiciousActivity),
]

def show_menu():
    print("\n========================================")
    print("   Video Streaming Platform — APIs")
    print("========================================")
    for i, (name, _) in enumerate(MENU, 1):
        print(f"  {i}. {name}")
    print("  0. Exit")
    print("----------------------------------------")

def main():
    while True:
        show_menu()
        choice = input("Select an API (0 to exit): ").strip()
        if choice == "0":
            print("Goodbye.")
            break
        if not choice.isdigit() or not (1 <= int(choice) <= len(MENU)):
            print("  Invalid choice, try again.")
            continue
        _, client_fn = MENU[int(choice) - 1]
        try:
            client_fn()
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    main()
