"""
A one-off script I wrote to solve the problem of not recording group1 and group2
times for trains -- thcipriani, 2021-03-22
"""
import sqlite3
import trainstats

conn = sqlite3.connect(trainstats.DB_PATH)
# If the db didn't exist at the start of the function, do the setup
crs = conn.cursor()

versions = crs.execute(
    'select version from train where group1 = 0'
).fetchall()

count = 0
for version in versions:
    version = version[0]
    wikiversion_changes = trainstats.get_wikiversion_changes(version)

    groups_times = trainstats.group_times(version, wikiversion_changes)
    count += 1

    print(f'{version} | {groups_times}')

    crs.execute('''
        UPDATE train
        SET group1 = ?,
            group2 = ?
        WHERE version = ?''', (
            groups_times['commonswiki'].timestamp(),
            groups_times['enwiki'].timestamp(),
            version
        )
    )

    if count % 20 == 0:
        print('Commit!')
        conn.commit()

print('Commit!')
conn.commit()
