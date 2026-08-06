from tools.email import draft_email, read_recent_emails

print(draft_email("your-own-email@gmail.com", "FitEdge test", "This is a test draft from FitEdge."))
print(read_recent_emails(3))