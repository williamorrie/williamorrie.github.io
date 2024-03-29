---
layout: post
title: "Visualising clusters of Northern Ireland Road Traffic Collisions (RTC's)"
---

### Idea
Using the open data that was collected for [RTC heat map](https://williamorrie.github.io/rtc_heatmap.html){:target="_blank"}, create an [RTC cluster map](https://williamorrie.github.io/rtc_clusters.html){:target="_blank"} with mapbox.

### Process 
1. Create a new branch on github
2. Create a new HTML page in new branch
3. Add mapbox boilerplate code for Heatmap
4. Update the data source to point to my [RTC geojson data](https://williamorrie.github.io/RTC_geo.json){:target="_blank"} held on github
5. Update the popup to display date of RTC

### Problems
1. Unable to test on mobile / GitHub.com as commits to new branch are not automatically published.
2. Original Heatmap layere were created in mapbox studio and published from there as a style, how do I reference the data in new map?
3. New post didn't appear on home page
4. Editing javascript in github web browser prone to errors
5. Wrecked cluster map by pasting script from codepen over entire page

### Solutions
1. Found this [article](https://automationpanda.com/2021/03/24/testing-github-pages-without-local-jekyll-setup/){:target="_blank} while researching something else. Repo Home Page > Settings > Options > Source
2. Was able to pull the data directly from github, when previously attempted this method recieved CORS errors.
3. New page did not have .md extension
4. Using [codepen.io](https://codepen.io/){:target="_blank"} to edit mapbox javascript
5. Reverted GitHub commit from command line (no way to do this from browser)

### Results
1. Basic [RTC cluster map](https://williamorrie.github.io/rtc_clusters.html){:target="_blank"} created
2. Able to make changes to website from mobile
