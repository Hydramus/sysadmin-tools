import os
import csv
import datetime
import argparse
from pdpyras import APISession, PDClientError

# Set up the argument parser
parser = argparse.ArgumentParser(
    description="PagerDuty Incident Report Script",
    epilog="Ensure you have set the PD_API_KEY environment variable before running the script."
)
parser.add_argument(
    "--email",
    required=True,
    help="The email address to use as the default sender."
)

# Parse the arguments
args = parser.parse_args()

# Retrieve the API key from environment variables
api_key = os.environ.get('PD_API_KEY')
if not api_key:
    parser.error("PD_API_KEY environment variable not set. "
                 "Please set it by running 'export PD_API_KEY=\"your_api_key_here\"'.")

# Use the email argument provided in the command line
default_email = args.email

# Ask the user if they want verbose output
verbose = input("Do you want verbose output? (yes/no): ").lower() == "yes"

# Create the API session with the provided email
session = APISession(api_key, default_from=default_email)

# Define the start and end dates for the time range
start_date = datetime.datetime(2022, 8, 22)
end_date = datetime.datetime.now()

# Calculate the number of days between the start and end dates
num_days = (end_date - start_date).days

# Get the current date for the filename
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
filename = f'pagerduty-incidents-report_{current_date}.csv'

# Open a CSV file for writing
with open(filename, 'w', newline='') as csvfile:
    fieldnames = ['id', 'status', 'priority', 'urgency', 'title', 'created', 'service', 'assigned_to', 'url', 'duration']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    # Write the header row
    writer.writeheader()

    # Loop over each day in the time range
    for i in range(num_days):
        # Calculate the 'since' and 'until' parameters for this day
        since = (start_date + datetime.timedelta(days=i)).isoformat()
        until = (start_date + datetime.timedelta(days=i+1)).isoformat()

        # Retrieve incidents for this day
        try:
            for incident in session.iter_all('incidents', params={'since': since, 'until': until}):
                # Calculate the duration of the incident
                created_at = datetime.datetime.strptime(incident['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                resolved_at = datetime.datetime.strptime(incident['last_status_change_at'], "%Y-%m-%dT%H:%M:%SZ") if incident['status'] == 'resolved' else datetime.datetime.now()
                duration = resolved_at - created_at

                # Write the incident details to the CSV file
                writer.writerow({
                    'id': incident['id'],
                    'status': incident['status'],
                    'priority': incident['priority']['name'] if incident['priority'] and incident['priority'].get('name') else '',
                    'urgency': incident['urgency'],
                    'title': incident['title'],
                    'created': incident['created_at'],
                    'service': incident['service']['name'] if incident['service'] and incident['service'].get('name') else '',
                    'assigned_to': ', '.join([assignment['assignee']['name'] for assignment in incident['assignments'] if assignment['assignee'] and assignment['assignee'].get('name')]),
                    'url': f"https://app.pagerduty.com/incidents/{incident['id']}",
                    'duration': str(duration)
                })

                # If verbose output is enabled, print the incident details
                if verbose:
                    print(f"Exported incident {incident['id']} with status '{incident['status']}', priority '{incident['priority']['name'] if incident['priority'] and incident['priority'].get('name') else ''}', urgency '{incident['urgency']}', title '{incident['title']}', created at '{incident['created_at']}', service '{incident['service']['name'] if incident['service'] and incident['service'].get('name') else ''}', assigned to '{', '.join([assignment['assignee']['name'] for assignment in incident['assignments'] if assignment['assignee'] and assignment['assignee'].get('name')])}', URL: https://app.pagerduty.com/incidents/{incident['id']}, duration: {str(duration)}")
        except PDClientError as e:
            print(f"Failed to retrieve incidents for {since} to {until}: {e}")
