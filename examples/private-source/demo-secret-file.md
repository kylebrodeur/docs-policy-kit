A secret-shaped demo: this file exists so the test suite and the README
can demonstrate the secret gate refusing an allowlisted file. The token
below is a synthetic example, not a real key anywhere:

    apiKey = "EXAMPLE-DEMO-NOT-SECRET-12345"

The pattern class it trips is the long literal assignment to a
secret-sounding name (see the SECRET_PATTERNS tuple in docpol/config.py).