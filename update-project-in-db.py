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
    'select link from patch where project not like "mediawiki%" and project != "VisualEditor/VisualEditor"'
).fetchall()

count = 0
for patch in patches:
    link = patch[0]
    patchid = trainstats.extract_changeid(link)
    patch_data = gerrit.search(patchid)
    patches_len = len(patch_data)
    found_patch = None
    for p in patch_data:
        if not p.get('submitted'):
            continue
        print(p['project'])
        if p['project'].startswith('mediawiki') or p['project'] == 'VisualEditor/VisualEditor':
            print(p)
            found_patch = p
    project = found_patch['project']
    count += 1

    print(f'{link} | {patchid} | {project} | match: {patches_len}')

    crs.execute('''
        UPDATE patch
        SET project = ?
        WHERE link = ?''', (
            project,
            link
        )
    )

    if count % 20 == 0:
        print('Commit!')
        conn.commit()

print('Commit!')
conn.commit()
