select patent.id, location.state, rawinventor.inventor_id from rawinventor 
left join patent on patent.id = rawinventor.patent_id 
left join inventor on inventor.id = rawinventor.inventor_id 
left join rawlocation on rawlocation.id = rawinventor.rawlocation_id 
left join location on location.id = rawlocation.location_id
where 
year(patent.date) < 1985;
