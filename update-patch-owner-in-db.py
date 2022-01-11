"""
A one-off script I wrote to solve the problem of not having a project
attached to patches. I'm committing it for posterity, but should be
removed in future once I've determined that it has no further use.
-- thcipriani, 2021-10-07
"""
import sqlite3
import trainstats
import gerrit

conn = sqlite3.connect(trainstats.DB_PATH)
# If the db didn't exist at the start of the function, do the setup
crs = conn.cursor()

patches = crs.execute(
    'select link from patch where owner is null'
).fetchall()
# patches = crs.execute(
#     '''select link, cast(strftime('%m',datetime(start_time, 'unixepoch')) as INT) as Month, cast(strftime('%Y',datetime(start_time, 'unixepoch')) as INT) as Year from train join patch p on p.train_id = train.id where Year = 2021 and Month >= 9 and Month <= 11 and owner is null order by Month desc'''
# ).fetchall()

count = 0
for patch in patches:
    link = patch[0]
    patchid = trainstats.extract_changeid(link)
    patch_data = gerrit.search(patchid)
    patches_len = len(patch_data)
    patch_data = [p for p in patch_data if p['submitted']][0]
    owner = patch_data['owner']
    count += 1

    print(f'{link} | {patchid} | {owner} | match: {patches_len}')

    crs.execute('''
        UPDATE patch
        SET owner = ?
        WHERE link = ?''', (
            owner,
            link
        )
    )

    if count % 20 == 0:
        print('Commit!')
        conn.commit()

print('Commit!')
conn.commit()
