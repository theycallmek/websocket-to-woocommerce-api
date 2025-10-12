import argparse
import os
import httpx
from dotenv import load_dotenv

# --- INSTRUCTIONS ---
# 1. Make sure you have python-dotenv and httpx installed:
#    pip install python-dotenv httpx
#
# 2. Create a file named .env in the same directory as this script.
#
# 3. Add your credentials and WordPress URL to the .env file:
#    WP_URL=https://your-wordpress-site.com
#    ROYALAUTH_API_KEY=your_application_api_key
#    ROYALAUTH_API_SECRET=your_application_api_secret
#
# 4. Run the script from your terminal with an action:
#    python wp-user-client-emulation.py status
#    python wp-user-client-emulation.py activate
#    python wp-user-client-emulation.py deactivate
# --------------------

def main():
    """
    Main function to run the client emulation script.
    """
    # Load environment variables from .env file
    load_dotenv()
    wp_url = os.getenv("WP_URL")
    api_key = os.getenv("ROYALAUTH_API_KEY")
    api_secret = os.getenv("ROYALAUTH_API_SECRET")

    # Check if all required environment variables are set
    if not all([wp_url, api_key, api_secret]):
        print("Error: Missing required environment variables.")
        print("Please ensure WP_URL, ROYALAUTH_API_KEY, and ROYALAUTH_API_SECRET are set in your .env file.")
        return

    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Emulate a client for the RoyalAuth WordPress plugin API.")
    parser.add_argument(
        "action",
        choices=["status", "activate", "deactivate"],
        help="The license action to perform."
    )
    args = parser.parse_args()

    # Construct the API endpoint URL
    api_url = f"{wp_url}/wp-json/royalauth/v1/license/{args.action}"

    # Prepare the data payload
    payload = {
        "api_key": api_key,
        "api_secret": api_secret
    }

    print(f"Sending '{args.action}' request to: {api_url}")

    try:
        # Make the POST request
        with httpx.Client() as client:
            response = client.post(api_url, json=payload, timeout=15)

        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # Print the successful response
        print("\n--- Success ---")
        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        print(response.json())

    except httpx.HTTPStatusError as e:
        print("\n--- Error ---")
        print(f"HTTP Error occurred: {e.response.status_code} - {e.response.reason_phrase}")
        print("Response JSON:")
        try:
            print(e.response.json())
        except Exception:
            print(e.response.text)

    except httpx.RequestError as e:
        print("\n--- Error ---")
        print(f"An error occurred while requesting {e.request.url!r}.")
        print("Please check the WP_URL in your .env file and your internet connection.")

if __name__ == "__main__":
    main()