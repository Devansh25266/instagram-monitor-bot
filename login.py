import instaloader

L = instaloader.Instaloader()

USERNAME = "trackerbotnew"
PASSWORD = "dev667788"

try:

    L.login(USERNAME, PASSWORD)

except instaloader.exceptions.TwoFactorAuthRequiredException:

    code = input("Enter 2FA Code: ")

    L.two_factor_login(code)

L.save_session_to_file()

print("Session saved successfully!")