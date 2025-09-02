import re

def has_port(text: str, port: int) -> bool:
    pattern = rf"(?<!\d):?{port}\b"
    return re.search(pattern, text) is not None


# Example usage
samples = [
    "server on 192.168.1.10:8080",
    "port is 8080 here",
    "bad case 80801 should not match",
    "another case with :8080",
]

for s in samples:
    print(f"{s!r} -> {has_port(s, 8080)}")
