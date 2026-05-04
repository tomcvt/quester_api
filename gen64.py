import secrets
import string

def generate_random_string(length=64):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# Generate and print the string
print(generate_random_string())