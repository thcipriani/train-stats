# Train Stats

```
 ----------------------------------------------------------------------------------------
/                                                                                        \
| /$$$$$$$$                 /$$            /$$$$$$   /$$                 /$$             |
||__  $$__/                |__/           /$$__  $$ | $$                | $$             |
|   | $$  /$$$$$$  /$$$$$$  /$$ /$$$$$$$ | $$  \__//$$$$$$    /$$$$$$  /$$$$$$   /$$$$$$$|
|   | $$ /$$__  $$|____  $$| $$| $$__  $$|  $$$$$$|_  $$_/   |____  $$|_  $$_/  /$$_____/|
|   | $$| $$  \__/ /$$$$$$$| $$| $$  \ $$ \____  $$ | $$      /$$$$$$$  | $$   |  $$$$$$ |
|   | $$| $$      /$$__  $$| $$| $$  | $$ /$$  \ $$ | $$ /$$ /$$__  $$  | $$ /$$\____  $$|
|   | $$| $$     |  $$$$$$$| $$| $$  | $$|  $$$$$$/ |  $$$$/|  $$$$$$$  |  $$$$//$$$$$$$/|
|   |__/|__/      \_______/|__/|__/  |__/ \______/   \___/   \_______/   \___/ |_______/ |
|                                                                                        |
|                                                                                        |
|                                                                                        |
|                                      🚂 ¯\_(ツ)_/¯?                                     |
\                                                                                        /
 ----------------------------------------------------------------------------------------
    \     
     \     
      \      
           ___ ____
         ⎛   ⎛ ,----
          \  //==--'
     _//|,.·//==--'    ____________________________
    _OO≣=-  ︶ ᴹw ⎞_§ ______  ___\ ___\ ,\__ \/ __ \
   (∞)_, )  (     |  ______/__  \/ /__ / /_/ / /_/ /
     ¨--¨|| |- (  / ______\____/ \___/ \__^_/  .__/
         ««_/  «_/ jgs/bd808                /_/
```

In which I look at data from the past several hundred trains and pretend that I know how to do exploratory data analysis.


```python
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns

from sqlalchemy import create_engine

TRAINS = [
    '1.39.0-wmf.1',
    '1.39.0-wmf.2',
    '1.39.0-wmf.3',
]

engine = create_engine('sqlite:///data/train.db')
df = pd.read_sql('''
SELECT
    version,
    rollbacks,
    rollbacks_time,
    group2_delay_days,
    (group0_delay_days +
     group1_delay_days +
     group2_delay_days) as total_delay,
    total_time as train_total_time,
    (select count(*) from blocker b where b.train_id = t.id) as blockers,
    (select count(*) from blocker b where b.train_id = t.id and resolved = 1) as resolved_blockers,
    patches,
    (select max(time_in_review) from patch p where p.train_id = t.id) as max_time_in_review,
    (select max(comments) from patch where patch.train_id = t.id) as max_comments_per_patch,
    (select max(start_time - created) from patch p where p.train_id = t.id) as max_cycle_time
FROM train t
''', engine)

# Makes your data 538% better...I think
plt.style.use('fivethirtyeight')
df.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>version</th>
      <th>rollbacks</th>
      <th>rollbacks_time</th>
      <th>group2_delay_days</th>
      <th>total_delay</th>
      <th>train_total_time</th>
      <th>blockers</th>
      <th>resolved_blockers</th>
      <th>patches</th>
      <th>max_time_in_review</th>
      <th>max_comments_per_patch</th>
      <th>max_cycle_time</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1.37.0-wmf.1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>178349</td>
      <td>5</td>
      <td>3</td>
      <td>450</td>
      <td>36809044.0</td>
      <td>27.0</td>
      <td>36952873.0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1.37.0-wmf.3</td>
      <td>3</td>
      <td>94493</td>
      <td>0</td>
      <td>1</td>
      <td>219880</td>
      <td>7</td>
      <td>6</td>
      <td>366</td>
      <td>56122286.0</td>
      <td>30.0</td>
      <td>56562620.0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1.37.0-wmf.4</td>
      <td>1</td>
      <td>66812</td>
      <td>1</td>
      <td>3</td>
      <td>263742</td>
      <td>9</td>
      <td>4</td>
      <td>422</td>
      <td>38820872.0</td>
      <td>29.0</td>
      <td>38982601.0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1.36.0-wmf.1</td>
      <td>0</td>
      <td>0</td>
      <td>4</td>
      <td>4</td>
      <td>519622</td>
      <td>1</td>
      <td>1</td>
      <td>566</td>
      <td>47181045.0</td>
      <td>31.0</td>
      <td>47755190.0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1.36.0-wmf.2</td>
      <td>4</td>
      <td>389769</td>
      <td>4</td>
      <td>5</td>
      <td>554704</td>
      <td>7</td>
      <td>1</td>
      <td>273</td>
      <td>110996452.0</td>
      <td>33.0</td>
      <td>111569626.0</td>
    </tr>
  </tbody>
</table>
</div>




```python
fig, ax = plt.subplots(figsize=(10,10))         # Sample figsize in inches
sns.heatmap(df.corr(), annot=True, cmap="YlGnBu", linewidths=0.3, annot_kws={"size": 8}, ax=ax)
plt.xticks(rotation=90)
plt.yticks(rotation=0)
plt.show()
```


    
![png](README_files/README_2_0.png)
    



```python
df.set_index('version')['blockers'].hist(figsize=(12, 10))
plt.xlabel("Blockers", labelpad=15)
plt.title("Blockers per Train", y=1.02, fontsize=22)
```




    Text(0.5, 1.02, 'Blockers per Train')




    
![png](README_files/README_3_1.png)
    



```python
df[df['blockers'] > 10].sort_values(by='blockers', ascending=False)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>version</th>
      <th>rollbacks</th>
      <th>rollbacks_time</th>
      <th>group2_delay_days</th>
      <th>total_delay</th>
      <th>train_total_time</th>
      <th>blockers</th>
      <th>resolved_blockers</th>
      <th>patches</th>
      <th>max_time_in_review</th>
      <th>max_comments_per_patch</th>
      <th>max_cycle_time</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>82</th>
      <td>1.34.0-wmf.20</td>
      <td>1</td>
      <td>16897</td>
      <td>5</td>
      <td>5</td>
      <td>600096</td>
      <td>20</td>
      <td>11</td>
      <td>413</td>
      <td>60583935.0</td>
      <td>37.0</td>
      <td>60715205.0</td>
    </tr>
    <tr>
      <th>242</th>
      <td>1.38.0-wmf.19</td>
      <td>1</td>
      <td>70250</td>
      <td>0</td>
      <td>1</td>
      <td>176801</td>
      <td>18</td>
      <td>10</td>
      <td>319</td>
      <td>85391889.0</td>
      <td>24.0</td>
      <td>85778365.0</td>
    </tr>
    <tr>
      <th>103</th>
      <td>1.33.0-wmf.22</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>63844</td>
      <td>17</td>
      <td>11</td>
      <td>391</td>
      <td>107411197.0</td>
      <td>45.0</td>
      <td>107659715.0</td>
    </tr>
    <tr>
      <th>77</th>
      <td>1.34.0-wmf.14</td>
      <td>2</td>
      <td>412678</td>
      <td>4</td>
      <td>5</td>
      <td>524983</td>
      <td>16</td>
      <td>7</td>
      <td>646</td>
      <td>73502579.0</td>
      <td>34.0</td>
      <td>73539481.0</td>
    </tr>
    <tr>
      <th>136</th>
      <td>1.31.0-wmf.20</td>
      <td>2</td>
      <td>134534</td>
      <td>1</td>
      <td>5</td>
      <td>255075</td>
      <td>14</td>
      <td>12</td>
      <td>822</td>
      <td>66099647.0</td>
      <td>75.0</td>
      <td>67210868.0</td>
    </tr>
    <tr>
      <th>210</th>
      <td>1.30.0-wmf.2</td>
      <td>2</td>
      <td>595079</td>
      <td>0</td>
      <td>0</td>
      <td>782668</td>
      <td>14</td>
      <td>12</td>
      <td>462</td>
      <td>67958577.0</td>
      <td>56.0</td>
      <td>68943029.0</td>
    </tr>
    <tr>
      <th>241</th>
      <td>1.38.0-wmf.18</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>171956</td>
      <td>13</td>
      <td>7</td>
      <td>287</td>
      <td>186407187.0</td>
      <td>43.0</td>
      <td>186862129.0</td>
    </tr>
    <tr>
      <th>124</th>
      <td>1.32.0-wmf.22</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>173055</td>
      <td>12</td>
      <td>7</td>
      <td>824</td>
      <td>64869761.0</td>
      <td>44.0</td>
      <td>65392036.0</td>
    </tr>
    <tr>
      <th>57</th>
      <td>1.35.0-wmf.31</td>
      <td>3</td>
      <td>365118</td>
      <td>4</td>
      <td>15</td>
      <td>516489</td>
      <td>11</td>
      <td>7</td>
      <td>427</td>
      <td>72215548.0</td>
      <td>70.0</td>
      <td>72206585.0</td>
    </tr>
    <tr>
      <th>76</th>
      <td>1.34.0-wmf.13</td>
      <td>2</td>
      <td>14912</td>
      <td>0</td>
      <td>1</td>
      <td>183853</td>
      <td>11</td>
      <td>8</td>
      <td>471</td>
      <td>53208155.0</td>
      <td>23.0</td>
      <td>53820019.0</td>
    </tr>
    <tr>
      <th>187</th>
      <td>1.28.0-wmf.21</td>
      <td>1</td>
      <td>88476</td>
      <td>0</td>
      <td>1</td>
      <td>176082</td>
      <td>11</td>
      <td>8</td>
      <td>514</td>
      <td>60386455.0</td>
      <td>93.0</td>
      <td>61360331.0</td>
    </tr>
  </tbody>
</table>
</div>




```python
block_df = pd.read_sql('''
SELECT
    version,
    group_blocked
FROM train t
JOIN blocker b ON t.id = b.train_id
''', engine)
block_df.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>version</th>
      <th>group_blocked</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1.37.0-wmf.7</td>
      <td>-1</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1.37.0-wmf.7</td>
      <td>-1</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1.37.0-wmf.12</td>
      <td>2</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1.37.0-wmf.12</td>
      <td>1</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1.37.0-wmf.12</td>
      <td>1</td>
    </tr>
  </tbody>
</table>
</div>




```python
block_df.group_blocked.unique()
```




    array([-1,  2,  1,  0])




```python
group_name_map = {
    -1: "Earlier",
    0: "Group0",
    1: "Group1",
    2: "Group2",
}
block_df['blocker_added'] = block_df.group_blocked.map(group_name_map)
block_df.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>version</th>
      <th>group_blocked</th>
      <th>blocker_added</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1.37.0-wmf.7</td>
      <td>-1</td>
      <td>Earlier</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1.37.0-wmf.7</td>
      <td>-1</td>
      <td>Earlier</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1.37.0-wmf.12</td>
      <td>2</td>
      <td>Group2</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1.37.0-wmf.12</td>
      <td>1</td>
      <td>Group1</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1.37.0-wmf.12</td>
      <td>1</td>
      <td>Group1</td>
    </tr>
  </tbody>
</table>
</div>




```python
block_df.group_blocked.value_counts()
```




    -1    403
     1    340
     0    282
     2    126
    Name: group_blocked, dtype: int64




```python
block_df.version
```




    0        1.37.0-wmf.7
    1        1.37.0-wmf.7
    2       1.37.0-wmf.12
    3       1.37.0-wmf.12
    4       1.37.0-wmf.12
                ...      
    1146     1.39.0-wmf.3
    1147     1.39.0-wmf.3
    1148     1.39.0-wmf.3
    1149     1.39.0-wmf.3
    1150     1.39.0-wmf.3
    Name: version, Length: 1151, dtype: object




```python
block_df.set_index('version')
block_df.sort_values('group_blocked', inplace=True)


fig = plt.figure(figsize=(16,6))
plt.grid(color='white', lw=0.5, axis='x')
n, bins, patches = plt.hist(block_df.blocker_added, bins=4, rwidth=0.95)

xticks = [(bins[idx+1] + value)/2 for idx, value in enumerate(bins[:-1])]
xticks_labels = [ "{:.2f}\nto\n{:.2f}".format(value, bins[idx+1]) for idx, value in enumerate(bins[:-1])]
plt.xticks(xticks, labels=["Before group0", "Group0", "Group1", "Group2"])

# remove y ticks
plt.yticks([])

# plot values on top of bars
for idx, value in enumerate(n):
    if value > 0:
        plt.text(xticks[idx], value+5, int(value), ha='center')

plt.title('Train Blockers by Group Where They Were Discovered', loc='left', pad=30)
plt.show()

```


    
![png](README_files/README_10_0.png)
    



```python
patches = pd.read_sql('''
SELECT
    link,
    version,
    submitted,
    insertions as ins,
    (deletions*-1) as del
FROM patch p JOIN train t ON t.id = p.train_id
''', engine)
patches.describe()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>submitted</th>
      <th>ins</th>
      <th>del</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>count</th>
      <td>8.601500e+04</td>
      <td>8.601500e+04</td>
      <td>8.601500e+04</td>
    </tr>
    <tr>
      <th>mean</th>
      <td>1.557361e+09</td>
      <td>3.588985e+02</td>
      <td>-2.847517e+02</td>
    </tr>
    <tr>
      <th>std</th>
      <td>5.157033e+07</td>
      <td>5.916831e+04</td>
      <td>5.672674e+04</td>
    </tr>
    <tr>
      <th>min</th>
      <td>1.431572e+09</td>
      <td>0.000000e+00</td>
      <td>-1.661412e+07</td>
    </tr>
    <tr>
      <th>25%</th>
      <td>1.518932e+09</td>
      <td>2.000000e+00</td>
      <td>-1.600000e+01</td>
    </tr>
    <tr>
      <th>50%</th>
      <td>1.561131e+09</td>
      <td>6.000000e+00</td>
      <td>-4.000000e+00</td>
    </tr>
    <tr>
      <th>75%</th>
      <td>1.596228e+09</td>
      <td>3.100000e+01</td>
      <td>-1.000000e+00</td>
    </tr>
    <tr>
      <th>max</th>
      <td>1.647938e+09</td>
      <td>1.728860e+07</td>
      <td>0.000000e+00</td>
    </tr>
  </tbody>
</table>
</div>




```python
patches['loc'] = patches['ins'] + patches['del']
patches.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>link</th>
      <th>version</th>
      <th>submitted</th>
      <th>ins</th>
      <th>del</th>
      <th>loc</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>https://gerrit.wikimedia.org/r/#/q/ccbfcf28,n,z</td>
      <td>1.37.0-wmf.1</td>
      <td>1618945759</td>
      <td>5</td>
      <td>-1</td>
      <td>4</td>
    </tr>
    <tr>
      <th>1</th>
      <td>https://gerrit.wikimedia.org/r/#/q/3302274f,n,z</td>
      <td>1.37.0-wmf.1</td>
      <td>1618878371</td>
      <td>1156</td>
      <td>-660</td>
      <td>496</td>
    </tr>
    <tr>
      <th>2</th>
      <td>https://gerrit.wikimedia.org/r/#/q/8b5471b5,n,z</td>
      <td>1.37.0-wmf.1</td>
      <td>1618343309</td>
      <td>976</td>
      <td>-3</td>
      <td>973</td>
    </tr>
    <tr>
      <th>3</th>
      <td>https://gerrit.wikimedia.org/r/#/q/a6abbb67,n,z</td>
      <td>1.37.0-wmf.1</td>
      <td>1618341075</td>
      <td>8</td>
      <td>-29</td>
      <td>-21</td>
    </tr>
    <tr>
      <th>4</th>
      <td>https://gerrit.wikimedia.org/r/#/q/af916aad,n,z</td>
      <td>1.37.0-wmf.1</td>
      <td>1618300868</td>
      <td>7</td>
      <td>-5</td>
      <td>2</td>
    </tr>
  </tbody>
</table>
</div>




```python
patches['submitted'] = pd.to_datetime(patches['submitted'], unit='s')
patches.set_index('submitted', inplace=True)
```


```python
out = patches.groupby(pd.Grouper(freq='M')).apply(lambda x: x)
out = out[out['link'] != 'https://gerrit.wikimedia.org/r/#/q/9a08dbab,n,z'] # The one patch that inserts 17.2M lines of code
out['ok'] = out['loc'].cumsum()
```

## Cycle time/Lead time

**Cycle time** is the time from when a patch enters code review to the time that it's in production. **Lead time** is the time it takes from commit to production.


```python
# GOAL
#         train     lead_time    cycle_time   Id
# 0    1.37.0-wmf.6    200   2000   u1234
# 1    1.37.0-wmf.6    123   2800   u1235

cycle = pd.read_sql('''
SELECT
    substr(version, 8) as version,
    datetime(start_time, 'unixepoch'),
    (start_time - created) as cycle_time,
    (start_time - submitted) as lead_time,
    datetime(created, 'unixepoch'),
    datetime(submitted, 'unixepoch'),
    link
FROM patch p JOIN train t ON t.id = p.train_id
WHERE (lead_time > 0 AND cycle_time > 0)
    AND (
        version = "%(version_one)s" OR
        version = "%(version_two)s" OR
        version = "%(version_three)s"
    )
''' % {
    'version_one': TRAINS[0],
    'version_two': TRAINS[1],
    'version_three': TRAINS[2],
}, engine)
cycle.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>version</th>
      <th>datetime(start_time, 'unixepoch')</th>
      <th>cycle_time</th>
      <th>lead_time</th>
      <th>datetime(created, 'unixepoch')</th>
      <th>datetime(submitted, 'unixepoch')</th>
      <th>link</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>wmf.1</td>
      <td>2022-03-21 10:06:50</td>
      <td>264894</td>
      <td>42619</td>
      <td>2022-03-18 08:31:56</td>
      <td>2022-03-20 22:16:31</td>
      <td>https://gerrit.wikimedia.org/r/q/771759</td>
    </tr>
    <tr>
      <th>1</th>
      <td>wmf.1</td>
      <td>2022-03-21 10:06:50</td>
      <td>264894</td>
      <td>43647</td>
      <td>2022-03-18 08:31:56</td>
      <td>2022-03-20 21:59:23</td>
      <td>https://gerrit.wikimedia.org/r/q/771758</td>
    </tr>
    <tr>
      <th>2</th>
      <td>wmf.1</td>
      <td>2022-03-21 10:06:50</td>
      <td>3227088</td>
      <td>15500</td>
      <td>2022-02-12 01:42:02</td>
      <td>2022-03-21 05:48:30</td>
      <td>https://gerrit.wikimedia.org/r/q/761969</td>
    </tr>
    <tr>
      <th>3</th>
      <td>wmf.1</td>
      <td>2022-03-21 10:06:50</td>
      <td>537645</td>
      <td>108855</td>
      <td>2022-03-15 04:46:05</td>
      <td>2022-03-20 03:52:35</td>
      <td>https://gerrit.wikimedia.org/r/q/770619</td>
    </tr>
    <tr>
      <th>4</th>
      <td>wmf.1</td>
      <td>2022-03-21 10:06:50</td>
      <td>432769</td>
      <td>110474</td>
      <td>2022-03-16 09:54:01</td>
      <td>2022-03-20 03:25:36</td>
      <td>https://gerrit.wikimedia.org/r/q/771093</td>
    </tr>
  </tbody>
</table>
</div>




```python
cycle.sort_values(by='lead_time', ascending=False).head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>version</th>
      <th>datetime(start_time, 'unixepoch')</th>
      <th>cycle_time</th>
      <th>lead_time</th>
      <th>datetime(created, 'unixepoch')</th>
      <th>datetime(submitted, 'unixepoch')</th>
      <th>link</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>65</th>
      <td>wmf.1</td>
      <td>2022-03-21 10:06:50</td>
      <td>525695</td>
      <td>524389</td>
      <td>2022-03-15 08:05:15</td>
      <td>2022-03-15 08:27:01</td>
      <td>https://gerrit.wikimedia.org/r/q/770658</td>
    </tr>
    <tr>
      <th>64</th>
      <td>wmf.1</td>
      <td>2022-03-21 10:06:50</td>
      <td>524292</td>
      <td>523318</td>
      <td>2022-03-15 08:28:38</td>
      <td>2022-03-15 08:44:52</td>
      <td>https://gerrit.wikimedia.org/r/q/770060</td>
    </tr>
    <tr>
      <th>63</th>
      <td>wmf.1</td>
      <td>2022-03-21 10:06:50</td>
      <td>27030481</td>
      <td>521572</td>
      <td>2021-05-12 13:38:49</td>
      <td>2022-03-15 09:13:58</td>
      <td>https://gerrit.wikimedia.org/r/q/689538</td>
    </tr>
    <tr>
      <th>78</th>
      <td>wmf.1</td>
      <td>2022-03-21 10:06:50</td>
      <td>793742</td>
      <td>517590</td>
      <td>2022-03-12 05:37:48</td>
      <td>2022-03-15 10:20:20</td>
      <td>https://gerrit.wikimedia.org/r/q/770068</td>
    </tr>
    <tr>
      <th>174</th>
      <td>wmf.1</td>
      <td>2022-03-21 10:06:50</td>
      <td>696445</td>
      <td>517086</td>
      <td>2022-03-13 08:39:25</td>
      <td>2022-03-15 10:28:44</td>
      <td>https://gerrit.wikimedia.org/r/q/770119</td>
    </tr>
  </tbody>
</table>
</div>



### Lead time

The time from commit to deploy (in seconds)


```python
cycle['lead_time_days'] = cycle['lead_time'] / (60*60*24)
cycle['cycle_time_days'] = cycle['cycle_time'] / (60*60*24)
cycle.sort_values(by='lead_time_days').head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>version</th>
      <th>datetime(start_time, 'unixepoch')</th>
      <th>cycle_time</th>
      <th>lead_time</th>
      <th>datetime(created, 'unixepoch')</th>
      <th>datetime(submitted, 'unixepoch')</th>
      <th>link</th>
      <th>lead_time_days</th>
      <th>cycle_time_days</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>238</th>
      <td>wmf.3</td>
      <td>2022-03-22 08:51:32</td>
      <td>2643</td>
      <td>1550</td>
      <td>2022-03-22 08:07:29</td>
      <td>2022-03-22 08:25:42</td>
      <td>https://gerrit.wikimedia.org/r/q/772545</td>
      <td>0.017940</td>
      <td>0.030590</td>
    </tr>
    <tr>
      <th>235</th>
      <td>wmf.2</td>
      <td>2022-03-21 18:21:39</td>
      <td>12396</td>
      <td>1886</td>
      <td>2022-03-21 14:55:03</td>
      <td>2022-03-21 17:50:13</td>
      <td>https://gerrit.wikimedia.org/r/q/772328</td>
      <td>0.021829</td>
      <td>0.143472</td>
    </tr>
    <tr>
      <th>225</th>
      <td>wmf.2</td>
      <td>2022-03-21 18:21:39</td>
      <td>15691926</td>
      <td>3395</td>
      <td>2021-09-21 03:29:33</td>
      <td>2022-03-21 17:25:04</td>
      <td>https://gerrit.wikimedia.org/r/q/722430</td>
      <td>0.039294</td>
      <td>181.619514</td>
    </tr>
    <tr>
      <th>224</th>
      <td>wmf.2</td>
      <td>2022-03-21 18:21:39</td>
      <td>93630481</td>
      <td>4846</td>
      <td>2019-04-03 01:53:38</td>
      <td>2022-03-21 17:00:53</td>
      <td>https://gerrit.wikimedia.org/r/q/500819</td>
      <td>0.056088</td>
      <td>1083.686123</td>
    </tr>
    <tr>
      <th>227</th>
      <td>wmf.2</td>
      <td>2022-03-21 18:21:39</td>
      <td>15895</td>
      <td>4849</td>
      <td>2022-03-21 13:56:44</td>
      <td>2022-03-21 17:00:50</td>
      <td>https://gerrit.wikimedia.org/r/q/772323</td>
      <td>0.056123</td>
      <td>0.183970</td>
    </tr>
  </tbody>
</table>
</div>




```python
from matplotlib import ticker as mticker
import numpy as np

# Adapted from <https://stackoverflow.com/a/60132262>
fig, ax = plt.subplots(1, 3, sharey=True, figsize=(20,10))
sns.violinplot(data=cycle,x='version', y='lead_time_days', ax=ax[0])
sns.swarmplot(data=cycle,x='version', y='lead_time_days', ax=ax[1])
sns.stripplot(data=cycle,x='version', y='lead_time_days', ax=ax[2])
ax[0].yaxis.set_major_formatter(mticker.StrMethodFormatter("{x}"))
plt.show()
```


    
![png](README_files/README_20_0.png)
    



```python
fig, ax = plt.subplots(1, 1, sharey=True, figsize=(20,10))
ax.set_yscale('log')
sns.stripplot(data=cycle,x='version', y='lead_time_days', ax=ax)
ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x}"))
plt.show()
```


    
![png](README_files/README_21_0.png)
    


### Cycle time

The time from patchset submission for code review to deploy


```python
from matplotlib import ticker as mticker
import numpy as np

# Adapted from <https://stackoverflow.com/a/60132262>
fig, ax = plt.subplots(1, 3, sharey=True, figsize=(20,10))
sns.violinplot(data=cycle,x='version', y='cycle_time_days', ax=ax[0])
sns.swarmplot(data=cycle,x='version', y='cycle_time_days', ax=ax[1])
sns.stripplot(data=cycle,x='version', y='cycle_time_days', ax=ax[2])
ax[0].yaxis.set_major_formatter(mticker.StrMethodFormatter("{x}"))
plt.show()
```

    /usr/lib/python3/dist-packages/seaborn/categorical.py:1296: UserWarning: 75.9% of the points cannot be placed; you may want to decrease the size of the markers or use stripplot.
      warnings.warn(msg, UserWarning)
    /usr/lib/python3/dist-packages/seaborn/categorical.py:1296: UserWarning: 45.2% of the points cannot be placed; you may want to decrease the size of the markers or use stripplot.
      warnings.warn(msg, UserWarning)



    
![png](README_files/README_23_1.png)
    


# Cycle time log scale

It's hard to see the majority of our patch's cycletime with the outliers. Here's the log-scale version.


```python
fig, ax = plt.subplots(1, 1, sharey=True, figsize=(20,10))
ax.set_yscale('log')
sns.stripplot(data=cycle,x='version', y='cycle_time_days', ax=ax)
ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x}"))
plt.show()
```


    
![png](README_files/README_25_0.png)
    


## Train bugfixes

> **Backport**
> * v. To retroactively supply a fix, or a new feature, to a previous version of a software product at the same time (or after) supplying it to the current version.
> * n. A commit that is backported

Each train has many backports. Each backport may be supplied to many trains. Backports add features, change feature flags, and fix bugs.

Some backports have tasks associated with them. Some tasks are "bugs" or "errors".

When a backport is associated with a task that is a "bug" or an "error" it's a bugfix. The number of bugfixes per train is a good signal of the number of bugs that were present in that train.

Bugs may persist for many trains; however, if a developer makes a backport, they felt that the bug was severe enough to warrant fixing immediately rather than waiting a week—that's signal about train quality, too.


```python
train_bugs = pd.read_sql('''
select
  version,
  count(b.link) as bug_count
from
  train t
  join bug_train bt on bt.train_id = t.id
  join bug b on bt.bug_id = b.id
group by
  version
order by
  start_time
''', engine)
train_bugs.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>version</th>
      <th>bug_count</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1.27.0-wmf.16</td>
      <td>3</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1.27.0-wmf.19</td>
      <td>1</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1.27.0-wmf.21</td>
      <td>1</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1.27.0-wmf.22</td>
      <td>2</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1.27.0-wmf.23</td>
      <td>3</td>
    </tr>
  </tbody>
</table>
</div>



### Bug count histogram

Seems to follow the power law


```python
train_bugs.hist()
```




    array([[<AxesSubplot:title={'center':'bug_count'}>]], dtype=object)




    
![png](README_files/README_29_1.png)
    



```python
train_bugs.sort_values(by="bug_count", ascending=False).head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>version</th>
      <th>bug_count</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>120</th>
      <td>1.34.0-wmf.13</td>
      <td>13</td>
    </tr>
    <tr>
      <th>90</th>
      <td>1.32.0-wmf.24</td>
      <td>11</td>
    </tr>
    <tr>
      <th>206</th>
      <td>1.37.0-wmf.20</td>
      <td>11</td>
    </tr>
    <tr>
      <th>119</th>
      <td>1.34.0-wmf.11</td>
      <td>11</td>
    </tr>
    <tr>
      <th>194</th>
      <td>1.37.0-wmf.5</td>
      <td>11</td>
    </tr>
  </tbody>
</table>
</div>




```python
train_bugs = pd.read_sql('''
select
  version,
  count(b.link) as bug_count,
  rollbacks,
  (select count(*) from blocker b where b.train_id = t.id and resolved = 1) as resolved_blockers,
      (select max(time_in_review) from patch p where p.train_id = t.id) as max_time_in_review,
    (select max(comments) from patch where patch.train_id = t.id) as max_comments_per_patch,
    (select max(start_time - created) from patch p where p.train_id = t.id) as max_cycle_time,
  patches
from
  train t
  join bug_train bt on bt.train_id = t.id
  join bug b on bt.bug_id = b.id
group by
  version
order by
  start_time
''', engine)
train_bugs.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>version</th>
      <th>bug_count</th>
      <th>rollbacks</th>
      <th>resolved_blockers</th>
      <th>max_time_in_review</th>
      <th>max_comments_per_patch</th>
      <th>max_cycle_time</th>
      <th>patches</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1.27.0-wmf.16</td>
      <td>3</td>
      <td>1</td>
      <td>0</td>
      <td>17557313.0</td>
      <td>95.0</td>
      <td>18128243.0</td>
      <td>322</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1.27.0-wmf.19</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>58248774.0</td>
      <td>45.0</td>
      <td>58798558.0</td>
      <td>230</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1.27.0-wmf.21</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>120956985.0</td>
      <td>73.0</td>
      <td>120937246.0</td>
      <td>180</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1.27.0-wmf.22</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
      <td>50045244.0</td>
      <td>58.0</td>
      <td>50160003.0</td>
      <td>416</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1.27.0-wmf.23</td>
      <td>3</td>
      <td>2</td>
      <td>3</td>
      <td>20153065.0</td>
      <td>40.0</td>
      <td>20228209.0</td>
      <td>168</td>
    </tr>
  </tbody>
</table>
</div>




```python
fig, ax = plt.subplots(figsize=(10,10))         # Sample figsize in inches
sns.heatmap(train_bugs.corr(), annot=True, cmap="YlGnBu", linewidths=0.3, annot_kws={"size": 8}, ax=ax)
plt.xticks(rotation=90)
plt.yticks(rotation=0)
plt.show()
```


    
![png](README_files/README_32_0.png)
    



```python
train_bugs[train_bugs['version'] == TRAINS[-1]]
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>version</th>
      <th>bug_count</th>
      <th>rollbacks</th>
      <th>resolved_blockers</th>
      <th>max_time_in_review</th>
      <th>max_comments_per_patch</th>
      <th>max_cycle_time</th>
      <th>patches</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>232</th>
      <td>1.39.0-wmf.3</td>
      <td>1</td>
      <td>0</td>
      <td>4</td>
      <td>19212051.0</td>
      <td>43.0</td>
      <td>19225926.0</td>
      <td>42</td>
    </tr>
  </tbody>
</table>
</div>



## A look at comments per patch

DCaro made an interesting comment on the [the fame blog](https://phabricator.wikimedia.org/phame/post/view/272/diving_into_our_deployment_data/#4166) about this repo. This is my ham-fisted investigation.


```python
comm_dist = pd.read_sql('select version, sum(comments) as comm from patch p join train t on p.train_id = t.id group by t.version', engine)
comm_dist.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>version</th>
      <th>comm</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1.27.0-wmf.16</td>
      <td>1840</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1.27.0-wmf.17</td>
      <td>1372</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1.27.0-wmf.18</td>
      <td>1204</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1.27.0-wmf.19</td>
      <td>1440</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1.27.0-wmf.20</td>
      <td>1573</td>
    </tr>
  </tbody>
</table>
</div>




```python
comm_dist.set_index('version')['comm'].hist(figsize=(12, 10))
plt.xlabel("Patch Comments", labelpad=15)
plt.title("Comments per Train", y=1.02, fontsize=22)
```




    Text(0.5, 1.02, 'Comments per Train')




    
![png](README_files/README_36_1.png)
    



```python
pcommdf = pd.read_sql('select link, comments from patch', engine)
pcommdf.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>link</th>
      <th>comments</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>https://gerrit.wikimedia.org/r/#/q/ccbfcf28,n,z</td>
      <td>1</td>
    </tr>
    <tr>
      <th>1</th>
      <td>https://gerrit.wikimedia.org/r/#/q/3302274f,n,z</td>
      <td>1</td>
    </tr>
    <tr>
      <th>2</th>
      <td>https://gerrit.wikimedia.org/r/#/q/8b5471b5,n,z</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>https://gerrit.wikimedia.org/r/#/q/a6abbb67,n,z</td>
      <td>15</td>
    </tr>
    <tr>
      <th>4</th>
      <td>https://gerrit.wikimedia.org/r/#/q/af916aad,n,z</td>
      <td>3</td>
    </tr>
  </tbody>
</table>
</div>




```python
pcommdf.set_index('link')['comments'].hist(figsize=(12, 10),bins=100)
```




    <AxesSubplot:>




    
![png](README_files/README_38_1.png)
    



```python
pcommdf.describe()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>comments</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>count</th>
      <td>86015.000000</td>
    </tr>
    <tr>
      <th>mean</th>
      <td>3.658257</td>
    </tr>
    <tr>
      <th>std</th>
      <td>5.566325</td>
    </tr>
    <tr>
      <th>min</th>
      <td>0.000000</td>
    </tr>
    <tr>
      <th>25%</th>
      <td>1.000000</td>
    </tr>
    <tr>
      <th>50%</th>
      <td>2.000000</td>
    </tr>
    <tr>
      <th>75%</th>
      <td>4.000000</td>
    </tr>
    <tr>
      <th>max</th>
      <td>354.000000</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Let's try to remove huge outliers
pcommdf[np.abs(pcommdf.comments - pcommdf.comments.mean()) <= (5 * pcommdf.comments.std())]
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>link</th>
      <th>comments</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>https://gerrit.wikimedia.org/r/#/q/ccbfcf28,n,z</td>
      <td>1</td>
    </tr>
    <tr>
      <th>1</th>
      <td>https://gerrit.wikimedia.org/r/#/q/3302274f,n,z</td>
      <td>1</td>
    </tr>
    <tr>
      <th>2</th>
      <td>https://gerrit.wikimedia.org/r/#/q/8b5471b5,n,z</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>https://gerrit.wikimedia.org/r/#/q/a6abbb67,n,z</td>
      <td>15</td>
    </tr>
    <tr>
      <th>4</th>
      <td>https://gerrit.wikimedia.org/r/#/q/af916aad,n,z</td>
      <td>3</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>86010</th>
      <td>https://gerrit.wikimedia.org/r/q/771638</td>
      <td>4</td>
    </tr>
    <tr>
      <th>86011</th>
      <td>https://gerrit.wikimedia.org/r/q/770833</td>
      <td>8</td>
    </tr>
    <tr>
      <th>86012</th>
      <td>https://gerrit.wikimedia.org/r/q/772045</td>
      <td>1</td>
    </tr>
    <tr>
      <th>86013</th>
      <td>https://gerrit.wikimedia.org/r/q/772022</td>
      <td>1</td>
    </tr>
    <tr>
      <th>86014</th>
      <td>https://gerrit.wikimedia.org/r/q/771990</td>
      <td>1</td>
    </tr>
  </tbody>
</table>
<p>85513 rows × 2 columns</p>
</div>




```python
pcommdf[np.abs(pcommdf.comments - pcommdf.comments.mean()) <= (5 * pcommdf.comments.std())].hist(bins=50,figsize=(10, 10))
plt.xlabel("Distribution of comments on patches", labelpad=15)
plt.title("Comments per Patch", y=1.02, fontsize=22)
```




    Text(0.5, 1.02, 'Comments per Patch')




    
![png](README_files/README_41_1.png)
    



```python

```
