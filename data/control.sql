select patent.id, location.state, rawinventor.inventor_id from patent 
left join rawinventor on rawinventor.patent_id = patent.id 
left join rawlocation on rawlocation.id = rawinventor.rawlocation_id 
left join location on location.id = rawlocation.location_id 
where 
year(patent.date) < 1986;-- and 
--(location.state = 'AK' or location.state = 'CA' or location.state = 'CT'
--  or location.state = 'MN' or location.state = 'MT' or location.state = 'ND'
--  or location.state = 'NV' or location.state = 'OK' or location.state = 'WA' or location.state = 'WV');
