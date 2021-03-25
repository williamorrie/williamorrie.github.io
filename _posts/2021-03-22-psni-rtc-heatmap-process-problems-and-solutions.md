---
layout: post
title: "Mapping PSNI RTC Data from OpenDataNI"
---

### Idea
Create a heatmap from PSNI RTC data using free online tools.

link]("https://williamorrie.github.io/rtc_hestmap.html"){:target="_blank}

### Process 
1. Use Google colab (ipython juypter notebook) to extract data from opendatni website
2. Merge separate CSV files to single data source
3. Clean data and extract important records
4. Convert Irish grid reference to long / lat
5. Create points from coordinates
6. Plot points and display demo in colab
7. Extract required columns and save  as geojson file
8. Create a GitHub sites page to present the data
9. Follow mapbox tutorial to create basic / free map
10. Upload geojson to mailbox as features 
11. Create tile layer from features 
12. Realise that mailbox classes this as a style that can be shared (different to ESRI process but works)
13. Change GitHub map style to match uploaded mapbox style
14. Happy with fancy rtc_heatmap.html

### Problems
1. Opendatni didnt use consistent URLs
2. Schema changes in data uploaded from PSNI
3. Got mixed up converting X/Y to long/lat
4. Unsure how to get data out of colab
5. Every change to new site requires a commit, feel this is messing up the history (compared to normal GitHub projects)
6. Got lost with different mailbox tutorials using API versions
7. I keep changing the names of the map pages
8. Couldn't access geojson directly fr GitHub due to CORS problems

### Resolutions
1. Specify full URL paths in script instead of data IDs
2. Ignore unmatched columns, as not relevant for this process, more difficult column matching could be scripted
3. It's not the 1st time I have put Northern Ireland points in the Indian Ocean
4. Spent time mounting Google drive, didn't realise could down files direct to browser
5. Accept that this is not going to be perfect and just an example of what I'm learning
6. Finished for day and slept on problems, woke before alarm and fixed site in no time
7. Stop sharing links before your content
8. Accept that the simple way to use mapbox is by uploading your data and sharing through their API / services

### Results
1. Crested a heat map of open data RTC in NI
2. Proved can process/analyse  data outside ESRI environment
3. Able to publish maps to web without  paying money
