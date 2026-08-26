import subprocess
import json
import urllib.request
import os

# Fetch openproject work packages for project 3
op_key = os.environ.get("OPENPROJECT_API_KEY", "")

def get_op_wps():
    req = urllib.request.Request("https://openproject.kesia.id/api/v3/projects/3/work_packages?pageSize=500")
    req.add_header("Authorization", "Basic " + urllib.parse.quote(f"apikey:{op_key}".encode("utf-8")).decode("utf-8") if False else "")
    # Or use curl via subprocess
    cmd = f'curl -s -u "apikey:{op_key}" "https://openproject.kesia.id/api/v3/projects/3/work_packages?pageSize=500"'
    res = subprocess.check_output(cmd, shell=True).decode('utf-8')
    data = json.loads(res)
    return data.get('_embedded', {}).get('elements', [])

wps = get_op_wps()
print(f"Total WPs fetched: {len(wps)}")

# Let's filter WPs that are NOT 'Released' (Status ID 20), Closed (12), Rejected (14), On hold (13)
unreleased_wps = []
for wp in wps:
    status_title = wp.get('_links', {}).get('status', {}).get('title', '')
    status_href = wp.get('_links', {}).get('status', {}).get('href', '')
    # status id 20 is Released
    if '/statuses/20' not in status_href and status_title not in ['Released', 'Closed', 'Rejected']:
        unreleased_wps.append({
            'id': wp['id'],
            'subject': wp['subject'],
            'status': status_title,
            'updatedAt': wp.get('updatedAt')
        })

print(f"Unreleased WPs count: {len(unreleased_wps)}")

# Now let's fetch commit messages from GitLab repos: kesia-fe, sirs-emr-microservice, sirs-masterdata-microservice, sirs-notification-microservice
gl_token = os.environ.get("GITLAB_API_KEY", "") or os.environ.get("GITLAB_TOKEN", "")

# We can query GitLab API via curl or python
def get_gl_commits(project_id_or_path):
    url = f"https://gitlab.com/api/v4/projects/{urllib.parse.quote(project_id_or_path, safe='')}/repository/commits?per_page=100"
    cmd = f'curl -s --header "PRIVATE-TOKEN: {gl_token}" "{url}"'
    res = subprocess.check_output(cmd, shell=True).decode('utf-8')
    try:
        return json.loads(res)
    except:
        return []

repos = [
    ("FE", "kesiaid/kesia-fe"),
    ("BE EMR", "kesiaid/sirs-emr-microservice"),
    ("BE Masterdata", "kesiaid/sirs-masterdata-microservice"),
    ("BE Notification", "kesiaid/sirs-notification-microservice")
]

commit_map = {} # ticket_id -> list of commits

for label, repo_path in repos:
    commits = get_gl_commits(repo_path)
    for c in commits:
        title = c.get('title', '')
        msg = c.get('message', '')
        # search for PP#xxxx or #xxxx or 4-digit numbers in commit title/msg
        matches = re.findall(r'(?:PP#|#)?(\d{4})', title + ' ' + msg)
        for m in matches:
            tid = int(m)
            if tid not in commit_map:
                commit_map[tid] = []
            commit_map[tid].append({
                'repo': label,
                'sha': c.get('short_id'),
                'title': title,
                'date': c.get('created_at')
            })

print(f"Tickets found in commits: {len(commit_map)}")

# Check unsynced: WP status in OP is NOT Released, but commit already merged/exists in repo!
unsynced = []
for wp in unreleased_wps:
    tid = wp['id']
    if tid in commit_map:
        unsynced.append({
            'wp': wp,
            'commits': commit_map[tid]
        })

print(f"\n--- HASIL SINKRONISASI ---")
print(f"Total tiket di board sprint (Status belum Released): {len(unreleased_wps)}")
print(f"Tiket yang BELUM STATUS RELEASED padahal SUDAH ADA COMMIT/MERGE di Git (Belum Sinkron): {len(unsynced)}\n")

for item in unsynced:
    wp = item['wp']
    print(f"Tiket #{wp['id']}: {wp['subject']}")
    print(f"  Status OpenProject : {wp['status']}")
    print(f"  Commit/Merge di Git:")
    for c in item['commits']:
        print(f"    - [{c['repo']}] {c['sha']}: {c['title']} ({c['date']})")
    print("-" * 50)

