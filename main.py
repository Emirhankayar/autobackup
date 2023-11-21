from flask import Flask, jsonify
from supabase_py import create_client, Client
from github import Github, InputGitTreeElement
import csv
from tqdm import tqdm
from datetime import datetime
import os
from dotenv import load_dotenv
import io

load_dotenv()

app = Flask(__name__)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
github_token = os.getenv("GITHUB_TOKEN")
github_repo = os.getenv("GITHUB_REPO")
flask_app_port = int(os.getenv("FLASK_APP_PORT", 10000))

# Create a client
supabase: Client = create_client(url, key)

# GitHub credentials
g = Github(github_token)
repo = g.get_user().get_repo(github_repo)

@app.route('/backup', methods=['GET'])
def backup():
    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y-%b-%d_%H-%M-%S")

    # List of table names
    tables = ["email", "user_added_posts", "user_bookmarked_posts", "user_highlighted_posts", "users", "tools"]

    # Loop over the table names
    for table in tqdm(tables, desc="Processing tables"):
        try:
            # Initialize an empty list to store the rows from the table
            rows = []

            # Initialize the start and end of the range
            start = 0
            end = 999

            # Fetch the rows in chunks
            while True:
                # Get a chunk of rows from the table
                response = supabase.table(table).select().range(start, end).execute()

                # Check if the chunk has rows
                if response['data']:
                    # Append the rows to the list
                    rows.extend(response['data'])

                    # Increase the start and end of the range
                    start += 1000
                    end += 1000
                else:
                    # If the chunk doesn't have rows, break the loop
                    break

            # Write the rows to a CSV file in memory
            csv_file = io.StringIO()
            if rows:  # Check if there are any rows
                writer = csv.DictWriter(csv_file, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            # Get the CSV content
            content = csv_file.getvalue()

            # Create a git tree element
            element = InputGitTreeElement(path=f"{timestamp}/{table}.csv", mode='100644', type='blob', content=content)

            # Get the current commit
            master_ref = repo.get_git_ref('heads/main')
            master_sha = master_ref.object.sha
            base_tree = repo.get_git_tree(master_sha)

            # Create a new tree and a new commit
            tree = repo.create_git_tree([element], base_tree)
            parent = repo.get_git_commit(master_sha)
            commit = repo.create_git_commit(f"Update {table}.csv", tree, [parent])
            master_ref.edit(commit.sha)

        except Exception as e:
            print(f"Error processing table {table}: {str(e)}")

    return jsonify({"message": "Backup completed successfully"}), 200


if __name__ == "__main__":
    app.run(port=flask_app_port, debug=True)