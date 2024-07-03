import csv

def analyze_license_usage(csv_filename="subscriptions.csv"):
    """Analyzes license usage data in a CSV file and saves results to another CSV.

    Args:
        csv_filename (str): Name of the input CSV file (default: "subscriptions.csv")
    """

    license_data = {}

    with open(csv_filename, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            domain = row["customerDomain"]

            if domain not in license_data:
                license_data[domain] = {
                    "Licensed Seats": 0,
                    "Seats in Use": 0,
                    "Remaining Seats": 0
                }

            try:
                licensed_seats = int(row.get('licensedNumberOfSeats', 0))
                num_seats = int(row.get('numberOfSeats', 0))
            except ValueError:
                print(f"Warning: Invalid value in 'licensedNumberOfSeats' or 'numberOfSeats' for row: {row}")
                continue

            license_data[domain]["Licensed Seats"] += licensed_seats
            license_data[domain]["Seats in Use"] += num_seats

    # Calculate Remaining Seats *after* processing all rows
    for domain in license_data:
        license_data[domain]["Remaining Seats"] = max(0, license_data[domain]["Seats in Use"] - license_data[domain]["Licensed Seats"])

    # Save to CSV file
    with open("license_usage.csv", "w", newline="", encoding="utf-8") as outfile:
        fieldnames = ["Customer Domain", "Licensed Seats", "Seats in Use", "Remaining Seats"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for domain, data in license_data.items():
            writer.writerow({"Customer Domain": domain, **data}) 

    # Display results
    with open("license_usage.csv", "r", newline="", encoding="utf-8") as outfile:
        reader = csv.reader(outfile)
        for row in reader:
            print(", ".join(row))  # Output as comma-separated values
            
    # Save to CSV file
    with open("license_usage.csv", "w", newline="", encoding="utf-8") as outfile:
        fieldnames = ["Customer Domain", "Licensed Seats", "Seats in Use", "Remaining Seats"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for domain, data in license_data.items():
            writer.writerow({"Customer Domain": domain, **data})

    # Print the contents of license_usage.csv
    print("\nContents of license_usage.csv:")
    with open("license_usage.csv", "r", newline="", encoding="utf-8") as outfile:
        for line in outfile:
            print(line.strip())  # Strip extra whitespace for clean output


if __name__ == "__main__":
    analyze_license_usage() 
