import argparse
import sys
import csv
import os

# ------------------------------------------------------------
# Expected Format for data.csv
#
# The CSV file should contain the following column headers:
#   oldhostname,newhostname,oldip,newip
#
# Each row should represent a mapping from an old hostname/IP
# to a new hostname/IP. Example:
#
# oldhostname,newhostname,oldip,newip
# server1,serverA,192.168.1.10,10.0.0.10
# server2,serverB,192.168.1.11,10.0.0.11
#
# You may omit IP columns if you're only replacing hostnames,
# or omit hostname columns if you're only replacing IPs.
# ------------------------------------------------------------

# Load hostname and IP replacement mappings from data.csv
def load_replacement_mappings(csv_filename):
    """
    Load hostname and IP replacement mappings from a CSV file.

    The CSV is expected to contain columns named:
    - "oldhostname" and "newhostname" for hostname replacements
    - "oldip" and "newip" for IP replacements

    Each row may provide one or both types of mapping. Only rows where both
    the "old" and "new" values are present for a mapping are added to the
    corresponding dictionary.

    Args:
        csv_filename (str): Path to the CSV file to read.

    Returns:
        tuple[dict, dict]: A pair (hostname_map, ip_map) where:
            - hostname_map maps oldhostname -> newhostname
            - ip_map maps oldip -> newip
          If no valid mappings are found for a category, the corresponding
          dictionary will be empty.

    Side effects / Errors:
        - If the file does not exist, the function prints an error and
          terminates the process via sys.exit(1).
        - If any other exception occurs while reading/parsing the CSV, the
          function prints an error and terminates via sys.exit(1).

    Notes:
        - The function uses csv.DictReader and returns values exactly as read;
          it does not perform additional normalization (e.g., stripping
          whitespace or validating IP/hostname formats).
        - Rows missing either the old or new value for a particular mapping
          are ignored for that mapping but do not prevent other mappings on
          the same row from being processed.

    Example CSV content:
        oldhostname,newhostname,oldip,newip
        server1.example.com,server1.prod.example.com,192.0.2.10,203.0.113.10

    Example return:
        ({"server1.example.com": "server1.prod.example.com"},
         {"192.0.2.10": "203.0.113.10"})
    """
    hostname_map = {}  # Dictionary to store oldhostname:newhostname
    ip_map = {}        # Dictionary to store oldip:newip

    try:
        # Open and read the CSV file
        with open(csv_filename, mode='r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Extract values from each row
                old_host = row.get('oldhostname')
                new_host = row.get('newhostname')
                old_ip = row.get('oldip')
                new_ip = row.get('newip')

                # Add valid mappings to dictionaries
                if old_host and new_host:
                    hostname_map[old_host] = new_host
                if old_ip and new_ip:
                    ip_map[old_ip] = new_ip
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

    return hostname_map, ip_map

# Replace values in the input file and save to sanitized_<filename>
def replace_values_in_file(input_filename, hostname_map, ip_map):
    """
    Replace values in a file and write a sanitized copy.

    Parameters
    ----------
    input_filename : str
        Path to the input file to read and sanitize.
    hostname_map : Mapping[str, str]
        Mapping of old hostnames to new hostnames. Each key found in the file
        will be replaced with its corresponding value.
    ip_map : Mapping[str, str]
        Mapping of old IP addresses to new IP addresses. Each key found in the
        file will be replaced with its corresponding value.

    Behavior
    --------
    - Reads the entire contents of `input_filename`.
    - Applies plain substring replacements for hostnames (iterating through
      `hostname_map`) and then for IP addresses (iterating through `ip_map`).
    - Replaces all literal occurrences of 'lab.local' with 'sanitized.domain'.
    - Writes the modified content to a new file named
      "sanitized_<basename(input_filename)>" in the current working directory.
    - Prints a message on success or an error message if an exception occurs.

    Returns
    -------
    None

    Side effects
    ------------
    - Creates or overwrites the sanitized output file in the current working directory.
    - Prints status or error messages to standard output.

    Exceptions
    ----------
    - FileNotFoundError is caught and results in a printed error message.
    - Any other Exception is caught and printed; exceptions are not re-raised.

    Notes
    -----
    - Replacements are simple string substitutions and are order-dependent:
      hostname replacements happen before IP replacements.
    - If more precise matching is required (e.g., word boundaries, avoiding
      partial matches), consider using regular expressions.
    - The implementation expects `os` to be imported in the module for
      constructing the sanitized filename; ensure `import os` is present.
    """
    try:
        # Read the contents of the input file
        with open(input_filename, 'r') as file:
            content = file.read()

        # Replace all old hostnames with new hostnames
        for old, new in hostname_map.items():
            content = content.replace(old, new)

        # Replace all old IPs with new IPs
        for old, new in ip_map.items():
            content = content.replace(old, new)

        # Replace all instances of 'lab.local' with 'sanitized.domain'
        content = content.replace('lab.local', 'sanitized.domain')

        # Generate sanitized filename
        sanitized_filename = f"sanitized_{os.path.basename(input_filename)}"

        # Write the updated content to the new file
        with open(sanitized_filename, 'w') as file:
            file.write(content)

        print(f"Sanitized file saved as '{sanitized_filename}'.")
    except FileNotFoundError:
        print(f"Error: File '{input_filename}' not found.")
    except Exception as e:
        print(f"An error occurred while processing the file: {e}")

# Main function to handle command-line arguments and orchestrate the workflow
def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Sanitize hostnames, IPs, and domains in a file using data.csv.')
    parser.add_argument('-f', '--file', type=str, help='Path to the input file')
    args = parser.parse_args()

    # Check if the user provided a file
    if not args.file:
        print("Error: No file specified.\nPlease run the script using the -f flag followed by the filename.")
        print("Example: python script.py -f filename.txt")
        sys.exit(1)

    # Check if data.csv exists in the current directory
    if not os.path.exists('data.csv'):
        print("Error: 'data.csv' not found in the current directory.")
        sys.exit(1)

    # Load mappings and sanitize the input file
    hostname_map, ip_map = load_replacement_mappings('data.csv')
    replace_values_in_file(args.file, hostname_map, ip_map)

# Entry point of the script
if __name__ == '__main__':
    main()
    # Print a final completion message showing the sanitized filename (if a file arg was provided)
    def _print_completion_message_from_argv():
        argv = sys.argv[1:]
        filename = None
        if '-f' in argv:
            i = argv.index('-f')
            if i + 1 < len(argv):
                filename = argv[i + 1]
        elif '--file' in argv:
            i = argv.index('--file')
            if i + 1 < len(argv):
                filename = argv[i + 1]

        if filename:
            sanitized = f"sanitized_{os.path.basename(filename)}"
            print(f"Script completed. Sanitized file: '{sanitized}'.")

    _print_completion_message_from_argv()